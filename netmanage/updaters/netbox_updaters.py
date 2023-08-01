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
        The id of the object being updated must be included
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
        raise TypeError("The id of the object being updated must be included")

    nb = api(url, token=token)

    # If a VRF was provided, then get its ID.
    if vrf:
        result = nbc.netbox_get_vrf_details(url, token, vrf)
        vrf = str(result.iloc[0]["id"])

    data = {
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
