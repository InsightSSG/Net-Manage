#!/usr/bin/env python3

import ast
import os
import pandas as pd
import pynetbox
import requests
from typing import Optional


def create_netbox_handler(
    nb_url: str, token: str, verify_ssl: bool = True
) -> pynetbox.core.api.Api:
    """
    Creates the handler for connecting to Netbox using pynetbox.

    Parameters
    ----------
    nb_url : str
        The path to the Netbox instance.
    token : str
        The API token for authentication.
    verify_ssl : bool, optional
        Whether to verify SSL certificates.

    Returns
    -------
    nb : pynetbox.core.api.Api
        An object for Netbox API interaction.
    """
    nb = pynetbox.api(nb_url, token)
    if not verify_ssl or not ast.literal_eval(os.environ["validate_certs"]):
        custom_session = requests.Session()
        custom_session.verify = False
        nb.http_session = custom_session
        requests.urllib3.disable_warnings()
    return nb


def netbox_get_all_cable_attributes(
    nb_url: str, token: str, verify_ssl: bool = True
) -> dict:
    """
    Gets the attributes for all cables.

    Parameters
    ----------
    nb_url : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    verify_ssl : bool, optional
        Whether to verify SSL certificates.

    Returns
    -------
    all_cables : dict
        A dictionary containing the attributes of all cables.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> all_cables = netbox_get_all_cable_attributes(nb_url, token)
    print(all_cables)
    """
    # Create the Netbox handler.
    nb = create_netbox_handler(nb_url, token)

    # Query the Netbox API for all cables.
    cables = nb.dcim.cables.all()

    # Initialize an empty dictionary to hold all the cable attributes.
    all_cables = {}

    # Get the attributes for each cable and add them to the dictionary.
    for cable in cables:
        # The cable id is used as the key and the attributes are the values.
        all_cables[cable.id] = vars(cable)

    return all_cables


def netbox_get_device_attributes(
    nb_url: str,
    token: str,
    device_id: Optional[int] = None,
    device_name: Optional[str] = None,
    verify_ssl: bool = True,
) -> pd.DataFrame:
    """
    Gets the attributes for a device by its id or name.

    Parameters
    ----------
    nb_url : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    device_id: Optional[int], Default None
        The id of the device for which to retrieve attributes.
    device_name: Optional[str], Default None
        The name of the device for which to retrieve attributes.
    verify_ssl : bool, optional
        Whether to verify SSL certificates.

    Returns
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the device details.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> df = netbox_get_device_attributes(nb_url, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    """
    # Create the netbox handler.
    nb = create_netbox_handler(nb_url, token)

    # If both device id and name are provided, raise an error
    if device_id and device_name:
        raise ValueError("Please provide either a device id or device name, not both")

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


def netbox_get_all_device_ids(nb_url: str, token: str, verify_ssl: bool = True) -> list:
    """
    Retrieves all the device IDs from the NetBox instance.

    Parameters
    ----------
    nb_url : str
        The URL of the NetBox instance.
    token : str
        The API token for the NetBox instance.
    verify_ssl : bool, optional
        Whether to verify SSL certificates. Defaults to True.

    Returns
    -------
    device_ids : list
        A list of all device IDs.
    """

    nb = create_netbox_handler(nb_url, token=token, verify_ssl=verify_ssl)
    devices = nb.dcim.devices.all()

    device_ids = [str(device.id) for device in devices]

    return device_ids


def netbox_get_device_interfaces(
    nb_url: str,
    token: str,
    device_id: str = None,
    device_name: str = None,
    verify_ssl: bool = True,
) -> dict:
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
    nb = create_netbox_handler(nb_url, token)

    # Use device ID or device name based on what's provided
    filter_param = {"device_id": device_id} if device_id else {"device": device_name}

    device_interfaces = nb.dcim.interfaces.filter(**filter_param)

    interfaces_dict = {}

    for interface in device_interfaces:
        interfaces_dict[interface.id] = vars(interface)

    return interfaces_dict


