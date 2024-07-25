#!/usr/bin/env python3

import asyncio
import json
import meraki
import pandas as pd
import sqlite3 as sl
from aiolimiter import AsyncLimiter
from netmanage import run_collectors as rc
from netmanage.helpers import helpers as hp
from netmanage.helpers import meraki_helpers as mhp
from meraki.aio import AsyncDashboardAPI
from meraki.exceptions import APIError, AsyncAPIError
from typing import List, Union


async def meraki_get_device_cdp_lldp_neighbors(
    api_key: str, db_path: str = "", serials: list = [], orgs: list = [], sem: int = 3
) -> pd.DataFrame:
    """
    Gets the CDP and LLDP neighbors for a list of device serial numbers.

    Parameters
    ----------
    api_key : str
        A valid Meraki Dashboard API key.
    db_path : str
        The path to the database to store results.
    serials : list
        A list containing one or more device serial numbers.
    orgs : list
        A list of organization IDs. If this list is populated, then the
        neighbors for all of the devices in the organization(s) will be
        returned. This could take several minutes for large organizations.
        Also, if 'serials' and 'org_ids' are both passed to the function,
        then 'org_ids' will be ignored.
    sem : int, optional
        The Semaphore used to limit the maximum number of concurrent requests
        to the Meraki API. Defaults to 3.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the CDP and LLDP neighbors.
    """
    sem = asyncio.Semaphore(sem)

    async def get_neighbors_for_device(dashboard, serial):
        """
        Get all neighbors for a single device serial number.
        """
        async with sem:
            try:
                neighbors = await dashboard.devices.getDeviceLldpCdp(serial)
                return neighbors
            except Exception as e:
                print(f"Error retrieving data for serial {serial}: {e}")
                return list()

    # If the user did not pass a list of serials to the function, then get all
    # of the serials from the list of orgs. If the user did not pass a list
    # of orgs either, then get all of the serials from all of the
    # organizations that the user's API key has access to.
    if not serials and not orgs:
        df_orgs = meraki_get_organizations(api_key)
        orgs = df_orgs["id"].to_list()
    if not serials:
        df_devices = meraki_get_org_devices(api_key, db_path, orgs=orgs)
        serials = df_devices["serial"].to_list()

    # Use the meraki.aio API to concurrently gather the device neighbors.
    async with AsyncDashboardAPI(api_key, print_console=False) as dashboard:
        # Schedule get_neighbors_for_device() for all serials to run
        # concurrently.
        results = await asyncio.gather(
            *(get_neighbors_for_device(dashboard, serial) for serial in serials)
        )

    rows = []
    for device in results:
        if not device:  # Skip empty device data
            continue
        sourceMac = device.get("sourceMac", None)
        ports = device.get("ports", {})
        for port, details in ports.items():
            row = {"sourceMac": sourceMac}
            lldp_details = details.get("lldp", {})
            cdp_details = details.get("cdp", {})

            row["lldp_sourcePort"] = lldp_details.get("sourcePort", None)
            row["lldpSystemName"] = lldp_details.get("systemName", None)
            row["lldpManagementAddress"] = lldp_details.get("managementAddress", None)
            row["lldpPortId"] = lldp_details.get("portId", None)

            row["cdp_sourcePort"] = cdp_details.get("sourcePort", None)
            row["cdpDeviceId"] = cdp_details.get("deviceId", None)
            row["cdpAddress"] = cdp_details.get("address", None)
            row["cdpPortId"] = cdp_details.get("portId", None)

            rows.append(row)

    return pd.DataFrame(rows)


