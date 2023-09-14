#!/usr/bin/env python3

import pynetbox
import pandas as pd
from typing import Dict, List, Optional, Any
from netmanage.collectors import netbox_collectors as nbc
from netmanage.helpers import helpers as hp
from netmanage.helpers import netbox_helpers as nhp

from pynetbox import api


def add_cable(netbox_url: str,
              netbox_token: str,
              a_terminations: list,
              b_terminations: list) -> None:
    """
    Add a cable to NetBox.

    Parameters
    ----------
    netbox_url : str
        The URL of the NetBox instance.
    netbox_token : str
        The authentication token for the NetBox API.
    a_terminations : list
        A list of dictionaries containing the terminations for the A side.
    b_terminations : list
        A list of dictionaries containing the terminations for the B side.

    Notes
    -----
    In Netbox 3.3, cables were changed so that they can have multiple
    terminations. This change was mentioned in the release notes, but it does
    not seem to be documented anywhere. Even the Ansible examples are out of
    date. The bulk import reference isn't of use either, since the field names
    and types are different.

    This version of the function works. Currently it only adds the
    terminations. It does not have support for adding colors and lengths, etc.
    We can add those later.

    Examples
    --------
    >>> netbox_token = '12387asdv13'
    >>> netbox_url = 'http://0.0.0.0:8000'
    >>> add_cable(netbox_url,
                  netbox_token,
                  [{'object_id': 22104, 'object_type': 'dcim.interface'}],
                  [{'object_id': 29287, 'object_type': 'dcim.interface'}])
    """
    nb = pynetbox.api(netbox_url, netbox_token)

    cable = {
        'a_terminations': a_terminations,
        'b_terminations': b_terminations
    }

    # Remove any keys that do not have values.
    cable = {k: v for k, v in cable.items() if v}
    print(cable)

    nb.dcim.cables.create(cable)


def add_device_mfg(url: str,
                   token: str,
                   database_path: str):
    """
    Add manufacturers to NB.

    Parameters
    ----------
    url : str
        Url of Netbox instance.
    token : str
        API token for authentication.
    database_path: str
        Path to NM DB
    Returns
    -------
    None
    """
    nm_mfgs = nhp.get_table_prefix_to_device_mfg()
    tables = hp.get_database_tables(database_path)
    mfgs = []

    for table in tables:
        try:
            mfg = table.split('_')[0].upper()
            mfgs.append(nm_mfgs[mfg])
        except Exception as e:
            print(f'Error parsing table {mfg}: {e}')

    mfgs = set(mfgs)
    if not mfgs:
        return None

    for mfg in mfgs:
        try:
            add_manufacturer(
                netbox_url=url,
                netbox_token=token,
                name=mfg.title(),
                slug=mfg.lower().replace(' ', '-')
            )
        except pynetbox.RequestError as e:
            print(f'Error adding {mfg}: {e}')


def add_device_role(netbox_url: str,
                    netbox_token: str,
                    name: str,
                    slug: str,
                    color: str = 'c0c0c0',  # Light Grey
                    description: str = str(),
                    vm_role: bool = False) -> None:
    """
    Create a device role in NetBox.

    Parameters
    ----------
    netbox_url : str
        The URL of the NetBox instance.
    netbox_token : str
        The authentication token for the NetBox API.
    name : str
        The name of the device role.
    slug : str
        The slug (unique identifier) for the device role.
    color : str
        The hexadecimal code associated with the device role. List of valid
        codes (valid for version 3.4.5) can be found here:
        https://tinyurl.com/netboxcolorcodes
    description : str, optional
        The description of the device role.
    vm_role : bool, optional
        Indicates whether the device role is for a virtual machine.

    Returns
    -------
    None
        This function does not return any value.

    Raises
    ------
    Exception
        If any error occurs while creating or updating the device role.
    """
    # Create an instance of the API using the provided URL and token
    nb = pynetbox.api(url=netbox_url, token=netbox_token)
    # Create or update the device role
    try:
        nb.dcim.device_roles.create(name=name,
                                    slug=slug,
                                    color=color,
                                    description=description,
                                    vm_role=vm_role)
    except Exception as e:
        print(f"Error while creating device role: {str(e)}")


