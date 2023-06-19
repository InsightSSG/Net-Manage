#!/usr/bin/env python3

import pynetbox
from typing import Optional
from collectors import netbox_collectors as nbc


def add_netbox_prefix(token: str,
                      url: str,
                      prefix: str,
                      description: str,
                      site: Optional[str] = None,
                      tenant: Optional[str] = None,
                      vrf: Optional[str] = None):
    """
    Add a new prefix to Netbox IPAM.

    Parameters
    ----------
    token : str
        API token for authentication.
    url : str
        Url of Netbox instance.
    prefix : str
        The prefix to be added to Netbox IPAM in CIDR notation.
    description: str
        A description for the prefix.
    site: Optional[str], Default None
        The slug of the Site where the prefix belongs.
    tenant: Optional[str], Default None
        The slug of the Tenant in which the prefix is located.
    vrf: Optional[str], Default None
        The name of the VRF.

    Returns
    -------
    None

    Raises
    ------
    pynetbox.RequestError
        If there is any problem in the request to Netbox API.

    Notes
    -------
    A RequestError is thrown if there is a duplicate prefix, but ONLY if
    the option to allow duplicate prefixes has been disabled (it is enabled by
    default). The option to disallow duplicate prefixes can be  disabled on a
    vrf-by-vrf basis. For prefixes that are not in VRFs, it can be disabled
    globally. See these URLs for more information:
    - https://demo.netbox.dev/static/docs/core-functionality/ipam/
    - https://demo.netbox.dev/static/docs/configuration/dynamic-settings/
    """
    nb = pynetbox.api(url, token=token)

    # If a VRF was provided, then get its ID.
    if vrf:
        result = nbc.netbox_get_vrf_details(url, token, vrf)
        vrf = str(result.iloc[0]['id'])

    data = {
        'prefix': prefix,
        'site': site,
        'description': description,
        'tenant': tenant,
        'vrf': vrf
    }
    try:
        nb.ipam.prefixes.create(data)
    except pynetbox.RequestError as e:
        print(f'[{prefix}]: {str(e)}')


def add_netbox_vrf(token: str,
                   url: str,
                   vrf_name: str,
                   description: str,
                   rd: Optional[str] = None,
                   enforce_unique: Optional[bool] = True):
    """
    Add a new VRF to Netbox.

    Parameters
    ----------
    token : str
        API token for authentication.
    url : str
        Url of Netbox instance.
    vrf_name : str
        The name of the VRF to be added to Netbox.
    description : str
        A description for the VRF.
    rd : Optional[str], Default None
        The route distinguisher for the VRF.
    enforce_unique : Optional[bool], Default True
        Whether duplicate VRF names should be disallowed (True) or allowed
        (False).

    Returns
    -------
    None

    Raises
    ------
    pynetbox.RequestError
        If there is any problem in the request to Netbox API.

    Notes
    -------
    A RequestError is thrown if there is a duplicate VRF name, but ONLY if
    the option to disallow duplicate VRF names is either passed to the function
    as 'enforce_unique=True' (the default) or has been enabled inside of Netbox
    (it is disabled by default). The option to enforce unique VRF names can be
    enabled globally or for certain groups of prefixes. See this URL for more
    information:
    - https://demo.netbox.dev/static/docs/core-functionality/ipam/
    - https://demo.netbox.dev/static/docs/configuration/dynamic-settings/

    """
    nb = pynetbox.api(url, token=token)
    data = {
        'name': vrf_name,
        'rd': rd,
        'description': description,
        'enforce_unique': enforce_unique
    }
    try:
        nb.ipam.vrfs.create(data)
    except pynetbox.RequestError as e:
        print(f'[{vrf_name}]: {str(e)}')