def get_network_appliance_vlans(
    ansible_os: str,
    api_key: str,
    collector: str,
    db_path: str,
    timestamp: str,
    db_method: str = "append",
    networks: list = [],
    orgs: list = [],
    replace_table: bool = False,
) -> pd.DataFrame:
    """
    Get the appliance VLANs for a list of networks or organizations. If
    networks are not provided, the list of orgs will be used. If both are
    provided, the networks will be used and the orgs will be ignored. If
    neither are provided, the function will return all appliance VLANs for all
    appliances in all organizations the user has access to (this could take a
    while).

    Parameters
    ----------
    ansible_os : str
        The Ansible OS version.
    api_key : str
        A valid Meraki Dashboard API key.
    collector : str
        A name for the Meraki data collector.
    db_path : str
        The path to the SQLite database file.
    timestamp : str
        The timestamp for the data collected in YYYY-MM-DD_HHMM format.
    db_method : {'fail', 'append', 'replace'}, optional
        The behavior to take when the database table already exists.
        Defaults to 'append'.
    networks : list, optional
        A list of Meraki network IDs. Defaults to an empty list.
    orgs : list, optional
        A list of Meraki organization IDs. Defaults to an empty list.
    replace_table : bool, optional
        Whether to replace the 'meraki_network_appliance_vlans' table.

    Returns
    -------
    pd.DataFrame
        A pandas DataFrame that contains the appliance VLANs.

    Examples
    --------
    Example 1:
    >>> ansible_os = '<ansible_os>'
    >>> api_key = '<your_api_key_here>'
    >>> collector = 'network_appliance_vlans'
    >>> db_path = '/path/to/database.db'
    >>> networks = ['N_123456789012345678', 'N_234567890123456789']
    >>> timestamp = '2022-01-01_0000'
    >>> df = get_network_appliance_vlans(api_key,
                                         collector,
                                         db_path,
                                         timestamp,
                                         networks=networks)
    >>> print(df)

    Example 2:
    >>> ansible_os = '<ansible_os>'
    >>> api_key = '<your_api_key_here>'
    >>> collector = 'network_appliance_vlans'
    >>> db_path = '/path/to/database.db'
    >>> orgs = ['O_123456789012345678']
    >>> timestamp = '2022-01-01_0000'
    >>> df = get_network_appliance_vlans(api_key,
                                         collector,
                                         db_path,
                                         timestamp,
                                         orgs=orgs)
    >>> print(df)

    Example 3:
    >>> ansible_os = '<ansible_os>'
    >>> api_key = '<your_api_key_here>'
    >>> collector = 'network_appliance_vlans'
    >>> db_path = '/path/to/database.db'
    >>> networks = ['N_123456789012345678', 'N_234567890123456789']
    >>> orgs = ['O_123456789012345678']
    >>> timestamp = '2022-01-01_0000'
    >>> df = get_network_appliance_vlans(api_key,
                                         collector,
                                         db_path,
                                         timestamp,
                                         networks=networks,
                                         orgs=orgs)
    >>> print(df)
    """
    # If 'networks' is empty and 'orgs' is not, get all applicable networks in
    # the orgs.
    if not networks:
        # Get the last timestamp in the MERAKI_ORG_NETWORKS table.
        query = """SELECT distinct timestamp
        FROM meraki_org_networks
        ORDER BY timestamp desc
        LIMIT 1
        """

        con = sl.connect(db_path)
        result = pd.read_sql(query, con)
        ts = result["timestamp"].to_list().pop()

        if orgs:
            joined_orgs = [f'"{_}"' for _ in orgs]
            joined_orgs = ", ".join(joined_orgs)

            # Get the unique network IDs for the most recent timestamp.
            query = f"""SELECT distinct id
            FROM meraki_org_networks
            WHERE productTypes like "%appliance%"
                AND timestamp = "{ts}"
                AND organizationId IN ({joined_orgs})"""
            result = pd.read_sql(query, con)
            networks = result["id"].to_list()
        else:
            # Get the unique network IDs for the most recent timestamp.
            query = f'''SELECT distinct id
            FROM meraki_org_networks
            WHERE productTypes like "%appliance%"
                AND timestamp = "{ts}"'''
            result = pd.read_sql(query, con)
            networks = result["id"].to_list()

    # Get the appliance vlans for each network. Note: if 'orgs' and 'networks'
    # are both non-empty, then 'orgs' is ignored. The list of networks takes
    # priority.
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True, log_path = '/var/log/netbox/')

    # The only way to get appliance VLANs is to iterate over a list of
    # networks. There is not a way to gather them for an organization. I found
    # that it takes about 1 minute per 100 networks. The Meraki API
    # automatically throttles requests (it uses a bucket token system), so
    # there isn't a way to speed it up.
    #
    # Therefore, we process the networks in batches of 's_len'. This has two
    # advantages:
    # 1. Conserves memory. This is done by adding each batch to the database
    #    then recreating the DataFrame.
    # 2. Display progress to the end user.
    s_len = 50  # Set the size of each slice (batch).
    slices = list()
    # Create a list of slices.
    while networks:
        slices.append(networks[:s_len])
        if len(networks) >= s_len:
            networks = networks[s_len:]
        else:
            networks = list()

    # Iterate over the slices, adding each slice to the database and displaying
    # progress to the end user.
    counter = 1
    total = len(slices)
    for slice in slices:
        _ = len(slice)
        # Display progress to the end user.
        print(f"Processing {_} networks (batch {counter} of {total})...")

        for network in slice:
            df = pd.DataFrame()
            try:
                result = dashboard.appliance.getNetworkApplianceVlans(network)
                # Create the DataFrame and add it to the database.
                df = pd.DataFrame(result).astype(str)
                # Add the subnets, network IPs, and broadcast IPs.
                addresses = df["subnet"].to_list()
                del df["subnet"]
                result = hp.generate_subnet_details(addresses)
                df["subnet"] = result["subnet"]
                df["network_ip"] = result["network_ip"]
                df["broadcast_ip"] = result["broadcast_ip"]
                # Add a column containing the CIDR notation.
                cidrs = hp.subnet_mask_to_cidr(df["subnet"].to_list())
                df["cidr"] = cidrs
                # Add the DataFrame to the database.
                if counter == 1 and replace_table:
                    database_method = "replace"
                else:
                    database_method = db_method
                rc.add_to_db(
                    f'{ansible_os.split(".")[-1]}_{collector}',
                    df,
                    timestamp,
                    db_path,
                    method=database_method,
                )
            except APIError as e:
                print(f"APIerror: {e}")
            except Exception as e:
                print(f"Error: {e}")
        counter += 1

    return df