def add_device_to_netbox(netbox_url: str,
                         netbox_token: str,
                         name: str,
                         manufacturer: str,
                         status: str,
                         device_role_id: str = str(),
                         device_role_name: str = str(),
                         device_type_id: str = str(),
                         device_type_name: str = str(),
                         site_id: str = str(),
                         site_name: str = str(),
                         tenant_id: str = str(),
                         tenant_name: str = str(),
                         serial: str = str(),
                         custom_fields: dict = {},
                         asset_tag: str = str(),
                         location: str = str(),
                         rack: str = str(),
                         position: int = int(),
                         face: str = str(),
                         parent: str = str(),
                         device_bay: str = str(),
                         airflow: str = str(),
                         virtual_chassis: str = str(),
                         vc_position: int = int(),
                         vc_priority: int = int(),
                         cluster: str = str(),
                         description: str = str(),
                         config_context: dict = {},
                         config_template: str = str(),
                         comments: str = str()) -> None:
    """
    Add a new device to NetBox.

    Parameters
    ----------
    netbox_url : str
        The URL of the NetBox instance.
    netbox_token : str
        The authentication token for the NetBox API.
    name : str
        The name of the device.
    manufacturer : str
        The manufacturer of the device.
    status : str
        The operational status of the device.
    device_role_id : str, optional
        The ID of the role assigned to the device.
    device_role_name : str, optional
        The name of the role assigned to the device.
    device_type_id : str, optional
        The ID of the device type.
    device_type_name : str, optional
        The name of the device type.
    site_id : str, optional
        The ID of the site where the device is located.
    site_name : str, optional
        The name of the site where the device is located.
    tenant_id : str, optional
        The ID of the tenant that owns the device.
    tenant_name : str, optional
        The name of the tenant that owns the device.
    serial : str, optional
        The serial number of the device.
    custom_fields : dict, optional
        The custom fields related to the device.
    asset_tag : str, optional
        The asset tag of the device.
    location : str, optional
        The location of the device.
    rack : str, optional
        The rack of the device.
    position : int, optional
        The position of the device in the rack.
    face : str, optional
        The face of the device in the rack.
    parent : str, optional
        The parent device of the device.
    device_bay : str, optional
        The device bay where the device is installed.
    airflow : str, optional
        The airflow direction of the device.
    virtual_chassis : str, optional
        The virtual chassis to which the device belongs.
    vc_position : int, optional
        The position of the device in the virtual chassis.
    vc_priority : int, optional
        The priority of the device in the virtual chassis.
    cluster : str, optional
        The cluster to which the device belongs.
    description : str, optional
        The description of the device.
    config_context : dict, optional
        A dictionary containing the config context.
    config_template : str, optional
        The configuration template of the device.
    comments : str, optional
        Any comments about the device.

    Returns
    -------
    None
        This function does not return any value. It only creates the device in
        NetBox.
    """
    # Create an instance of the API using the provided URL and token
    nb = api(url=netbox_url, token=netbox_token)

    # If the user provided a device_role name instead of a device_role ID, then
    # use the name of the device_role to find its ID.
    if device_role_name and not device_role_id:
        df = nbc.\
            netbox_get_device_role_attributes(netbox_url,
                                              netbox_token,
                                              device_role=device_role_name)
        device_role_id = str(df.loc[0, 'id'])

    # If the user provided a device_type name instead of a device_tole ID, then
    # user the name of the device_type to find its ID.
    if device_type_name and not device_type_id:
        df = nbc.\
            netbox_get_device_type_attributes(netbox_url,
                                              netbox_token,
                                              device_type=device_type_name)
        device_type_id = str(df.loc[0, 'id'])

    # If the user provided a site name instead of a site ID, then use the name
    # to find the ID.
    if site_name and not site_id:
        df = nbc.netbox_get_site_attributes(netbox_url,
                                            netbox_token,
                                            site_name)
        site_id = str(df.loc[0, 'id'])

    # If the user provided a tenant name instead of a tenant ID, then use the
    # name to find the ID.
    if tenant_name and not tenant_id:
        df = nbc.netbox_get_tenant_attributes(netbox_url,
                                              netbox_token,
                                              tenant_name)
        tenant_id = str(df.iloc[0]['id'])

    # Create the device dictionary. Note that at some point Netbox changed
    # 'device_role' to 'role'. For now, having both keys in the dictionary
    # seems to work. If it breaks down the road, then we will have to build in
    # some version-specific logic.
    device = {
        'name': name,
        'manufacturer': manufacturer,
        'device_role': device_role_id,
        'role': device_role_id,
        'device_type': device_type_id,
        'status': status,
        'site': site_id,
        'tenant': tenant_id,
        'serial': serial,
        'asset_tag': asset_tag,
        'location': location,
        'rack': rack,
        'position': position,
        'face': face,
        'parent': parent,
        'device_bay': device_bay,
        'airflow': airflow,
        'virtual_chassis': virtual_chassis,
        'vc_position': vc_position,
        'vc_priority': vc_priority,
        'cluster': cluster,
        'description': description,
        'comments': comments,
        'config_context': config_context,
        'config_template': config_template,
        'custom_fields': custom_fields
    }

    # Remove any keys that do not have values.
    device = {k: v for k, v in device.items() if v}

    # Add the device to NetBox
    try:
        nb.dcim.devices.create(device)
    except Exception as e:
        if 'Constraint “dcim_device_unique_name_site_tenant” is violated' \
                in str(e):
            print(f'Site ID: {site_id}: {name}: Device already exists')
        else:
            raise Exception(
                f"Error occurred while adding the device: {str(e)}")


