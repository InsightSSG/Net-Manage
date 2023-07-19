#!/usr/bin/env python3

'''
Define Meraki collectors.
'''

import json
import meraki
import pandas as pd
from netmanage import run_collectors as rc
import sqlite3 as sl

from netmanage.helpers import helpers as hp
from meraki.exceptions import APIError
from typing import Union


def get_network_appliance_vlans(ansible_os: str,
                                api_key: str,
                                collector: str,
                                db_path: str,
                                timestamp: str,
                                db_method: str = 'append',
                                networks: list = [],
                                orgs: list = [],
                                replace_table: bool = False) -> pd.DataFrame:
    '''
    Get the appliance VLANs for a list of networks or organizations.

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
    '''

    # If 'networks' and 'orgs' are empty, then gracefully exit the function.
    if not networks and not orgs:
        return pd.DataFrame()

    # If 'networks' is empty and 'orgs' is not, get all applicable networks in
    # the orgs.
    if orgs and not networks:
        joined_orgs = [f'"{_}"' for _ in orgs]
        joined_orgs = ', '.join(joined_orgs)

        con = sl.connect(db_path)

        # Get the last timestamp in the MERAKI_ORG_NETWORKS table.
        query = '''SELECT distinct timestamp
        FROM meraki_org_networks
        ORDER BY timestamp desc
        LIMIT 1
        '''
        result = pd.read_sql(query, con)
        ts = result['timestamp'].to_list().pop()

        # Get the unique network IDs for the most recent timestamp.
        query = f'''SELECT distinct id
        FROM meraki_org_networks
        WHERE productTypes like "%appliance%"
            AND timestamp = "{ts}"
            AND organizationId IN ({joined_orgs})'''
        result = pd.read_sql(query, con)
        networks = result['id'].to_list()

    # Get the appliance vlans for each network. Note: if 'orgs' and 'networks'
    # are both non-empty, then 'orgs' is ignored. The list of networks takes
    # priority.
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)

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
        print(f'Processing {_} networks (batch {counter} of {total})...')

        for network in slice:
            df = pd.DataFrame()
            try:
                result = dashboard.appliance.getNetworkApplianceVlans(network)
                # Create the DataFrame and add it to the database.
                df = pd.DataFrame(result).astype(str)
                # Add the subnets, network IPs, and broadcast IPs.
                addresses = df['subnet'].to_list()
                del df['subnet']
                result = hp.generate_subnet_details(addresses)
                df['subnet'] = result['subnet']
                df['network_ip'] = result['network_ip']
                df['broadcast_ip'] = result['broadcast_ip']
                # Add the DataFrame to the database.
                if counter == 1 and replace_table:
                    database_method = 'replace'
                else:
                    database_method = db_method
                rc.add_to_db(f'{ansible_os.split(".")[-1]}_{collector}',
                             df,
                             timestamp,
                             db_path,
                             method=database_method)
            except APIError:
                pass
        counter += 1

    return df