async def meraki_get_network_clients(
    api_key: str,
    networks: List[str] = None,
    macs: List[str] = None,
    orgs: List[str] = None,
    per_page: int = 1000,
    print_to_console: bool = False,
    sem: int = 3,
    timespan: int = 300,
    total_pages: Union[int, str] = "all",
) -> pd.DataFrame:
    """
    Retrieves a list of clients connected to specified networks or organizations using
    the Meraki API.

    Parameters
    ----------
    api_key : str
        The user's API key.
    networks : List[str], optional
        A list of network IDs. Defaults to None.
    macs : List[str], optional
        A list of MAC addresses to filter the clients. Defaults to None.
    orgs : List[str], optional
        A list of organization IDs. Defaults to None. If populated, clients for all
        networks in these organizations are returned.
    per_page : int, optional
        The number of clients to retrieve per page. Defaults to 1000.
    print_to_console : bool, optional
        Whether to print Meraki log messages to the console. Defaults to False.
    sem : int, optional
        Maximum number of concurrent requests to the Meraki API. Defaults to 3.
    timespan : int, optional
        The timespan in seconds to retrieve client data for. Defaults to 300 (5
        minutes).
    total_pages : Union[int, str], optional
        The number of pages to return. Defaults to 'all', which retrieves all pages.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the clients for the network(s).

    Examples
    --------
    >>> import asyncio
    >>> api_key = '<your_api_key_here>'
    >>> networks = ['N_123456789012345678', 'N_234567890123456789']
    >>> df = asyncio.run(meraki_get_network_clients(api_key, networks))
    >>> print(df)
    """
    networks = networks or []
    macs = macs or []
    orgs = orgs or []

    async def get_clients_for_network(dashboard, network_id, limiter):
        async with limiter:
            clients = await dashboard.networks.getNetworkClients(
                network_id,
                perPage=per_page,
                timespan=timespan,
                total_pages=total_pages,
                print_console=print_to_console,
            )
            return clients

    if not networks and orgs:
        df_orgs = meraki_get_organizations(api_key)  # Call synchronously
        orgs = df_orgs["id"].to_list()
    if not networks:
        df_networks = meraki_get_org_networks(api_key, orgs=orgs)  # Call synchronously
        networks = df_networks["id"].to_list()

    limiter = AsyncLimiter(sem, 1)  # Initialize limiter

    async with AsyncDashboardAPI(
        api_key,
        print_console=print_to_console,
        maximum_concurrent_requests=sem,
        maximum_retries=20,
        log_path = '/var/log/netbox/'
    ) as dashboard:
        tasks = [get_clients_for_network(dashboard, nid, limiter) for nid in networks]
        results = await asyncio.gather(*tasks)

    data = [client for clients in results for client in clients]
    df_data = {key: [] for key in set().union(*(d.keys() for d in data))}
    for client in data:
        for key in df_data:
            df_data[key].append(client.get(key, None))

    df = pd.DataFrame.from_dict(df_data).astype("str")

    if macs:
        df_clients = (
            pd.concat([df[df["mac"].str.contains(mac)] for mac in macs])
            .drop_duplicates()
            .reset_index(drop=True)
        )
    else:
        df_clients = df.copy()

    return df_clients


def meraki_get_network_devices(
    api_key: str, db_path: str, networks: list = [], orgs: list = []
) -> pd.DataFrame:
    """
    Gets the devices for all orgs that the user's API key has access to.

    This function uses the following logic:

    1. If a user passes a list of networks, the list of orgs is ignored.
    2. If a user passes a list of orgs but not a list of networks, the function
       will query all networks in the list of orgs that the user's API key has
       access to.
    3. If a user does not pass a list of networks or a list of orgs, the
       function will query all networks in all orgs the user's API key has
       access to.

    Parameters
    ----------
    api_key : str
        The user's API key.
    db_path : str
        The path to the database to store results.
    networks : list, optional
        One or more network IDs. Defaults to an empty list.
    orgs : list, optional
        One or more organization IDs. If none are specified, then the devices
        for all orgs will be returned.

    Returns
    -------
    df_devices : pd.DataFrame
        The device statuses for the network(s).

    Examples
    --------
    Example 1:
    >>> api_key = '<your_api_key_here>'
    >>> db_path = '/path/to/database.db'
    >>> networks = ['N_123456789012345678', 'N_234567890123456789']
    >>> df = meraki_get_network_devices(api_key, db_path, networks=networks)
    >>> print(df)

    Example 2:
    >>> api_key = '<your_api_key_here>'
    >>> db_path = '/path/to/database.db'
    >>> orgs = ['O_123456789012345678']
    >>> df = meraki_get_network_devices(api_key, db_path, orgs=orgs)
    >>> print(df)

    Example 3:
    >>> api_key = '<your_api_key_here>'
    >>> db_path = '/path/to/database.db'
    >>> df = meraki_get_network_devices(api_key, db_path)
    >>> print(df)
    """
    # Initialize Meraki dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.networks

    # This list will contain all of the devices for each network. It will be
    # used to create the dataframe. This method accounts for networks that have
    # different device types, since not all device types contain the same keys.
    data = list()

    if not networks:
        # df_networks = meraki_get_org_networks(api_key, db_path)  # , orgs=orgs)
        df_networks = meraki_get_org_networks(api_key, db_path, orgs=orgs)
        if df_networks.empty:
            networks = []
        else:
            networks = df_networks["id"].to_list()

    for net in networks:
        # There is no easy way to check if the user's API key has access to
        # each network, so this is wrapped in a try/except block.
        try:
            devices = app.getNetworkDevices(net)
            for item in devices:
                data.append(item)
        except Exception as e:
            print(str(e))

    df_data = dict()

    # Get all of the keys from devices in 'data', and add them as a key to
    # 'df_data'. The value of the key in 'df_data' will be a list.
    for item in data:
        for key in item:
            if not df_data.get(key):
                df_data[key] = list()

    # Iterate over the devices, adding the data for each device to
    # 'df_data'
    for item in data:
        for key in df_data:
            df_data[key].append(item.get(key))

    # Create and return the dataframe
    df_devices = pd.DataFrame.from_dict(df_data)

    # Convert all data to a string. This is because Pandas incorrectly detects
    # the data type for latitude / longitude, which causes the table insertion
    # to fail.
    df_devices = df_devices.astype(str)

    return df_devices