def add_device_type(netbox_url: str,
                    netbox_token: str,
                    manufacturer_name: str,
                    model: str,
                    slug: str,
                    u_height: int,
                    is_full_depth: bool = False,
                    part_number: str = str(),
                    subdevice_role: str = str(),
                    airflow: str = str(),
                    description: str = str(),
                    weight: float = float(),
                    weight_unit: str = str(),
                    comments: str = str(),
                    tags: List[str] = list()) \
        -> pynetbox.models.dcim.DeviceTypes:
    """
    Add a device type to NetBox.

    Parameters
    ----------
    netbox_url : str
        The URL of the NetBox instance.
    netbox_token : str
        The authentication token for the NetBox API.
    manufacturer_name : str
        The name of the manufacturer of the device type.
    model : str
        The model name of the device type.
    slug : str
        The slug (unique identifier) for the device type.
    u_height : int
        The height of the device type in rack units (U).
    is_full_depth : bool, optional
        Indicates whether the device consumes both front and rear rack faces.
    part_number : str, optional
        The part number of the device type.
    subdevice_role : str, optional
        The subdevice role of the device type.
    airflow : str, optional
        The airflow direction of the device type.
    description : str, optional
        The description of the device type.
    weight : float, optional
        The weight of the device type.
    weight_unit : str, optional
        The unit for the device weight.
    comments : str, optional
        Additional comments or notes.
    tags : List[str], optional
        Tags associated with the device type.

    Returns
    -------
    device_type : pynetbox.models.dcim.DeviceTypes
        The created DeviceType object in NetBox.
    """
    nb = pynetbox.api(netbox_url, netbox_token)
    manufacturer = nb.dcim.manufacturers.get(name=manufacturer_name)
    device_type = nb.dcim.device_types.create(
        manufacturer=manufacturer.id,
        model=model,
        slug=slug,
        part_number=part_number,
        u_height=u_height,
        is_full_depth=is_full_depth,
        subdevice_role=subdevice_role,
        airflow=airflow,
        description=description,
        weight=weight,
        weight_unit=weight_unit,
        comments=comments,
        tags=tags
    )
    return device_type


def add_device_types(url: str,
                     token: str,
                     database_path: str):
    """
    Add Device types based on NM database devices.

    Parameters
    ----------
    url : str
        Url of Netbox instance.
    token : str
        API token for authentication.
    database_path: str
        Path to NM DB
    Returns
    -------
    None
    """
    query = """SELECT source, model FROM
             device_models GROUP BY source, model;"""
    mfgs = nhp.get_table_prefix_to_device_mfg()
    device_types = nhp.get_device_types()
    con = hp.connect_to_db(database_path)
    df_tables = pd.read_sql(query, con)
    for idx, row in df_tables.iterrows():
        data = dict()
        data['netbox_url'] = url
        data['netbox_token'] = token
        mfg = row["source"].split("_")[0]
        mfg = mfgs.get(mfg).upper()
        if not mfg:
            continue
        model = row["model"]
        data['manufacturer_name'] = mfg.title()
        data['model'] = row["model"]
        slug = model.lower().replace(" ", "-")
        slug = nhp.make_nb_url_compliant(slug)
        data['slug'] = slug.lower()
        data['u_height'] = device_types[mfg][model].get("u_height")
        data['weight'] = device_types[mfg][model].get("weight")
        data['weight_unit'] = device_types[mfg][model].get("weight_unit")
        data['is_full_depth'] = device_types[mfg][model].get("is_full_depth")
        data['airflow'] = device_types[mfg][model].get("airflow")

        try:
            add_device_type(data)
        except Exception as e:
            print(data)
            print(f'add_device_type error: {e}')