def meraki_get_network_clients(api_key: str,
                               networks: list,
                               macs: list = [],
                               per_page: int = 1000,
                               timespan: int = 86400,
                               total_pages: Union[int, str] = 'all') \
                                -> pd.DataFrame:
    '''
    Gets the list of clients on a network.

    Parameters
    ----------
    api_key : str
        The user's API key.
    networks : list
        One or more network IDs.
    macs : list, optional
        A list of MAC addresses to filter the clients. Defaults to an empty
        list.
    per_page : int, optional
        The number of clients to retrieve per page. Defaults to 1000.
    timespan : int, optional
        The timespan in seconds to retrieve client data for. Defaults to 86400
        (24 hours).
    total_pages : int or str, optional
        The total number of pages to retrieve. If set to 'all', it will
        retrieve all available pages. Defaults to 'all'.

    Returns
    -------
    df_clients : pd.DataFrame
        A Pandas DataFrame containing the clients for the network(s).

    Examples
    --------
    Example 1:
    >>> api_key = '<your_api_key_here>'
    >>> networks = ['N_123456789012345678', 'N_234567890123456789']
    >>> df = meraki_get_network_clients(api_key, networks)
    >>> print(df)

    Example 2:
    >>> api_key = '<your_api_key_here>'
    >>> networks = ['N_123456789012345678', 'N_234567890123456789']
    >>> macs = ['00:11:22:33:44:55', 'AA:BB:CC:DD:EE:FF']
    >>> df = meraki_get_network_clients(api_key, networks, macs=macs)
    >>> print(df)
    '''
    # Create a list to store the individual clients for each network.
    data = list()

    # Iterate over the network(s), gathering the clients and adding them to
    # 'data'
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    for network in networks:
        clients = dashboard.networks.getNetworkClients(network,
                                                       timespan=timespan,
                                                       perPage=per_page,
                                                       total_pages=total_pages)
        for client in clients:
            data.append(client)

    # Create a dictionary to store the client data. It will be used to create
    # 'df_clients'
    df_data = dict()

    # Each client is returned as a dictionary. Iterate over the keys in the
    # dictionary and add them to 'df_data'. This requires iterating over all
    # the clients twice, but it ensures that all keys are added to 'df_data'.
    for client in data:
        for key in client:
            df_data[key] = list()

    # Iterate over the clients, adding the data to 'df_data'
    for client in data:
        for key in df_data:
            df_data[key].append(client.get(key))

    # Create the dataframe and convert all datatypes to strings
    df = pd.DataFrame.from_dict(df_data)
    df = df.astype('str')

    # Create 'df_clients'. If the user has provided a list of MACs, then only
    # add those clients to 'df_clients'. Otherwise, add all clients.
    if macs:
        df_clients = pd.DataFrame()
        for mac in macs:
            mask = df['mac'].str.contains(mac)
            df_clients = pd.concat([df_clients, df[mask]])
        # Drop duplicate rows. They can be created if a user esarches for
        # partial MAC addresses that overlap (e.g., 'ec:f0', 'ec:f0:b6')
        df_clients = df_clients.drop_duplicates()
        df_clients = df_clients.reset_index(drop=True)
    else:
        df_clients = df.copy()

    return df_clients


def meraki_get_network_devices(api_key: str,
                               db_path: str,
                               networks: list = [],
                               orgs: list = []) -> pd.DataFrame:
    '''
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
    '''
    # Initialize Meraki dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.networks

    # This list will contain all of the devices for each network. It will be
    # used to create the dataframe. This method accounts for networks that have
    # different device types, since not all device types contain the same keys.
    data = list()

    if not networks:
        df_networks = meraki_get_org_networks(api_key, db_path)  # , orgs=orgs)
        print(df_networks)
        networks = df_networks['network_id'].to_list()

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


def meraki_get_network_device_statuses(db_path: str,
                                       networks: list) -> pd.DataFrame:
    '''
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
    '''
    df_statuses = pd.DataFrame()

    con = sl.connect(db_path)

    for network in networks:
        query = f'''SELECT *
        FROM meraki_org_device_statuses
        WHERE networkId = "{network}"
        ORDER BY timestamp desc
        LIMIT 1
        '''
        result = pd.read_sql(query, con)
        df_statuses = pd.concat([df_statuses, result])

    con.close()

    # Delete the 'table_id' column, since it was pulled from the
    # 'meraki_org_device_statuses' table and will need to be recreated
    del df_statuses['table_id']

    return df_statuses