def meraki_get_network_device_statuses(db_path: str, networks: list) -> pd.DataFrame:
    """
    Gets the statuses of all devices in a network.

    This function leverages the 'meraki_get_org_device_statuses' function as
    there is no specific API endpoint available for retrieving device statuses
    at the network level.

    Parameters
    ----------
    db_path : str
        The path to the database to store the results.
    networks : list
        One or more network IDs.

    Returns
    -------
    df_statuses : pd.DataFrame
        A DataFrame containing the device statuses.

    Examples
    --------
    >>> db_path = '/path/to/database.db'
    >>> networks = ['N_123456789012345678', 'N_234567890123456789']
    >>> df = meraki_get_network_device_statuses(db_path, networks)
    >>> print(df)
    """
    df_statuses = pd.DataFrame()

    con = sl.connect(db_path)

    for network in networks:
        query = f"""SELECT *
        FROM meraki_org_device_statuses
        WHERE networkId = "{network}"
        ORDER BY timestamp desc
        LIMIT 1
        """
        result = pd.read_sql(query, con)
        df_statuses = pd.concat([df_statuses, result])

    con.close()

    # Delete the 'table_id' column, since it was pulled from the
    # 'meraki_org_device_statuses' table and will need to be recreated
    if "table_id" in df_statuses.columns:
        del df_statuses["table_id"]

    return df_statuses


def meraki_get_organizations(api_key: str) -> pd.DataFrame:
    """
    Gets a list of organizations and their associated parameters that the
    user's API key has access to.

    Parameters
    ----------
    api_key : str
        The user's API key.

    Returns
    -------
    df_orgs : pd.DataFrame
        A DataFrame containing a list of organizations the user's API key
        has access to.

    Examples
    --------
    >>> api_key = '<your_api_key_here>'
    >>> df = meraki_get_organizations(api_key)
    >>> print(df)
    """
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)

    # Get the organizations the user has access to and add them to a dataframe
    orgs = dashboard.organizations.getOrganizations()

    df_orgs = pd.DataFrame(orgs).astype(str)

    return df_orgs


def meraki_get_org_appliance_uplink_statuses(
    api_key: str, db_path: str, orgs: list = []
) -> pd.DataFrame:
    """Gets the uplink statuses for appliances in a list of organizations.

    This API endpoint also returns some associated data, like uplink IP
    addresses.

    Parameters
    ----------
    api_key : str
        The user's API key.
    db_path : str
        The path to the database to store results.
    orgs : list, optional
        One or more organization IDs. If none are specified, then the devices
        for all orgs will be returned. Defaults to an empty list.

    Returns
    -------
    df : pd.DataFrame
        The appliance uplinks for the organizations.

    Examples
    --------
    >>> api_key = '<your_api_key_here>'
    >>> db_path = '/path/to/database.db'
    >>> orgs = ['org_id_1', 'org_id_2']
    >>> df = meraki_get_org_devices(api_key, db_path, orgs)
    >>> print(df)
    """
    # Get the organizations (collected by 'meraki_get_orgs') from the database
    table = "meraki_organizations"
    organizations = hp.meraki_parse_organizations(db_path, orgs, table)

    # Initialize Meraki dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.appliance

    # This list will contain all of the uplinks for each org. It will then be
    # used to create the dataframe. This method accounts for uplinks that might
    # not have the same keys.
    results = list()
    for org in organizations:
        # Check if API access is enabled for the org
        enabled = mhp.meraki_check_api_enablement(db_path, org)
        if enabled:
            uplinks = app.getOrganizationApplianceUplinkStatuses(org, total_pages="all")
            for uplink in uplinks:
                uplink["orgId"] = org
            results.append(uplinks)

    # Combine the uplinks from the orgs into a single list.
    data = [_ for uplink in results for _ in uplink]

    df_data = list()

    for item in data:
        row = {}
        row["networkId"] = item["networkId"]
        row["serial"] = item["serial"]
        row["model"] = item["model"]
        row["highAvailability"] = item["highAvailability"]["role"]
        row["lastReportedAt"] = item["lastReportedAt"]
        row["uplinks"] = len(item["uplinks"])

        for uplink in item["uplinks"]:
            prefix = "wan1" if uplink["interface"] == "wan1" else "wan2"
            row[f"{prefix}_interface"] = uplink["interface"]
            row[f"{prefix}_status"] = uplink["status"]
            row[f"{prefix}_ip"] = uplink["ip"]
            row[f"{prefix}_gateway"] = uplink["gateway"]
            row[f"{prefix}_publicIp"] = uplink["publicIp"]
            row[f"{prefix}_primaryDns"] = uplink.get("primaryDns", None)
            row[f"{prefix}_secondaryDns"] = uplink.get("secondaryDns", None)
            row[f"{prefix}_ipAssignedBy"] = uplink.get("ipAssignedBy")

        df_data.append(row)

    # Convert the list of dictionaries to a DataFrame and return it.
    df = pd.DataFrame(df_data)

    return df