def add_ip_ranges_to_netbox(netbox_url: str,
                            netbox_token: str,
                            ranges: List[Dict[str, str]],
                            default_tenant: str = None,
                            default_vrf: int = None,
                            default_tags: List[str] = list()) -> None:
    """
    Add IP ranges to Netbox using pynetbox.

    Parameters
    ----------
    netbox_url : str
        The URL of the Netbox instance.
    token : str
        The token for authentication to Netbox.
    ranges : List[Dict[str, str]]
        A list of dictionaries representing IP ranges.
        Each dictionary should contain keys: start_ip, end_ip, description, and
        optionally: tenant, vrf, tags.
    default_tenant : str, optional
        The default tenant that the IP range belongs to, if not specified in
        the range dictionary. Default is None.
    default_vrf : str, optional
        The default VRF that the IP range belongs to, if not specified in the
        range dictionary. Default is None.
    default_tags : List[str], optional
        Default tags to be added to the IP range, if not specified in the
        range dictionary. Default is None.

    Returns
    -------
    None

    Examples
    --------
    >>> add_ip_ranges_to_netbox(
    ...     'http://netbox.local',
    ...     '0123456789abcdef0123456789abcdef01234567',
    ...     [
    ...         {'start_ip': '192.168.1.0',
                 'end_ip': '192.168.1.255',
                 'description': 'Office IPs',
                 'tags': ['office']},
    ...         {'start_ip': '10.0.0.0',
                 'end_ip': '10.0.0.255',
                 'description':
                 'Datacenter IPs',
                 'vrf': 'DC_VRF',
                 'tags': ['dc']}
    ...     ],
    ...     default_tenant='Corporate',
    ...     default_tags=['main']
    ... )
    """
    # Initialize the pynetbox API
    nb = pynetbox.api(netbox_url, token=netbox_token)

    for ip_range in ranges:
        range_data = {
            'start_address': ip_range['start_ip'],
            'end_address': ip_range['end_ip'],
            'description': ip_range.get('description', ''),
            'tenant': ip_range.get('tenant', default_tenant),
            'vrf': ip_range.get('vrf', default_vrf),
            'tags': ip_range.get('tags', default_tags)
        }

        try:
            # Add the IP range to Netbox
            response = nb.ipam.ip_ranges.create(range_data)
            if not response:
                msg = [f"Failed to add IP range {ip_range['start_ip']}",
                       f"{ip_range['end_ip']}. Response: {response}"]
                msg = ' - '.join(msg)
                print(msg)
            else:
                msg = [f"Successfully added IP range {ip_range['start_ip']}",
                       f"{ip_range['end_ip']}."]
                msg = ' - '.join(msg)
                print(msg)
        except pynetbox.RequestError as e:
            msg = [f"Failed to add IP range {ip_range['start_ip']}",
                   f"{ip_range['end_ip']}: {e}"]
            msg = ' - '.join(msg)
            print(msg)


def add_manufacturer(netbox_url: str,
                     netbox_token: str,
                     name: str,
                     slug: str,
                     description: Optional[str] = "",
                     tags: Optional[list] = []) -> None:
    """
    Create a device manufacturer in NetBox.

    Parameters
    ----------
    netbox_url : str
        The URL of the NetBox instance.
    netbox_token : str
        The authentication token for the NetBox API.
    name : str
        The name of the manufacturer.
    slug : str
        The slug (unique identifier) for the manufacturer.
    description : str, optional
        The description of the manufacturer.
    tags : list, optional
        optional tags

    Returns
    -------
    None
        This function does not return any value.

    Raises
    ------
    Exception
        If any error occurs while creating the device manufacturer.
    """
    # Create an instance of the API using the provided URL and token
    nb = api(url=netbox_url, token=netbox_token)

    # Create the device manufacturer
    try:
        nb.dcim.manufacturers.create(name=name,
                                     slug=slug,
                                     description=description,
                                     tags=tags)
    except Exception as e:
        print(f"Error while creating manufacturer {name}: {str(e)}")