def netbox_get_device_manufacturers_types_ids(handler, verify_ssl: bool = True) -> dict:
    """
    Retrieves all device manufacturers, device types, and their IDs from Netbox using
    GraphQL.

    Parameters
    ----------
    handler : pynetbox.core.api.Api
        The Netbox API handler object.
    validate_certs : bool, optional
        Whether to verify SSL certs. Defaults to True.

    Returns
    -------
    data : dict
        A dictionary with manufacturers as keys; each key maps to a list of dictionaries
        with device types and their IDs.
    """
    graphql_url = f"{handler.base_url.strip('/api')}/graphql/"
    headers = {
        "Authorization": f"Token {handler.token}",
        "Content-Type": "application/json",
    }

    query = """
    {
      manufacturer_list {
        name
        device_types {
          id
          model
        }
      }
    }
    """

    response = requests.post(
        graphql_url, json={"query": query}, headers=headers, verify=verify_ssl
    )
    response.raise_for_status()

    manufacturers_data = response.json().get("data", {}).get("manufacturer_list", [])
    return {
        manufacturer["name"]: [
            {"id": device_type["id"], "model": device_type["model"]}
            for device_type in manufacturer["device_types"]
        ]
        for manufacturer in manufacturers_data
    }


def netbox_get_device_role_attributes(
    nb_url: str, token: str, device_role: Optional[str] = None, verify_ssl: bool = True
) -> pd.DataFrame:
    """
    Gets the attributes for one or more device roles.

    Parameters
    ----------
    nb_url : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    device_role: Optional[str], Default None
        The name of the device role for which to retrieve attributes. If one ]
        is not provided, then attributes for all device roles will be returned.
    verify_ssl : bool, optional
        Whether to verify SSL certificates.

    Returns
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the device role details.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> df = netbox_get_device_role_attributes(nb_url, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    """
    # Create the netbox handler.
    nb = create_netbox_handler(nb_url, token)

    # Query the Netbox API for all device roles.
    device_roles = nb.dcim.device_roles.all()
    device_roles_list = list(device_roles)

    df_data = list()

    # Get the attributes for the device role(s), add them to 'df_data', then
    # create and return a DataFrame.
    if device_roles_list and device_role:
        for item in device_roles_list:
            if item["name"] == device_role:
                device_role_attributes = vars(item)
                df_data.append(device_role_attributes)
                break
    elif device_roles_list:
        for role in device_roles_list:
            df_data.append(vars(role))

    df = pd.DataFrame(df_data)

    return df


def netbox_get_device_type_attributes(
    nb_url: str, token: str, device_type: Optional[str] = None, verify_ssl: bool = True
) -> pd.DataFrame:
    """
    Gets the attributes for one or more device types.

    Parameters
    ----------
    nb_url : str
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
    >>> df = netbox_get_device_type_attributes(nb_url, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    """
    # Create the netbox handler.
    nb = create_netbox_handler(nb_url, token)

    # Query the Netbox API for all device types.
    device_types = nb.dcim.device_types.all()
    device_types_list = list(device_types)

    df_data = list()

    # Get the attributes for the device type(s), add them to 'df_data', then
    # create and return a DataFrame.
    if device_types_list and device_type:
        for item in device_types_list:
            if item["model"] == device_type:
                device_type_attributes = vars(item)
                df_data.append(device_type_attributes)
                break
    elif device_types_list:
        for _type in device_types_list:
            df_data.append(vars(_type))

    df = pd.DataFrame(df_data)

    return df


def netbox_get_devices_by_site(
    nb_url: str, token: str, site_ids: list = None, verify_ssl: bool = True
) -> pd.DataFrame:
    """
    Retrieves a DataFrame of devices for specified sites in Netbox. If no site IDs are
    provided, returns devices for all sites.

    Parameters
    ----------
    nb_url : str
        URL of the NetBox instance.
    token : str
        API token for the NetBox instance.
    site_ids : list, optional
        List of site IDs to filter devices. If None or empty, fetches all sites.
    verify_ssl : bool
        Whether to verify SSL certificates.

    Returns
    -------
    pd.DataFrame
        DataFrame containing device information for specified sites or all sites if no
        IDs are provided.
    """
    nb = create_netbox_handler(nb_url, token)
    rows = []

    if site_ids:
        sites = [nb.dcim.sites.get(id) for id in site_ids if nb.dcim.sites.get(id)]
    else:
        sites = nb.dcim.sites.all()

    for site in sites:
        site_devices = nb.dcim.devices.filter(site_id=site.id)
        for device in site_devices:
            rows.append(
                {
                    "site_id": site.id,
                    "site_name": site.name,
                    "site_tenant": site.tenant.name if site.tenant else None,
                    "device_id": device.id,
                    "device_name": device.name,
                    "device_tenant": device.tenant.name if device.tenant else None,
                    "manufacturer": device.device_type.manufacturer.name,
                    "model": device.device_type.model,
                    "serial": device.serial,
                }
            )

    return pd.DataFrame(rows)


