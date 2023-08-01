import netmanage.netbox_collectors as nbc
from typing import Optional
from pynetbox import api, RequestError


def update_prefix(
    token: str,
    url: str,
    _id: int,
    prefix: Optional[str] = None,
    description: Optional[str] = None,
    site: Optional[str] = None,
    tenant: Optional[str] = None,
    vrf: Optional[str] = None,
):
    """
    Add a new prefix to Netbox IPAM.

    Parameters
    ----------
    token : str
        API token for authentication.
    url: str
        Url of Netbox instance.
    _id: int
        The netbox id of the object being updated must be included
    prefix: Optional[str]
        The prefix to be added to Netbox IPAM in CIDR notation.
    description: Optional[str]
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

    if not _id:
        raise TypeError("The netbox id of the object being updated must be included")

    nb = api(url, token=token)

    # If a VRF was provided, then get its ID.
    if vrf:
        result = nbc.netbox_get_vrf_details(url, token, vrf)
        vrf = str(result.iloc[0]["id"])

    data = {
        "id": _id,
        "prefix": prefix,
        "site": site,
        "description": description,
        "tenant": tenant,
        "vrf": vrf,
    }

    if prefix is None:
        del data["prefix"]
    if description is None:
        del data["description"]
    if site is None:
        del data["site"]
    if tenant is None:
        del data["tenant"]
    if vrf is None:
        del data["vrf"]

    try:
        nb.ipam.prefixes.update(data)
    except RequestError as e:
        print(f"[{prefix}]: {str(e)}")

def update_site(token: str,
             url: str,
             _id: int,
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
    _id: int
        The netbox id of the object being updated must be included
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

    if not _id:
        raise TypeError("The netbox id of the object being updated must be included")

    api = api(url=url, token=token)
    site = {"id": _id,
        "name": name,
            "slug": slug,
            "status": status}

    # Check which optional fields are passed and add them to the site payload
    # as appropriate.
    if name:
        site["name"] = name
    if slug:
        site["slug"] = slug
    if status:
        site["status"] = status
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
    return api.dcim.sites.update(site)
