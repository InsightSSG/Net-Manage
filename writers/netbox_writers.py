#!/usr/bin/env python3

import pynetbox
from typing import Optional


def add_netbox_prefix(token: str,
                      url: str,
                      prefix: str,
                      description: str,
                      site: Optional[str] = None,
                      tenant: Optional[str] = None):
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

    Returns
    -------
    None

    Raises
    ------
    pynetbox.core.query.RequestError
        If there is any problem in the request to Netbox API.
    """
    nb = pynetbox.api(url, token=token)
    data = {
        'prefix': prefix,
        'site': site,
        'description': description,
        'tenant': tenant
    }
    nb.ipam.prefixes.create(data)