def netbox_get_devices_with_manufacturers_names_models(
    nb_url: str, token: str, verify_ssl: bool = True
) -> dict:
    """
    Retrieves all devices with their corresponding manufacturer name, manufacturer ID,
    device name, and device model.

    Parameters
    ----------
    nb_url : str
        The URL of the NetBox instance.
    token : str
        The API token for the NetBox instance.
    verify_ssl : bool, optional
        Whether to verify SSL certificates.

    Returns
    -------
    devices_info : dict
        A dictionary with device IDs as keys and manufacturer, device name, and device
        model details as values.
    """

    nb = create_netbox_handler(nb_url, token=token, verify_ssl=verify_ssl)
    devices = nb.dcim.devices.all()

    devices_info = {}
    for device in devices:
        manufacturer = device.device_type.manufacturer
        devices_info[device.id] = {
            "device_name": device.name,
            "device_model": device.device_type.model,
            "manufacturer_name": manufacturer.name,
            "manufacturer_id": manufacturer.id,
        }

    return devices_info


def netbox_get_interface_attributes(
    nb_url: str, token: str, interface_id: str, verify_ssl: bool = True
) -> dict:
    """
    Gets the attributes for a specific interface.

    Parameters
    ----------
    nb_url : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    interface_id: str
        The ID of the interface for which to retrieve attributes.
    verify_ssl : bool
        Whether to verify SSL certificates.

    Returns
    -------
    interface_attributes : dict
        A dictionary containing the attributes of the specified interface.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> interface_attributes = netbox_get_interface_attributes(nb_url,
                                                               token,
                                                               interface_id)
    print(interface_attributes)
    """
    # Create the Netbox handler.
    nb = create_netbox_handler(nb_url, token)

    # Query the Netbox API for the specified interface.
    interface = nb.dcim.interfaces.get(interface_id)

    # Get the attributes for the specified interface and store them in a
    # dictionary.
    interface_attributes = vars(interface)

    return interface_attributes


def netbox_get_ipam_prefixes(
    nb_url: str, token: str, verify_ssl: bool = True
) -> pd.DataFrame:
    """Gets all prefixes from a Netbox instance.

    Parameters
    ----------
    nb_url : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    verify_ssl : bool
        Whether to verify SSL certificates.

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
    >>> df = netbox_get_ipam_prefixes(nb_url, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    """
    # Create the netbox handler
    nb = create_netbox_handler(nb_url, token)

    # Query the Netbox API for all IPAM prefixes
    result = nb.ipam.prefixes.all()

    # Iterate over the prefixes, adding each one as a row for 'df'.
    df = pd.DataFrame()
    for _ in result:
        _ = dict(_)
        df = pd.concat([df, pd.DataFrame.from_dict(_, orient="index").T]).reset_index(
            drop=True
        )
    return df


def netbox_get_prefixes_sites_vrfs(
    netbox_url: str, token: str, verify_ssl: bool = True
) -> pd.DataFrame:
    """
    Fetch all IPAM prefixes with their associated sites and VRFs from a Netbox instance.

    Parameters
    ----------
    netbox_url : str
        The URL of the Netbox instance.
    token : str
        The API token for authentication.
    verify_ssl : bool
        Whether to verify SSL certificates.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the prefixes, associated sites, and VRFs.

    Notes
    -----
    - Requires pandas and pynetbox to be installed.
    - Netbox instance must be accessible from the script's environment.
    - The user must have read permissions on the IPAM module in Netbox.
    """

    # Initialize the pynetbox API
    nb = create_netbox_handler(netbox_url, token=token, verify_ssl=verify_ssl)

    # Fetching all prefixes
    prefixes = nb.ipam.prefixes.all()

    # Extracting required data and building a DataFrame
    data = []
    for prefix in prefixes:
        site = prefix.site.name if prefix.site else "None"
        vrf = prefix.vrf.name if prefix.vrf else "None"
        data.append({"Prefix": prefix.prefix, "Site": site, "VRF": vrf})

    return pd.DataFrame(data)