def meraki_get_org_devices(api_key: str, db_path: str, orgs: list = []) -> pd.DataFrame:
    """
    Gets the devices for all orgs that the user's API key has access to. If the user
    specifies an optional list of organization IDs, then the function will only return
    the devices for those organizations.

    Parameters
    ----------
    api_key : str
        The user's API key.
    db_path : str
        The path to the database to store results.
    orgs : list, optional
        One or more organization IDs. If none are specified, then the devices
        for all orgs will be returned. Defaults to an empty list.

    Returns
    -------
    df_devices : pd.DataFrame
        The device statuses for the organizations.

    Examples
    --------
    >>> api_key = '<your_api_key_here>'
    >>> db_path = '/path/to/database.db'
    >>> orgs = ['org_id_1', 'org_id_2']
    >>> df = meraki_get_org_devices(api_key, db_path, orgs)
    >>> print(df)
    """
    # Get the organizations (collected by 'meraki_get_orgs') from the database
    table = "meraki_organizations"
    organizations = hp.meraki_parse_organizations(db_path, orgs, table)

    # Initialize Meraki dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.organizations

    # This list will contain all of the devices for each org. It will then be
    # used to create the dataframe. This method accounts for orgs that have
    # different device types, since not all device types contain the same keys.
    data = list()
    for org in organizations:
        # Check if API access is enabled for the org
        enabled = mhp.meraki_check_api_enablement(db_path, org)
        if enabled:
            devices = app.getOrganizationDevices(org, total_pages="all")
            for item in devices:
                item["orgId"] = org
                data.append(item)

    df_data = dict()
    df_data["orgId"] = list()

    # Get all of the keys from devices in 'data', and add them as a key to
    # 'df_data'. The value of the key in 'df_data' will be a list.
    for item in data:
        for key in item:
            if not df_data.get(key) and key != "orgId":
                df_data[key] = list()

    # Iterate over the devices, adding the data for each device to 'df_data'
    for item in data:
        for key in df_data:
            df_data[key].append(item.get(key))

    # Create the dataframe
    df_devices = pd.DataFrame.from_dict(df_data)

    # Convert all data to a string. This is because Pandas incorrectly detects
    # the data type for latitude / longitude, which causes the table insertion
    # to fail.
    df_devices = df_devices.astype(str)

    return df_devices


def meraki_get_org_device_statuses(
    api_key: str, db_path: str, orgs: list = [], total_pages="all"
) -> tuple:
    """
    Gets the device statuses for all organizations the user's API key has
    access to.

    Parameters
    ----------
    api_key : str
        The user's API key.
    db_path : str
        The path to the database to store results.
    orgs : list, optional
        One or more organization IDs. If none are specified, then the device
        statuses for all orgs will be returned. Defaults to an empty list.
    total_pages : int or str, optional
        The number of pages to retrieve. Defaults to 'all'. Note that a value
        besides 'all' must be an integer.

    Returns
    -------
    tuple
        A tuple containing:
        - df_statuses : pd.DataFrame
            The device statuses for the organizations.
        - idx_cols : list
            The column names to use for creating the SQL table index.

    Examples
    --------
    >>> api_key = '<your_api_key_here>'
    >>> db_path = '/path/to/database.db'
    >>> orgs = ['org_id_1', 'org_id_2']
    >>> total_pages = 5
    >>> df, idx_cols = meraki_get_org_device_statuses(api_key,
                                                      db_path,
                                                      orgs,
                                                      total_pages)
    >>> print(df)
    >>> print(idx_cols)
    """
    # Initialize Meraki dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.organizations

    # If the user did not specify any organization IDs, then get them by
    # querying the database
    if not orgs:
        table = "meraki_organizations"
        orgs = hp.meraki_parse_organizations(db_path, orgs, table)

    # Create a list to store raw results from the API (the results are
    # returned as a list of dictionaries--one dictionary per device)
    data = list()

    # Query the API for the device statuses and add them to 'data')
    tp = total_pages
    for org in orgs:
        # Check if API access is enabled for the org
        enabled = mhp.meraki_check_api_enablement(db_path, org)
        if enabled:
            statuses = app.getOrganizationDevicesStatuses(org, total_pages=tp)
            for item in statuses:
                item["orgId"] = org  # Add the orgId to each device status
                data.append(item)

    # Create the dictionary 'df_data' from the device statuses in 'data'.
    # This method adds all possible keys from the devices to 'df_data' before
    # adding the device statuses to 'df_data'. If a device status does not
    # contain a particular key then it will be added as None
    df_data = dict()
    for item in data:
        for key in item:
            if not df_data.get(key):
                df_data[key] = list()

    # Populate 'df_data'
    for item in data:
        for key in df_data:
            df_data[key].append(item.get(key))

    # Create the dataframe and return it
    df_statuses = pd.DataFrame.from_dict(df_data)

    # Set all datatypes to string. Otherwise it will fail when adding the
    # dataframe to the database
    df_statuses = df_statuses.astype(str)

    # Set the columns to use for the SQL database table index
    idx_cols = ["timestamp", "mac"]

    return df_statuses, idx_cols


