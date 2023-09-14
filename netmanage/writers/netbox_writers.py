#!/usr/bin/env python3

import pynetbox
from typing import Dict, List, Optional, Any
from netmanage.collectors import netbox_collectors as nbc

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

    # Create the device dictionary.
    device = {
        'name': name,
        'manufacturer': manufacturer,
        'device_role': device_role_id,
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
        raise Exception(f"Error occurred while adding the device: {str(e)}")


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


def add_prefix(token: str,
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