def get_netbox_vlan_internal_id(
    netbox_url: str, token: str, vlan_vid: int, vlan_name: str, verify_ssl: bool = True
) -> Optional[int]:
    """
    Get the Netbox internal ID for a VLAN based on its VLAN ID and name.

    Parameters
    ----------
    netbox_url : str
        The URL of the Netbox instance.
    token : str
        The API token to authenticate with Netbox.
    vlan_vid : int
        The VLAN ID (VID).
    vlan_name : str
        The name of the VLAN.
    verify_ssl : bool, optional
        Whether to verify SSL certificates.

    Returns
    -------
    int or None
        The Netbox internal ID for the VLAN if found, otherwise None.

    Examples
    --------
    >>> netbox_url = "http://netbox.local"
    >>> token = "YOUR_API_TOKEN"
    >>> vlan_id = get_netbox_vlan_internal_id(netbox_url,
                                              token,
                                              100,
                                              "VLAN100")
    >>> print(vlan_id)
    """
    # Initialize the Netbox API client
    nb = create_netbox_handler(netbox_url, token, verify_ssl=verify_ssl)

    # Query for the VLAN with the given VLAN ID and name
    vlans = list(nb.ipam.vlans.filter(vid=vlan_vid, name=vlan_name))

    # If the VLAN is found, return its Netbox internal ID
    if vlans and len(vlans) == 1:
        return vlans[0].id
    else:
        return None


def netbox_get_device_details(
    nb_url: str, token: str, device_id: int, verify_ssl: bool = True
) -> dict:
    """
    Retrieves details for a specified device by its ID from the NetBox instance.

    Parameters
    ----------
    nb_url : str
        The URL of the NetBox instance.
    token : str
        The API token for the NetBox instance.
    device_id : int
        The ID of the device for which to retrieve details.
    verify_ssl : bool, optional
        Whether to verify SSL certificates. Defaults to True.

    Returns
    -------
    device_details : dict
        A dictionary containing all details of the specified device.
    """

    nb = create_netbox_handler(nb_url, token=token, verify_ssl=verify_ssl)

    # Retrieve the device by its ID
    device = nb.dcim.devices.get(device_id)
    if device:
        return vars(device)
    else:
        return {"error": "Device not found"}


def netbox_get_site_attributes(
    nb_url: str, token: str, site: Optional[str] = None, verify_ssl: bool = True
) -> pd.DataFrame:
    """
    Gets the attributes for one or more sites.

    Parameters
    ----------
    nb_url : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    site: Optional[str], Default None
        The name of the site for which to retrieve attributes. If one is not
        provided, then attributes for all sites will be returned.
    verify_ssl : bool, optional
        Whether to verify SSL certificates.

    Returns
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the site details.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> df = netbox_get_site_attributes(nb_url, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    """
    # Create the netbox handler.
    nb = create_netbox_handler(nb_url, token)

    # Query the Netbox API for all sites.
    sites = nb.dcim.sites.all()
    sites_list = list(sites)

    df_data = list()

    # Get the attributes for the site(s), add them to 'df_data', then create
    # and return a DataFrame.
    if sites_list and site:
        for item in sites_list:
            if item["name"] == str(site):
                site_attributes = vars(item)
                df_data.append(site_attributes)
                break
    elif sites_list:
        for _site in sites_list:
            df_data.append(vars(_site))

    df = pd.DataFrame(df_data)

    return df