def meraki_get_organizations(api_key: str) -> pd.DataFrame:
    '''
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
    '''
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)

    # Get the organizations the user has access to and add them to a dataframe
    orgs = dashboard.organizations.getOrganizations()

    df_orgs = pd.DataFrame(orgs).astype(str)

    # df_data = list()

    # for item in orgs:
    #     df_data.append([item['id'],
    #                     item['name'],
    #                     item['url'],
    #                     item['api']['enabled'],
    #                     item['licensing']['model'],
    #                     item['cloud']['region']['name'],
    #                     '|'.join(item['management']['details'])]
    #                    )
    # cols = ['org_id',
    #         'name',
    #         'url',
    #         'api',
    #         'licensing_model',
    #         'cloud_region',
    #         'management_details']

    # df_orgs = pd.DataFrame(data=df_data, columns=cols).astype(str)

    return df_orgs


def meraki_get_org_devices(api_key: str,
                           db_path: str,
                           orgs: list = []) -> pd.DataFrame:
    '''
    Gets the devices for all orgs that the user's API key has access to.

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
    '''
    # Get the organizations (collected by 'meraki_get_orgs') from the database
    table = 'meraki_organizations'
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
        enabled = hp.meraki_check_api_enablement(db_path, org)
        if enabled:
            devices = app.getOrganizationDevices(org, total_pages="all")
            for item in devices:
                item['orgId'] = org
                data.append(item)

    df_data = dict()
    df_data['orgId'] = list()

    # Get all of the keys from devices in 'data', and add them as a key to
    # 'df_data'. The value of the key in 'df_data' will be a list.
    for item in data:
        for key in item:
            if not df_data.get(key) and key != 'orgId':
                df_data[key] = list()

    # Iterate over the devices, adding the data for each device to 'df_data'
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


def meraki_get_org_device_statuses(api_key: str,
                                   db_path: str,
                                   orgs: list = [],
                                   total_pages='all') -> tuple:
    '''
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
    '''
    # Initialize Meraki dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.organizations

    # If the user did not specify any organization IDs, then get them by
    # querying the database
    if not orgs:
        table = 'meraki_organizations'
        orgs = hp.meraki_parse_organizations(db_path, orgs, table)

    # Create a list to store raw results from the API (the results are
    # returned as a list of dictionaries--one dictionary per device)
    data = list()

    # Query the API for the device statuses and add them to 'data')
    tp = total_pages
    for org in orgs:
        # Check if API access is enabled for the org
        enabled = hp.meraki_check_api_enablement(db_path, org)
        if enabled:
            statuses = app.getOrganizationDevicesStatuses(org, total_pages=tp)
            for item in statuses:
                item['orgId'] = org  # Add the orgId to each device status
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
    idx_cols = ['timestamp', 'mac', 'table_id']

    return df_statuses, idx_cols


def meraki_get_org_networks(api_key: str,
                            db_path: str = '',
                            orgs: list = [],
                            use_db: bool = False) -> pd.DataFrame:
    '''
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
    pd.DataFrame
        The networks in one or more organizations.

    Examples
    --------
    >>> api_key = '<your_api_key_here>'
    >>> db_path = '/path/to/database.db'
    >>> orgs = ['org_id_1', 'org_id_2']
    >>> use_db = True
    >>> df = meraki_get_org_networks(api_key, db_path, orgs, use_db)
    >>> print(df)
    '''
    if use_db:
        # Get the organizations (collected by 'meraki_get_orgs') from the
        # database
        table = 'meraki_organizations'
        organizations = hp.meraki_parse_organizations(db_path, orgs, table)
    else:
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
            enabled = hp.meraki_check_api_enablement(db_path, org)
        else:
            enabled = False
        if enabled or not use_db:
            networks = app.getOrganizationNetworks(org, total_pages="all")
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
    '''
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
    '''
    # Query the database to get the LLDP neighbors
    headers = ['orgId',
               'networkId',
               'name',
               'serial',
               'portId as local_port',
               'lldp']
    query = f'''SELECT {','.join(headers)}
    FROM MERAKI_SWITCH_PORT_STATUSES
    WHERE lldp != 'None'
    '''
    con = sl.connect(db_path)
    result = pd.read_sql(query, con)

    # Rename 'portId as local_port' to 'local_port' and update 'headers'
    result.rename(columns={'portId as local': 'local_port'}, inplace=True)
    headers = result.columns.to_list()

    # Add result['lldp'] to a list and convert each item into a dictionary. The
    # dictionaries will be used to create the column headers.
    lldp_col = result['lldp'].to_list()
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
        _row = [row['orgId'],
                row['networkId'],
                row['name'],
                row['serial'],
                row['local_port']]
        lldp = json.loads(row['lldp'].replace("'", '"'))
        for key in keys:
            _row.append(lldp.get(key))
        df_data.append(_row)

    headers.reverse()
    for item in headers:
        if item != 'lldp':
            keys.insert(0, item)

    # Create the dataframe
    df_lldp = pd.DataFrame(data=df_data, columns=keys)

    df_lldp.rename(columns={'portId': 'remote_port'}, inplace=True)

    # Re-order columns. Only certain columns are selected. This ensures that
    # the code will continue to function if Meraki adds additional keys in the
    # future.
    col_order = ['orgId',
                 'networkId',
                 'name',
                 'serial',
                 'local_port',
                 'remote_port',
                 'systemName',
                 'chassisId',
                 'systemDescription',
                 'managementAddress']

    # Reverse the list so the last item becomes the first column, the next to
    # last item becomes the second column, and so on.
    col_order.reverse()
    # Re-order the columns
    for c in col_order:
        df_lldp.insert(0, c, df_lldp.pop(c))

    return df_lldp


