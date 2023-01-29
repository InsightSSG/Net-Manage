#!/usr/bin/env python3

'''
Define Meraki collectors.
'''

import helpers as hp
import json
import meraki
import pandas as pd
import sqlite3 as sl


def meraki_get_network_clients(api_key,
                               networks,
                               macs=list(),
                               per_page=1000,
                               timespan=86400,
                               total_pages='all'):
    '''
    Gets the list of clients on a network.

    Args:
        api_key (str):          The user's API key
        db_path (str):          The path to the database to store results
        networks (list):        One or more network IDs.

    Returns:
        df_clients (DataFrame): The clients for the network(s)
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


def meraki_get_network_devices(api_key, db_path, networks=list(), orgs=list()):
    '''
    Gets the devices for all orgs that the user's API key has access to. This
    function uses the following logic:

    1. If a user passes a list of networks, the list of orgs is ignored.

    2. If a user passes a list of orgs but not a list of networks, the function
       will query all networks in the list of orgs that the user's API key has
       access to.

    3. If a user does not pass a list of networks or a list of orgs, the
       function will query all networks in all orgs the user's API key has
       access to.

    Args:
        api_key (str):          The user's API key
        db_path (str):          The path to the database to store results
        networks (list):        One or more network IDs.
        orgs (list):            One or more organization IDs. If none are
                                specified, then the devices for all orgs will
                                be returned

    Returns:
        df_devices (DataFrame): The device statuses for the network(s)
    '''
    # Initialize Meraki dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.networks

    # This list will contain all of the devices for each network. It will be
    # used to create the dataframe. This method accounts for networks that have
    # different device types, since not all device types contain the same keys.
    data = list()

    if not networks:
        df_networks = meraki_get_org_networks(api_key, db_path, orgs=orgs)
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


def meraki_get_network_device_statuses(db_path, networks):
    '''
    Gets the statuses of all devices in a network. There is not an API
    endpoint for this, so it leverages 'meraki_get_org_device_statuses'.

    Args:
        db_path (str):              The path to the database to store results
        networks (list):            One or more network IDs.

    Returns:
        df_statuses (DataFrame):    A dataframe containing the device statuses
    '''
    df_statuses = pd.DataFrame()

    con = sl.connect(db_path)

    for network in networks:
        query = f'''SELECT *
        FROM meraki_get_org_device_statuses
        WHERE networkId = "{network}"
        ORDER BY timestamp desc
        LIMIT 1
        '''
        result = pd.read_sql(query, con)
        df_statuses = pd.concat([df_statuses, result])

    con.close()

    # Delete the 'table_id' column, since it was pulled from the
    # 'meraki_get_org_device_statuses' table and will need to be recreated
    del df_statuses['table_id']

    return df_statuses


def meraki_get_organizations(api_key):
    '''
    Gets a list of organizations and their associated parameters that the
    user's API key has access to.

    Args:
        api_key (str):  The user's API key

    Returns:
        df_orgs (list): A dataframe containing a list of organizations the
                        user's API key has access to
    '''
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)

    # Get the organizations the user has access to and add them to a dataframe
    orgs = dashboard.organizations.getOrganizations()

    df_data = list()

    for item in orgs:
        df_data.append([item['id'],
                        item['name'],
                        item['url'],
                        item['api']['enabled'],
                        item['licensing']['model'],
                        item['cloud']['region']['name'],
                        '|'.join(item['management']['details'])]
                       )
    cols = ['org_id',
            'name',
            'url',
            'api',
            'licensing_model',
            'cloud_region',
            'management_details']

    df_orgs = pd.DataFrame(data=df_data, columns=cols).astype(str)

    return df_orgs


def meraki_get_org_devices(api_key, db_path, orgs=list()):
    '''
    Gets the devices for all orgs that the user's API key has access to.

    Args:
        api_key (str):          The user's API key
        db_path (str):          The path to the database to store results
        orgs (list):            One or more organization IDs. If none are
                                specified, then the devices for all orgs will
                                be returned

    Returns:
        df_devices (DataFrame): The device statuses for the organizations
    '''
    # Get the organizations (collected by 'meraki_get_orgs') from the database
    table = 'meraki_get_organizations'
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


def meraki_get_org_device_statuses(api_key,
                                   db_path,
                                   orgs=list(),
                                   total_pages='all'):
    '''
    Gets the device statuses for all organizations the user's API key has
    access to.

    Args:
        api_key (str):              The user's API key
        db_path (str):              The path to the database to store results
        orgs (list):                (Optional) One or more organization IDs. If
                                    none are specified, then the device
                                    statuses for all orgs will be returned.
        total_pages (int):          (Optional) The number of pages to retrieve.
                                    Defaults to 'all'. Note that value
                                    besides 'all' must be an integer.

    Returns:
        df_statuses (DataFrame):    The device statuses for the organizations
        idx_cols (list):            The column names to use for creating the
                                    SQL table index.
    '''
    # Initialize Meraki dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.organizations

    # If the user did not specify any organization IDs, then get them by
    # querying the database
    if not orgs:
        table = 'meraki_get_organizations'
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


def meraki_get_org_networks(api_key,
                            db_path=str(),
                            orgs=list(),
                            use_db=False):
    '''
    Gets the networks for one or more organizations.

    Args:
        api_key (str):              The user's API key
        db_path (str):              The path to the database to store results
        orgs (list):                A list of organization IDs to query. NOTE:
                                    The function assumes that the orgs are
                                    accessible with the user's API key. It will
                                    not do a separate check unless 'use_db' is
                                    set to True.
        use_db (bool):              Whether to use a database. Results will be
                                    stored in memory if this is set to False.

    Returns:
        df_networks (DataFrame):    The networks in one or more organizations
    '''
    if use_db:
        # Get the organizations (collected by 'meraki_get_orgs') from the
        # database
        table = 'meraki_get_organizations'
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


def meraki_get_switch_lldp_neighbors(db_path):
    '''
    Uses the data returned from the 'meraki_get_switch_port_statuses' collector
    to create a dataframe containing switch LLDP neighbors.

    Args:
        db_path (str):          The path to the database containing the
                                'meraki_get_switch_port_statuses' collector
                                output

    Returns:
        df_lldp (dataframe):    A dataframe containing the LLDP neighbors for
                                the switch(es)
    '''
    # Query the database to get the LLDP neighbors
    headers = ['orgId',
               'networkId',
               'name',
               'serial',
               'portId as local_port',
               'lldp']
    query = f'''SELECT {','.join(headers)}
    FROM MERAKI_GET_SWITCH_PORT_STATUSES
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