def netbox_get_tenant_attributes(
    nb_url: str, token: str, tenant: Optional[str] = None, verify_ssl: bool = True
) -> pd.DataFrame:
    """
    Gets the attributes for one or more tenants.

    Parameters
    ----------
    nb_url : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    tenant: Optional[str], Default None
        The name of the tenant for wihch to retrieve attributes. If one is not
        provided, then attributes for all tenants will be returned.
    verify_ssl : bool, optional
        Whether to verify SSL certificates.

    Returns
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the VRF details.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> df = netbox_get_tenant_attributes(nb_url, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    """
    # Create the netbox handler.
    nb = create_netbox_handler(nb_url, token)

    # Query the Netbox API for all tenants.
    tenants = nb.tenancy.tenants.all()
    tenants_list = list(tenants)

    df_data = list()

    # Get the attributes for the tenant(s), add them to 'df_data', then create
    # and return a DataFrame.
    if tenants_list and tenant:
        for item in tenants_list:
            if item["name"] == tenant:
                tenant_attributes = vars(item)
                df_data.append(tenant_attributes)
                break
    elif tenants_list:
        for _tenant in tenants_list:
            df_data.append(vars(_tenant))

    df = pd.DataFrame(df_data)

    return df


def netbox_get_vrf_details(
    nb_url: str, token: str, vrf: Optional[str] = None, verify_ssl: bool = True
) -> pd.DataFrame:
    """
    Gets details of one or more VRFs in Netbox.

    Parameters
    ----------
    nb_url : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    vrf: Optional[str], Default None
        The name of the VRF for which to retrieve details. If one is not
        provided, then details for all VRFs will be returned.
    verify_ssl : bool, optional
        Whether to verify SSL certificates.

    Returns
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the VRF details.

    See Also
    --------
    create_netbox_handler : A function to create 'nb'

    Examples
    --------
    >>> df = netbox_get_vrf_details(nb_url, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    """
    # Create the netbox handler
    nb = create_netbox_handler(nb_url, token)

    # Query the Netbox API for the VRF details and add them to 'df_data'.
    df_data = dict()
    if vrf:
        result = nb.ipam.vrfs.get(name=vrf)
        for attribute_name in dir(result):
            attribute_value = getattr(result, attribute_name)
            if attribute_name[:1] != "_":
                if not df_data.get(attribute_name):
                    df_data[attribute_name] = list()
                df_data[attribute_name].append(attribute_value)
    else:
        result = nb.ipam.vrfs.all()
        for item in result:
            # result = nb.ipam.vrfs.get(name=vrf)
            for attribute_name in dir(item):
                attribute_value = getattr(item, attribute_name)
                if attribute_name[:1] != "_":
                    if not df_data.get(attribute_name):
                        df_data[attribute_name] = list()
                    df_data[attribute_name].append(attribute_value)

    # Create the DataFrame and re-order the columns so that 'id', 'name',
    # 'description', and 'tenant' are first.
    df = pd.DataFrame.from_dict(df_data)

    to_move = ["id", "name", "description", "tenant"]
    to_move.reverse()
    for col_name in to_move:
        try:
            col = df.pop(col_name)
            df.insert(0, col_name, col)
        except KeyError:
            print(f"[{vrf}]: VRF does not exist.")
            break

    return df


def fetch_device_roles_dict(nb_url, token):
    """
    Fetches all device roles from Netbox and maps display names to IDs.
    :param nb_url: URL of the Netbox instance.
    :param token: API token for authentication.
    :return: Dictionary mapping role display names to their IDs.
    """
    nb = create_netbox_handler(nb_url, token)
    roles = nb.dcim.device_roles.all()
    return {role.display: role.id for role in roles}


def fetch_site_name_id_mapping(nb_url, token):
    """
    Fetches all site names from Netbox and maps display names to IDs.
    :param nb_url: URL of the Netbox instance.
    :param token: API token for authentication.
    :return: Dictionary mapping role display names to their IDs.
    """
    nb = create_netbox_handler(nb_url, token)
    sites = nb.dcim.sites.all()
    return {site.name: site.id for site in sites}


def fetch_device_types_dict(nb_url, token):
    """
    Fetches all device types from Netbox and maps display names to IDs.
    :param nb_url: URL of the Netbox instance.
    :param token: API token for authentication.
    :return: Dictionary mapping device_type names to their IDs.
    """
    nb = create_netbox_handler(nb_url, token)
    types = nb.dcim.device_types.all()
    return {type.display: type.id for type in types}