def meraki_get_org_networks(
    api_key: str, db_path: str = "", orgs: list = [], use_db: bool = False
) -> pd.DataFrame:
    """
    Gets the networks for one or more organizations.

    Parameters
    ----------
    api_key : str
        The user's API key.
    db_path : str, optional
        The path to the database to store results. Defaults to an empty string.
    orgs : list, optional
        A list of organization IDs to query. Note that the function assumes
        that the orgs are accessible with the user's API key. It will not do a
        separate check unless 'use_db' is set to True. Defaults to an empty
        list.
    use_db : bool, optional
        Whether to use a database. Results will be stored in memory if this is
        set to False. Defaults to False.

    Returns
    -------
    df_networks : pd.DataFrame
        The networks in one or more organizations.

    Examples
    --------
    >>> api_key = '<your_api_key_here>'
    >>> db_path = '/path/to/database.db'
    >>> orgs = ['org_id_1', 'org_id_2']
    >>> use_db = True
    >>> df = meraki_get_org_networks(api_key, db_path, orgs, use_db)
    >>> print(df)
    """
    if use_db:
        # Get the organizations (collected by 'meraki_get_orgs') from the
        # database
        table = "meraki_organizations"
        organizations = hp.meraki_parse_organizations(db_path, orgs, table)
    else:
        if not orgs:
            orgs = meraki_get_organizations(api_key)
            orgs = orgs["id"].to_list()
        organizations = orgs
    # Initialize Meraki dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.organizations

    # Create a list to store the results for all orgs. This is necessary to
    # ensure that the DataFrame contains columns for all networks (not all
    # networks return the same keys)
    data = list()

    df_data = dict()
    for org in organizations:
        if use_db:
            # Check if API access is enabled for the org
            enabled = mhp.meraki_check_api_enablement(db_path, org)
        else:
            enabled = False
        if enabled or not use_db:
            try:
                networks = app.getOrganizationNetworks(org, total_pages="all")
            except Exception as e:
                print(f"Network lookup for org {org} failed.\nerror: {e}")
                networks = []
            for item in networks:
                data.append(item)

    # Iterate over 'data', creating the keys for the DataFrame
    for item in data:
        for key in item:
            if not df_data.get(key):
                df_data[key] = list()

    # Iterate over 'data', adding the networks to 'df_data'
    for item in data:
        for key in df_data:
            df_data[key].append(item.get(key))

    df_networks = pd.DataFrame.from_dict(df_data).astype(str)

    return df_networks


def meraki_get_switch_lldp_neighbors(db_path: str) -> pd.DataFrame:
    """
    Uses the data returned from the 'meraki_get_switch_port_statuses' collector
    to create a dataframe containing switch LLDP neighbors.

    Parameters
    ----------
    db_path : str
        The path to the database containing the
        'meraki_get_switch_port_statuses' collector output.

    Returns
    -------
    pd.DataFrame
        A dataframe containing the LLDP neighbors for the switch(es).

    Examples
    --------
    >>> db_path = '/path/to/database.db'
    >>> df_lldp = meraki_get_switch_lldp_neighbors(db_path)
    >>> print(df_lldp)
    """
    # Check to see if the 'MERAKI_SWITCH_PORT_STATUSES' table exists, and that the
    # 'portId' column is present.
    df_schema = hp.sql_get_table_schema(db_path, "MERAKI_SWITCH_PORT_STATUSES")

    if "portId" in df_schema.columns.to_list():
        # Query the database to get the LLDP neighbors
        headers = [
            "orgId",
            "networkId",
            "name",
            "serial",
            "portId as local_port",
            "lldp",
        ]
        query = f"""SELECT {','.join(headers)}
        FROM MERAKI_SWITCH_PORT_STATUSES
        WHERE lldp != 'None'
        """
        con = sl.connect(db_path)
        result = pd.read_sql(query, con)

        # Rename 'portId as local_port' to 'local_port' and update 'headers'
        result.rename(columns={"portId as local": "local_port"}, inplace=True)
        headers = result.columns.to_list()

        # Add result['lldp'] to a list and convert each item into a dictionary. The
        # dictionaries will be used to create the column headers.
        lldp_col = result["lldp"].to_list()
        lldp_col = [json.loads(_.replace("'", '"')) for _ in lldp_col]

        # keys = headers
        keys = list()
        for item in lldp_col:
            for key in item:
                if key not in keys:
                    keys.append(key)

        # Create a list to store the data that will be used to create the
        # dataframe. This method ensures that keys that the Meraki API did not
        # return (because they were empty) are added to 'df_lldp'
        df_data = list()

        for idx, row in result.iterrows():
            _row = [
                row["orgId"],
                row["networkId"],
                row["name"],
                row["serial"],
                row["local_port"],
            ]
            lldp = json.loads(row["lldp"].replace("'", '"'))
            for key in keys:
                _row.append(lldp.get(key))
            df_data.append(_row)

        headers.reverse()
        for item in headers:
            if item != "lldp":
                keys.insert(0, item)

        # Create the dataframe
        df_lldp = pd.DataFrame(data=df_data, columns=keys)

        df_lldp.rename(columns={"portId": "remote_port"}, inplace=True)

        # Re-order columns. Only certain columns are selected. This ensures that
        # the code will continue to function if Meraki adds additional keys in the
        # future.
        col_order = [
            "orgId",
            "networkId",
            "name",
            "serial",
            "local_port",
            "remote_port",
            "systemName",
            "chassisId",
            "systemDescription",
            "managementAddress",
        ]

        # Reverse the list so the last item becomes the first column, the next to
        # last item becomes the second column, and so on.
        col_order.reverse()
        # Re-order the columns
        for c in col_order:
            df_lldp.insert(0, c, df_lldp.pop(c))
        return df_lldp
    # If the MERAKI_SWITCH_PORT_STATUSES table does not exist or the portId column is
    # not present.
    else:
        return pd.DataFrame()


