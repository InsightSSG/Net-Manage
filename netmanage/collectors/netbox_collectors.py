#!/usr/bin/env python3

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


def netbox_get_all_cable_attributes(nb_path: str, token: str) -> dict:
    """
    Gets the attributes for all cables.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.

    Returns
    -------
    all_cables : dict
        A dictionary containing the attributes of all cables.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> all_cables = netbox_get_all_cable_attributes(nb_path, token)
    print(all_cables)
    """
    # Create the Netbox handler.
    nb = create_netbox_handler(nb_path, token)

    # Query the Netbox API for all cables.
    cables = nb.dcim.cables.all()

    # Initialize an empty dictionary to hold all the cable attributes.
    all_cables = {}

    # Get the attributes for each cable and add them to the dictionary.
    for cable in cables:
        # The cable id is used as the key and the attributes are the values.
        all_cables[cable.id] = vars(cable)

    return all_cables


def netbox_get_device_attributes(nb_path: str,
                                 token: str,
                                 device_id: Optional[int] = None,
                                 device_name: Optional[str] = None) \
                                    -> pd.DataFrame:
    """
    Gets the attributes for a device by its id or name.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    device_id: Optional[int], Default None
        The id of the device for which to retrieve attributes.
    device_name: Optional[str], Default None
        The name of the device for which to retrieve attributes.

    Returns
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the device details.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> df = netbox_get_device_attributes(nb_path, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    """
    # Create the netbox handler.
    nb = create_netbox_handler(nb_path, token)

    # If both device id and name are provided, raise an error
    if device_id and device_name:
        raise ValueError(
            "Please provide either a device id or device name, not both")

    if device_id:
        device = nb.dcim.devices.get(device_id)
    elif device_name:
        device = nb.dcim.devices.get(name=device_name)
    else:
        raise ValueError("Please provide either a device id or device name")

    # Return the attributes for the device
    if device:
        device_attributes = vars(device)
        df = pd.DataFrame([device_attributes])
    else:
        df = pd.DataFrame()

    return df


def netbox_get_all_device_ids(nb_url: str, token: str) -> list:
    """
    Retrieves all the device IDs from the NetBox instance.

    Parameters
    ----------
    nb_url : str
        The URL of the NetBox instance.
    token : str
        The API token for the NetBox instance.

    Returns
    -------
    device_ids : list
        A list of all device IDs.
    """

    nb = pynetbox.api(url=nb_url, token=token)
    devices = nb.dcim.devices.all()

    device_ids = [str(device.id) for device in devices]

    return device_ids


def netbox_get_device_interfaces(nb_url: str,
                                 token: str,
                                 device_id: str = None,
                                 device_name: str = None) -> dict:
    """
    Retrieves all the interfaces for a device by its device ID or device name.

    Parameters
    ----------
    nb_url : str
        The URL of the NetBox instance.
    token : str
        The API token for the NetBox instance.
    device_id : str
        The ID of the device for which to retrieve the interfaces.
    device_name : str
        The name of the device for which to retrieve the interfaces.

    Returns
    -------
    interfaces_dict : dict
        A dictionary where keys are the IDs of the interfaces and values are
        the interface details.
    """
    nb = pynetbox.api(url=nb_url, token=token)

    # Use device ID or device name based on what's provided
    filter_param = {'device_id': device_id} if device_id \
        else {'device': device_name}

    device_interfaces = nb.dcim.interfaces.filter(**filter_param)

    interfaces_dict = {}

    for interface in device_interfaces:
        interfaces_dict[interface.id] = vars(interface)

    return interfaces_dict


def netbox_get_device_role_attributes(nb_path: str,
                                      token: str,
                                      device_role: Optional[str] = None) \
                                        -> pd.DataFrame:
    """
    Gets the attributes for one or more device roles.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    device_role: Optional[str], Default None
        The name of the device role for which to retrieve attributes. If one ]
        is not provided, then attributes for all device roles will be returned.

    Returns
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the device role details.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> df = netbox_get_device_role_attributes(nb_path, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    """
    # Create the netbox handler.
    nb = create_netbox_handler(nb_path, token)

    # Query the Netbox API for all device roles.
    device_roles = nb.dcim.device_roles.all()
    device_roles_list = list(device_roles)

    df_data = list()

    # Get the attributes for the device role(s), add them to 'df_data', then
    # create and return a DataFrame.
    if device_roles_list and device_role:
        for item in device_roles_list:
            if item['name'] == device_role:
                device_role_attributes = vars(item)
                df_data.append(device_role_attributes)
                break
    elif device_roles_list:
        for role in device_roles_list:
            df_data.append(vars(role))

    df = pd.DataFrame(df_data)

    return df


def netbox_get_device_type_attributes(nb_path: str,
                                      token: str,
                                      device_type: Optional[str] = None) \
                                        -> pd.DataFrame:
    """
    Gets the attributes for one or more device types.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    device_type: Optional[str], Default None
        The name of the device type for which to retrieve attributes. If one
        is not provided, then attributes for all device types will be returned.

    Returns
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the device type details.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> df = netbox_get_device_type_attributes(nb_path, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    """
    # Create the netbox handler.
    nb = create_netbox_handler(nb_path, token)

    # Query the Netbox API for all device types.
    device_types = nb.dcim.device_types.all()
    device_types_list = list(device_types)

    df_data = list()

    # Get the attributes for the device type(s), add them to 'df_data', then
    # create and return a DataFrame.
    if device_types_list and device_type:
        for item in device_types_list:
            if item['model'] == device_type:
                device_type_attributes = vars(item)
                df_data.append(device_type_attributes)
                break
    elif device_types_list:
        for _type in device_types_list:
            df_data.append(vars(_type))

    df = pd.DataFrame(df_data)

    return df


def netbox_get_interface_attributes(nb_path: str,
                                    token: str,
                                    interface_id: str) -> dict:
    """
    Gets the attributes for a specific interface.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    interface_id: str
        The ID of the interface for which to retrieve attributes.

    Returns
    -------
    interface_attributes : dict
        A dictionary containing the attributes of the specified interface.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> interface_attributes = netbox_get_interface_attributes(nb_path,
                                                               token,
                                                               interface_id)
    print(interface_attributes)
    """
    # Create the Netbox handler.
    nb = create_netbox_handler(nb_path, token)

    # Query the Netbox API for the specified interface.
    interface = nb.dcim.interfaces.get(interface_id)

    # Get the attributes for the specified interface and store them in a
    # dictionary.
    interface_attributes = vars(interface)

    return interface_attributes


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


def netbox_get_site_attributes(nb_path: str,
                               token: str,
                               site: Optional[str] = None) -> pd.DataFrame:
    '''
    Gets the attributes for one or more sites.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    site: Optional[str], Default None
        The name of the site for which to retrieve attributes. If one is not
        provided, then attributes for all sites will be returned.

    Returns
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the site details.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> df = netbox_get_site_attributes(nb_path, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    '''
    # Create the netbox handler.
    nb = create_netbox_handler(nb_path, token)

    # Query the Netbox API for all sites.
    sites = nb.dcim.sites.all()
    sites_list = list(sites)

    df_data = list()

    # Get the attributes for the site(s), add them to 'df_data', then create
    # and return a DataFrame.
    if sites_list and site:
        for item in sites_list:
            if item['name'] == site:
                site_attributes = vars(item)
                df_data.append(site_attributes)
                break
    elif sites_list:
        for _site in sites_list:
            df_data.append(vars(_site))

    df = pd.DataFrame(df_data)

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
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the VRF details.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
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
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the VRF details.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
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