def meraki_get_switch_port_statuses(api_key, db_path, networks):
    '''
    Gets the port statuses and associated data (including errors and warnings)
    for all Meraki switches in the specified network(s).

    Args:
        api_key (str):          The user's API key
        db_path (str):          The path to the database to store results
        networks (list):        The networks in which to gather switch port
                                statuses.

    Returns:
        df_ports (DataFrame):   The port statuses
    '''
    # Query the database to get all switches in the network(s)
    statement = f'''networkId = "{'" or networkId = "'.join(networks)}"'''
    query = f'''SELECT distinct orgId, networkId, name, serial
    FROM MERAKI_GET_ORG_DEVICES
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

    # from pprint import pprint
    for item in data:
        device = data[item]
        for port in device:
            for key in df_data:
                df_data[key].append(device[port].get(key))

    df_ports = pd.DataFrame.from_dict(df_data)
    df_ports = df_ports.astype(str)

    return df_ports


def meraki_get_switch_port_usages(api_key, db_path, networks, timestamp):
    '''
    Gets switch port usage in total rate per second.

    Args:
        api_key (str):          The user's API key
        db_path (str):          The path to the database to store results
        networks (list):        The networks in which to gather switch port
                                statuses.
        timestamp (str):        The timestamp passed to run_collectors

    Returns:
        df_usage (DataFrame):   The port statuses
    '''
    # Query the database to get all switches in the network(s)
    statement = f'''networkId = "{'" or networkId = "'.join(networks)}"'''
    query = f'''SELECT distinct orgId, networkId, name, serial, portId
    FROM MERAKI_GET_SWITCH_PORT_STATUSES
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