def meraki_get_switch_port_statuses(
    api_key: str, db_path: str, orgs: list = []
) -> pd.DataFrame:
    """
    Gets the port statuses and associated data (including errors and warnings) for all
    Meraki switches in the specified orgs. If no orgs are specified, then the switches
    for all orgs that the user's API key has access to will be returned.

    Parameters
    ----------
    api_key : str
        The user's API key.
    db_path : str
        The path to the database to store results.
    orgs : list, optional
        The orgs in which to gather switch port statuses. If none are
        provided, then all switch ports for all orgs will be returned
        (which could take several minutes in large organizations).

    Returns
    -------
    df_ports : pd.DataFrame
        The port statuses.
    """
    if orgs:
        # Query the database to get all switches in the orgs(s)
        statement = f'''orgId = "{'" or orgId = "'.join(orgs)}"'''
        query = f"""SELECT distinct orgId, networkId, name, serial
        FROM MERAKI_ORG_DEVICES
        WHERE ({statement}) and productType = 'switch'
        """
    else:
        # Query the database to get all switches that the user's API key has access to
        # in the 'MERAKI_ORG_DEVICES' table.
        query = '''SELECT distinct orgId, networkId, name, serial
                    FROM MERAKI_ORG_DEVICES
                    WHERE productType = "switch"'''

    con = sl.connect(db_path)
    df_ports = pd.read_sql(query, con)

    # Initialize the dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.switch

    # Get the port statuses for the switches in df_ports
    data = dict()
    for idx, row in df_ports.iterrows():
        orgId = row["orgId"]
        networkId = row["networkId"]
        name = row["name"]
        serial = row["serial"]

        data[serial] = dict()

        ports = app.getDeviceSwitchPortsStatuses(serial)
        for port in ports:
            port_id = port["portId"]
            data[serial][port_id] = dict()
            data[serial][port_id]["orgId"] = orgId
            data[serial][port_id]["networkId"] = networkId
            data[serial][port_id]["name"] = name
            data[serial][port_id]["serial"] = serial
            for key, value in port.items():
                data[serial][port_id][key] = value

    # Create a dictionary based on the contents of 'data'. This method ensures
    # that all arrays are of equal length when we create the dataframe.
    df_data = dict()
    df_data["orgId"] = list()
    df_data["networkId"] = list()
    df_data["name"] = list()
    df_data["serial"] = list()
    for item in data:
        device = data[item]
        for port in device:
            for key in device[port]:
                if not df_data.get(key):
                    df_data[key] = list()

    for item in data:
        device = data[item]
        for port in device:
            for key in df_data:
                df_data[key].append(device[port].get(key))

    df_ports = pd.DataFrame.from_dict(df_data)
    df_ports = df_ports.astype(str)

    return df_ports


def meraki_get_switch_port_usages(api_key: str, db_path: str, networks: list,
                                  timestamp: str) -> pd.DataFrame:
    '''
    Gets switch port usage in total rate per second.

    Parameters
    ----------
    api_key : str
        The user's API key.
    db_path : str
        The path to the database to store results.
    networks : list
        The networks in which to gather switch port statuses.
    timestamp : str
        The timestamp passed to run_collectors.

    Returns
    -------
    pd.DataFrame
        The port usages.

    Examples
    --------
    >>> api_key = '<your_api_key_here>'
    >>> db_path = '/path/to/database.db'
    >>> networks = ['N_123456789012345678', 'N_234567890123456789']
    >>> timestamp = '2022-01-01_0000'
    >>> df_usage = meraki_get_switch_port_usages(api_key,
                                                 db_path,
                                                 networks,
                                                 timestamp)
    >>> print(df_usage)
    '''
    # Query the database to get all switches in the network(s)
    statement = f'''networkId = "{'" or networkId = "'.join(networks)}"'''
    if networks:
        query = f'''SELECT distinct orgId, networkId, name, serial, portId
        FROM MERAKI_SWITCH_PORT_STATUSES
        WHERE {statement} and timestamp = "{timestamp}"
        '''
    else:
        query = f'''SELECT distinct orgId, networkId, name, serial, portId
        FROM MERAKI_SWITCH_PORT_STATUSES WHERE timestamp = "{timestamp}"'''

    con = sl.connect(db_path)
    df_devices = pd.read_sql(query, con)
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.switch

    # Extract the unique serials
    serials = [*set(df_devices['serial'].to_list())]

    # Convert the dataframe to a list. The keys will be the column names, and
    # the values will be a list containing the column data
    df_data = df_devices.to_dict('list')
    # Create empty lists for rate per second data that will be collected
    df_data['ratePerSec'] = list()
    df_data['sentRatePerSec'] = list()
    df_data['recvRatePerSec'] = list()

    # Get the port usage for each device in the network(s), and add it to
    # df_data
    for serial in serials:
        for item in app.getDeviceSwitchPortsStatusesPackets(serial):
            ratePerSec = item['packets'][0]['ratePerSec']['total']
            sentRatePerSec = item['packets'][0]['ratePerSec']['sent']
            recvRatePerSec = item['packets'][0]['ratePerSec']['recv']
            df_data['ratePerSec'].append(ratePerSec)
            df_data['sentRatePerSec'].append(sentRatePerSec)
            df_data['recvRatePerSec'].append(recvRatePerSec)

    # Create and return df_usage
    df_usage = pd.DataFrame.from_dict(df_data)

    return df_usage