def meraki_get_switch_port_statuses(api_key: str,
                                    db_path: str,
                                    networks: list) -> pd.DataFrame:
    '''
    Gets the port statuses and associated data (including errors and warnings)
    for all Meraki switches in the specified network(s).

    Parameters
    ----------
    api_key : str
        The user's API key.
    db_path : str
        The path to the database to store results.
    networks : list
        The networks in which to gather switch port statuses.

    Returns
    -------
    pd.DataFrame
        The port statuses.

    Examples
    --------
    >>> api_key = '<your_api_key_here>'
    >>> db_path = '/path/to/database.db'
    >>> networks = ['N_123456789012345678', 'N_234567890123456789']
    >>> df_ports = meraki_get_switch_port_statuses(api_key, db_path, networks)
    >>> print(df_ports)
    '''
    # Query the database to get all switches in the network(s)
    statement = f'''networkId = "{'" or networkId = "'.join(networks)}"'''
    query = f'''SELECT distinct orgId, networkId, name, serial
    FROM MERAKI_ORG_DEVICES
    WHERE ({statement}) and productType = 'switch'
    '''

    con = sl.connect(db_path)
    df_ports = pd.read_sql(query, con)

    # Initialize the dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.switch

    # Get the port statuses for the switches in df_ports
    data = dict()
    for idx, row in df_ports.iterrows():
        orgId = row['orgId']
        networkId = row['networkId']
        name = row['name']
        serial = row['serial']

        data[serial] = dict()

        ports = app.getDeviceSwitchPortsStatuses(serial)
        for port in ports:
            port_id = port['portId']
            data[serial][port_id] = dict()
            data[serial][port_id]['orgId'] = orgId
            data[serial][port_id]['networkId'] = networkId
            data[serial][port_id]['name'] = name
            data[serial][port_id]['serial'] = serial
            for key, value in port.items():
                data[serial][port_id][key] = value

    # Create a dictionary based on the contents of 'data'. This method ensures
    # that all arrays are of equal length when we create the dataframe.
    df_data = dict()
    df_data['orgId'] = list()
    df_data['networkId'] = list()
    df_data['name'] = list()
    df_data['serial'] = list()
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


def meraki_get_switch_port_usages(api_key: str,
                                  db_path: str,
                                  networks: list,
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
    query = f'''SELECT distinct orgId, networkId, name, serial, portId
    FROM MERAKI_SWITCH_PORT_STATUSES
    WHERE {statement} and timestamp = "{timestamp}"
    '''

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