def add_prefix(netbox_url: str,
               token: str,
               prefix: str,
               status: Optional[str] = "active",
               description: Optional[str] = str(),
               site_id: Optional[int] = None,
               vrf_id: Optional[int] = None,
               tenant_id: Optional[int] = None,
               vlan_id: Optional[int] = None,
               vid: Optional[int] = None,
               vlan_name: Optional[str] = str(),
               role_id: Optional[int] = None,
               is_pool: Optional[bool] = False
               ) -> pynetbox.models.ipam.Prefixes:
    """
    Add a prefix to Netbox using pynetbox.

    Parameters
    ----------
    netbox_url : str
        The URL of the Netbox instance.
    token : str
        The API token to authenticate with Netbox.
    prefix : str
        The IP prefix in CIDR notation.
    status : str, optional
        The status of the prefix (e.g., "active", "reserved"), by default
        "active".
    description : str, optional
        A description for the prefix, by default None.
    site_id : int, optional
        The site ID to associate with the prefix, by default None.
    vrf_id : int, optional
        The VRF ID to associate with the prefix, by default None.
    tenant_id : int, optional
        The tenant ID to associate with the prefix, by default None.
    vlan_id : int, optional
        The VLAN ID to associate with the prefix, by default None. Note that
        this is Netbox's internal ID for the VLAN.
    vid : int, optional
        The VLAN ID as displayed in Netbox (I.e., what is configured on the
        device). Used in conjunction with 'vlan_name' to search for Netbox's
        vlan_id.
    vlan_name: str, optional
        The VLAN name. Used to search for Netbox's vlan_id.
    role_id : int, optional
        The role ID to associate with the prefix, by default None.
    is_pool : bool, optional
        Whether the prefix is an IP address pool, by default False.

    Returns
    -------
    pynetbox.models.ipam.Prefixes
        The created prefix object.

    Examples
    --------
    >>> netbox_url = "http://netbox.local"
    >>> token = "YOUR_API_TOKEN"
    >>> prefix_obj = add_prefix(netbox_url, token, "192.168.1.0/24")
    >>> print(prefix_obj)
    """

    # If a vlan_id is not specified but a vid and vlan_name are, then search
    # for the vlan_id.
    if not vlan_id and vid and vlan_name:
        vlan_id = nbc.get_netbox_vlan_internal_id(netbox_url,
                                                  token,
                                                  vid,
                                                  vlan_name)

    # Initialize the Netbox API client
    nb = pynetbox.api(netbox_url, token=token)

    # Create the prefix
    prefix_obj = nb.ipam.prefixes.create({
        "prefix": prefix,
        "status": status,
        "description": description,
        "site": site_id,
        "vrf": vrf_id,
        "tenant": tenant_id,
        "vlan": vlan_id,
        "role": role_id,
        "is_pool": is_pool
    })

    return prefix_obj