async def meraki_get_switch_ports(
    api_key: str, orgs: list = [], sem: int = 3
) -> pd.DataFrame:
    """
    Gets a list of switchports that the user's API key has access to.

    Parameters
    ----------
    api_key : str
        The user's API key.
    orgs : list, optional
        A list of organization IDs for which to get the switch ports. If not specified,
        then the switch ports for all organizations that a user's API key can access
        will be returned. Defaults to an empty list.
    sem : int, optional
        The Semaphore used to limit the maximum number of concurrent requests
        to the Meraki API. Defaults to 3.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing a list of devices and ports the user's API key
        has access to.

    Examples
    --------
    >>> api_key = '<your_api_key_here>'
    >>> df = meraki_get_switch_ports(api_key)
    >>> df.columns
        Index(["device",
        "portId",
        "name",
        "tags",
        "enabled",
        "poeEnabled",
        "type",
        "vlan",
        "voiceVlan",
        "allowedVlans",
        "rstpEnabled",
        "stpGuard",
        "linkNegotiation",
        "accessPolicyType"],
        dtype='object')
    """
    sem = asyncio.Semaphore(sem)

    async def get_switch_ports_for_org(dashboard, org):
        try:
            return await dashboard.switch.getOrganizationSwitchPortsBySwitch(org)
        except AsyncAPIError:
            return []

    if not orgs:
        orgs = meraki_get_organizations(api_key)
        orgs = orgs["id"].to_list()

    data = list()

    async with AsyncDashboardAPI(
        api_key,
        print_console=False,
    ) as dashboard:
        result = await asyncio.gather(
            *(get_switch_ports_for_org(dashboard, org) for org in orgs)
        )
        for res in result:
            for row in res:
                if not row:
                    continue
                device = row["name"]
                for idx, port in enumerate(row["ports"]):
                    row["ports"][idx]["device"] = device
                    data.append(row["ports"][idx])

    df = pd.DataFrame(data)
    try:
        # Move the 'device' column to be the first column
        col_order = ["device"] + [col for col in df if col != "device"]
        df = df[col_order]
        df = hp.convert_lists_to_json_in_df(df)
        # Convert all float columns to int
        for col in df.columns:
            if df[col].dtype == "float64":
                df[col] = df[col].astype("Int64")
        df = df.astype(str)
    except KeyError:
        pass
    return df


async def meraki_get_appliance_ports(
    api_key: str, org_ids: list = None, sem: int = 3
) -> pd.DataFrame:
    """
    Gets a list of appliance ports that the
    user's API key has access to, optionally filtered by organization IDs.

    Parameters
    ----------
    api_key : str
        The user's API key.
    org_ids : list, optional
        A list of organization IDs to filter the appliance ports by.
    sem : int, optional
        The Semaphore used to limit the maximum number of concurrent requests
        to the Meraki API. Defaults to 3.

    Returns
    -------
    df_orgs : pd.DataFrame
        A DataFrame containing a list of appliance and ports the user's API key
        has access to.

    Examples
    --------
    >>> api_key = '<your_api_key_here>'
    >>> df = meraki_get_appliance_ports(api_key, org_ids=['123', '456'])
    >>> df.columns
        Index(['device',
        'number',
        'enabled',
        'type',
        'dropUntaggedTraffic',
        'allowedVlans',
        'vlan',
        'accessPolicy'],
        dtype='object')
    """
    sem = asyncio.Semaphore(sem)

    async def get_all_networks(dashboard, organization_id):
        try:
            return await dashboard.organizations.getOrganizationNetworks(
                organizationId=organization_id, total_pages="all"  # Fetch all pages
            )
        except AsyncAPIError as e:
            print(f"Error accessing organization {organization_id}: {e}")
            return []

    async def get_switch_ports_for_appl(dashboard, net):
        try:
            res = await dashboard.appliance.getNetworkAppliancePorts(net["id"])
            data = [{**item, "device": net["name"]} for item in res]
            return data
        except Exception as e:
            print(f"Error fetching ports for network {net['id']}: {e}")
            return []

    # Get list of organizations
    all_orgs = meraki_get_organizations(api_key)

    # Filter organizations if org_ids is provided
    if org_ids is not None:
        orgs = all_orgs[all_orgs["id"].isin(org_ids)]
    else:
        orgs = all_orgs

    orgs_list = orgs["id"].to_list()

    data = list()

    async with AsyncDashboardAPI(api_key, print_console=False) as dashboard:
        networks_result = await asyncio.gather(
            *(get_all_networks(dashboard, org) for org in orgs_list)
        )

        networks = [
            {"id": net["id"], "name": net["name"]}
            for sublist in networks_result
            for net in sublist
            if net
        ]

        ports_result = await asyncio.gather(
            *(get_switch_ports_for_appl(dashboard, net) for net in networks)
        )

        for res in ports_result:
            data.extend(res)

    df = pd.DataFrame(data)
    # Move the 'device' column to be the first column
    col_order = ["device"] + [col for col in df if col != "device"]
    df = df[col_order]
    # Convert all float columns to int
    for col in df.columns:
        if df[col].dtype == "float64":
            df[col] = df[col].astype("Int64")
    df = df.astype(str)
    df = df.replace("nan", "")
    return df
