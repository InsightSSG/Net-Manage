#!/usr/bin/env python3

"""A collection of collectors to gather data from Netbox, using pynetbox.

"""

import pandas as pd
import pynetbox
from typing import Optional


def create_netbox_handler(nb_path: str,
                          token: str) -> pynetbox.core.api.Api:
    '''
    Creates the handler for connecting to Netbox using pynetbox.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.

    Returns
    -------
    nb : pynetbox.core.api.Api
        An object used to connect to the Netbox API.

    Examples
    --------
    >>> nb = create_netbox_handler(nb_path, token)
    >>> print(nb)
    <pynetbox.core.api.Api object at 0x7fb3576a4c1990>
    '''
    nb = pynetbox.api(nb_path, token)
    return nb


def netbox_get_ipam_prefixes(nb_path: str,
                             token: str) -> pd.DataFrame:
    """Gets all prefixes from a Netbox instance.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.

    Returns
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the IPAM prefixes.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Notes
    -----
    The Netbox API returns the prefixes in the form of a nested dictionary.
    Some items in the nested dictionaries have keys that overlap with the
    top-level dictionary. Because of that, the keys in the nested
    dictionaries are prefixed with the key(s) in the level(s) above it,
    followed by an underscore.

    For example, a key named 'id' that is nested under 'tenant' would be
    added as a column named 'tenant_id'.

    Examples
    ----------
    >>> df = netbox_get_ipam_prefixes(nb_path, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    """
    # Create the netbox handler
    nb = create_netbox_handler(nb_path, token)

    # Query the Netbox API for all IPAM prefixes
    result = nb.ipam.prefixes.all()

    # Iterate over the prefixes, adding each one as a row for 'df'.
    df = pd.DataFrame()
    for _ in result:
        _ = dict(_)
        df = pd.concat([df, pd.DataFrame.from_dict(_, orient='index').T]).\
            reset_index(drop=True)
    return df


def netbox_get_tenant_attributes(nb_path: str,
                                 token: str,
                                 tenant: Optional[str] = None) -> pd.DataFrame:
    '''
    Gets the attributes for one or more tenants.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    tenant: Optional[str], Default None
        The name of the tenant for wihch to retrieve attributes. If one is not
        provided, then attributes for all tenants will be returned.

    Returns
    ----------
    df : pd.DataFrame
        A Pandas dataframe containing the VRF details.

    See Also
    ----------
    create_netbox_handler : A function to create 'nb'

    Examples
    ----------
    >>> df = netbox_get_tenant_attributes(nb_path, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    '''
    # Create the netbox handler.
    nb = create_netbox_handler(nb_path, token)

    # Query the Netbox API for all tenants.
    tenants = nb.tenancy.tenants.all()
    tenants_list = list(tenants)

    df_data = list()

    # Get the attributes for the tenant(s), add them to 'df_data', then create
    # and return a DataFrame.
    if tenants_list and tenant:
        for item in tenants_list:
            if item['name'] == tenant:
                tenant_attributes = vars(item)
                df_data.append(tenant_attributes)
                break
    elif tenants_list:
        for _tenant in tenants_list:
            df_data.append(vars(_tenant))

    df = pd.DataFrame(df_data)

    return df


def netbox_get_vrf_details(nb_path: str,
                           token: str,
                           vrf: Optional[str] = None) -> pd.DataFrame:
    '''
    Gets details of one or more VRFs in Netbox.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    vrf: Optional[str], Default None
        The name of the VRF for wihch to retrieve details. If one is not
        provided, then details for all VRFs will be returned.

    Returns
    ----------
    df : pd.DataFrame
        A Pandas dataframe containing the VRF details.

    See Also
    ----------
    create_netbox_handler : A function to create 'nb'

    Examples
    ----------
    >>> df = netbox_get_vrf_details(nb_path, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    '''
    # Create the netbox handler
    nb = create_netbox_handler(nb_path, token)

    # Query the Netbox API for the VRF details and add them to 'df_data'.
    df_data = dict()
    if vrf:
        result = nb.ipam.vrfs.get(name=vrf)
        for attribute_name in dir(result):
            attribute_value = getattr(result, attribute_name)
            if attribute_name[:1] != '_':
                if not df_data.get(attribute_name):
                    df_data[attribute_name] = list()
                df_data[attribute_name].append(attribute_value)
    else:
        result = nb.ipam.vrfs.all()
        for item in result:
            # result = nb.ipam.vrfs.get(name=vrf)
            for attribute_name in dir(item):
                attribute_value = getattr(item, attribute_name)
                if attribute_name[:1] != '_':
                    if not df_data.get(attribute_name):
                        df_data[attribute_name] = list()
                    df_data[attribute_name].append(attribute_value)

    # Create the DataFrame and re-order the columns so that 'id', 'name',
    # 'description', and 'tenant' are first.
    df = pd.DataFrame.from_dict(df_data)

    to_move = ['id', 'name', 'description', 'tenant']
    to_move.reverse()
    for col_name in to_move:
        try:
            col = df.pop(col_name)
            df.insert(0, col_name, col)
        except KeyError:
            print(f'[{vrf}]: VRF does not exist.')
            break

    return df