def add_site(token: str,
             url: str,
             name: str,
             slug: str,
             status: str,
             latitude: Optional[float] = None,
             longitude: Optional[float] = None,
             physical_address: Optional[str] = None,
             shipping_address: Optional[str] = None,
             tenant_id: Optional[str] = None,
             tenant_name: Optional[str] = None,
             timezone: Optional[str] = None,
             meraki_organization_id: Optional[int] = None,
             meraki_network_id: Optional[str] = None,
             meraki_product_types: Optional[str] = None,
             meraki_tags: Optional[str] = None,
             meraki_enrollement_string: Optional[str] = None,
             meraki_configTemplateId: Optional[str] = None,
             meraki_isBoundToConfigTemplate: Optional[bool] = None,
             meraki_notes: Optional[str] = None,
             meraki_site_url: Optional[str] = None,
             ) -> Dict[str, Any]:
    """
    Create a new site in Netbox with custom Meraki fields.

    Parameters
    ----------
    token : str
        API token for authentication.
    url : str
        Url of Netbox instance.
    name (str):
        The name of the site.
    slug (str):
        The slug for the site.
    status (str):
        The status of the site. Valid statuses are 'planned', 'staging',
        'active', 'decommissioning', 'retired'.
    latitude (float, optional):
        The latitude of the site. Defaults to None.
    longitude (float, optional):
        The longitude of the site. Defaults to None.
    physical_address (str, optional):
        The physical address for the site. Defaults to None.
    shipping_address (str, optional):
        The shipping address for the site. Defaults to None.
    tenant_id (str, optional):
        The numeric ID of the tenant. Defaults to None.
    tenant_name (str, optional):
        The name of the tenant. Defaults to None.
    timezone (str, optional):
        The time zone for the site. Valid options are found here:
        https://en.wikipedia.org/wiki/List_of_tz_database_time_zones.
    meraki_organization_id (int, optional):
        The Meraki organization ID associated with the site. Defaults to None.
    meraki_network_id (str, optional):
        The Meraki network ID associated with the site. Defaults to None.
    meraki_product_types (str, optional):
        The Meraki product types for the site. Defaults to None.
    meraki_tags (str, optional):
        The Meraki tags for the site. Defaults to None.
    meraki_enrollement_string (str, optional):
        The Meraki enrollment string for the site. Defaults to None.
    meraki_configTemplateId (str, optional):
        The Meraki config template ID for the site. Defaults to None.
    meraki_isBoundToConfigTemplate (bool, optional):
        Whether the site is bound to a Meraki config template. Defaults to
        None.
    meraki_notes (str, optional):
        Any notes related to the Meraki configuration for the site. Defaults
        to None.
    meraki_site_url (str, optional):
        The URL associated with the site. Defaults to None.

    Returns:
    ----------
    dict: The response from the Netbox API when adding the site.
    """
    # Initialize pynetbox API and site payload
    api = pynetbox.api(url=url, token=token)
    site = {"name": name,
            "slug": slug,
            "status": status}

    # Check which optional fields are passed and add them to the site payload
    # as appropriate.
    if tenant_id:
        site["tenant"] = tenant_id
    if tenant_name:
        tenant_df = nbc.netbox_get_tenant_attributes(url, token, tenant_name)
        site["tenant"] = str(tenant_df.iloc[0]["id"])
    if physical_address:
        site["physical_address"] = physical_address
    if shipping_address:
        site["shipping_address"] = shipping_address
    if latitude:
        site["latitude"] = latitude
    if longitude:
        site["longitude"] = longitude
    if timezone:
        site["time_zone"] = timezone

    # Check which Meraki fields are passed and add them to the site payload as
    # appropriate.
    if meraki_organization_id:
        site["custom_fields__meraki_organization_id"] = meraki_organization_id
    if meraki_network_id:
        site["custom_fields__meraki_network_id"] = meraki_network_id
    if meraki_product_types:
        site["custom_fields__meraki_product_types"] = meraki_product_types
    if meraki_tags:
        site["custom_fields__meraki_tags"] = meraki_tags
    if meraki_enrollement_string:
        site["custom_fields__meraki_enrollment_string"] = \
            meraki_enrollement_string
    if meraki_configTemplateId:
        site["custom_fields__meraki_configTemplateId"] = \
            meraki_configTemplateId
    if meraki_isBoundToConfigTemplate is not None:
        site["custom_fields__meraki_isBoundToConfigTemplate"] = \
            meraki_isBoundToConfigTemplate
    if meraki_notes:
        site["custom_fields__meraki_notes"] = meraki_notes
    if meraki_site_url:
        site["custom_fields__url"] = meraki_site_url

    # Send the API request to add the site and return the response
    return api.dcim.sites.create(site)


def add_vlan(token: str,
             url: str,
             vlan_id: int,
             name: str,
             site: Optional[str] = None,
             tenant: Optional[str] = None,
             status: Optional[str] = 'active'):
    """
    Add a new VLAN to Netbox.

    Parameters
    ----------
    token : str
        API token for authentication.
    url : str
        Url of Netbox instance.
    vlan_id : int
        The VLAN ID to be added.
    name : str
        The name of the VLAN.
    site: Optional[str], Default None
        The slug of the Site where the VLAN belongs.
    tenant: Optional[str], Default None
        The slug of the Tenant in which the VLAN is located.
    status: Optional[str], Default 'active'
        The status of the VLAN ("active", "reserved", etc).

    Returns
    -------
    None

    Raises
    ------
    pynetbox.RequestError
        If there is any problem in the request to Netbox API.
    """

    nb = pynetbox.api(url, token=token)

    data = {
        'vid': vlan_id,
        'name': name,
        'site': site,
        'tenant': tenant,
        'status': status,
    }

    try:
        nb.ipam.vlans.create(data)
    except pynetbox.RequestError as e:
        print(f'[VLAN {vlan_id}]: {str(e)}')


def add_vrf(token: str,
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
