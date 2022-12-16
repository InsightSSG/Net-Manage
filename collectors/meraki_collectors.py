#!/usr/bin/env python3

'''
Define Meraki collectors.
'''

import meraki
import pandas as pd
import sqlite3 as sl


def helpers(cols=str(),
            db_path=str(),
            network=str(),
            org=str(),
            orgs=str(),
            table=str()
            ):
    '''

    '''
    def meraki_check_api_enablement(db_path, org):
        '''
        Queries the database to find if API access is enabled.

        Args:
            db_path (str):  The path to the database to store results
            org (str):      The organization to check API access for.
        '''
        enabled = False

        query = ['SELECT timestamp, api from MERAKI_GET_ORGANIZATIONS',
                 f'WHERE org_id = {org}',
                 'ORDER BY timestamp DESC',
                 'limit 1']
        query = ' '.join(query)

        con = sl.connect(db_path)
        result = pd.read_sql(query, con)

        con.close()

        if result['api'].to_list()[0] == 'True':
            enabled = True

        return enabled

    def map_meraki_network_to_organization(network,
                                           db_path,
                                           col='org_id',
                                           table='MERAKI_GET_ORG_NETWORKS'):
        '''
        Args:
            db_path (str):  The path to the database to query
            network (str):  The network ID to query
            col_name (str): (Optional) The column name to query. Defaults to
                            'org_id'
            table (str):    (Optional) The table name to query. Defaults to
                            'meraki_get_org_networks'

        Returns:
            org_id (str):   The organization ID
        '''
        con = sl.connect(db_path)
        cur = con.cursor()
        cur.execute(f'SELECT {col} FROM {table} WHERE network_id="{network}"')
        org_id = cur.fetchone()[0]
        cur.close()

        return org_id

    def parse_meraki_organizations(db_path, orgs=list(), table=str()):
        '''
        Parses a list of organizations that are passed to certain Meraki
        collectors.

        Args:
            db_path (str):          The path to the database to store results
            orgs (list):            One or more organization IDs. If none are
                                    specified, then the networks for all orgs
                                    will be returned.
            table (str):            The database table to query

        Returns:
            organizations (list):   A list of organizations
        '''
        con = sl.connect(db_path)
        organizations = list()
        if orgs:
            for org in orgs:
                df_orgs = pd.read_sql(f'select distinct org_id from {table} \
                    where org_id = "{org}"', con)
                organizations.append(df_orgs['org_id'].to_list().pop())
        else:
            df_orgs = pd.read_sql(f'select distinct org_id from {table}', con)
            for org in df_orgs['org_id'].to_list():
                organizations.append(org)
        con.close()

        return organizations


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
    organizations = helpers.parse_meraki_organizations(db_path, orgs, table)

    # Initialize Meraki dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.organizations

    # This list will contain all of the devices for each org. It will then be
    # used to create the dataframe. This method accounts for orgs that have
    # different device types, since not all device types contain the same keys.
    data = list()

    for org in organizations:
        # Check if API access is enabled for the org
        enabled = helpers.meraki_check_api_enablement(db_path, org)
        if enabled:
            devices = app.getOrganizationDevices(org, total_pages="all")
            for item in devices:
                data.append(item)

    df_data = dict()

    # Get all of the keys from devices in 'data', and add them as a key to
    # 'df_data'. The value of the key in 'df_data' will be a list.
    for item in data:
        for key in item:
            if not df_data.get(key):
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
                                   networks=list(),
                                   orgs=list(),
                                   total_pages='all'):
    '''
    Gets the device statuses for all organizations the user's API key has
    access to.

    Args:
        api_key (str):              The user's API key
        db_path (str):              The path to the database to store results
        networks (list):            (Optional) One or more network IDs.
        orgs (list):                (Optional) One or more organization IDs. If
                                    none are specified, then the device
                                    statuses for all orgs will be returned.
        total_pages (int):          (Optional) The number of pages to retrieve.
                                    Defaults to 'all'. Note that value
                                    besides 'all' must be an integer.

    Returns:
        df_statuses (DataFrame):    The device statuses for the organizations
    '''
    # Initialize Meraki dashboard
    dashboard = meraki.DashboardAPI(api_key=api_key, suppress_logging=True)
    app = dashboard.organizations

    # If the user did not specify any organization IDs, then get them by
    # querying the database
    if not orgs:
        table = 'meraki_get_organizations'
        orgs = helpers.parse_meraki_organizations(db_path, orgs, table)

    # Create a dictionary to map organization IDs to network IDs
    mapper = dict()
    for org in orgs:
        if not mapper.get(org):
            mapper[org] = list()

    # If the user provided any networks, add them to 'mapper'
    if networks:
        for net_id in networks:
            # Get the organization ID for the network ID
            org_id = helpers.map_meraki_network_to_organization(net_id,
                                                                db_path)
            # Add the network ID to 'mapper'. If the user provided lists of
            # organization IDs and network IDs, and the network ID belongs to
            # one of the organization IDs, then the organization ID will be
            # filtered to only include network IDs from the 'networks'
            # parameter. This is designed behavior.
            if not mapper.get(org_id):
                mapper[org_id] = list()
            mapper[org_id].append(net_id)

    # Create a list to store raw results from the API (the results are
    # returned as a list of dictionaries--one dictionary per device)
    data = list()

    # If the user specified a specific number of pages to return, then convert
    # the parameter to an integer
    tp = total_pages
    if tp != 'all':
        tp = int(tp)

    # Query the API for the device statuses and add them to 'data')
    for key, value in mapper.items():
        # Check if API access is enabled for the org
        enabled = helpers.meraki_check_api_enablement(db_path, key)
        if enabled:
            if value:
                statuses = app.getOrganizationDevicesStatuses(key,
                                                              networkIds=value,
                                                              total_pages=tp)
            else:
                statuses = app.getOrganizationDevicesStatuses(key,
                                                              total_pages=tp)
            for item in statuses:
                item['orgId'] = key  # Add the orgId to each device status
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

    return df_statuses


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
        # Get the organizations (collected by 'meraki_get_orgs') from the database
        table = 'meraki_get_organizations'
        organizations = helpers.parse_meraki_organizations(db_path, orgs, table)
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
            enabled = helpers.meraki_check_api_enablement(db_path, org)
        else:
            enabled = False
        if enabled or not use_db:
            networks = app.getOrganizationNetworks(org, total_pages="all")
            for item in networks:
                for key, value in item.items():
                    data.append(item)

    print(len(data))

    # Iterate over 'data', creating the keys for the DataFrame
    for item in data:
        for key in item:
            if not df_data.get(key):
                df_data[key] = list()

    # Iterate over 'data', adding the networks to 'df_data'
    for item in data:
        for key in df_data:
            df_data[key].append(item.get(key))
    #             network_id = item['id']
    #             name = item['name']
    #             product_types = '|'.join(item['productTypes'])
    #             network_tz = item['timeZone']
    #             tags = '|'.join(item['tags'])
    #             enrollment_str = item['enrollmentString']
    #             url = item['url']
    #             notes = item['notes']
    #             template_bound = item['isBoundToConfigTemplate']

    #             df_data.append([org,
    #                             network_id,
    #                             name,
    #                             product_types,
    #                             network_tz,
    #                             tags,
    #                             enrollment_str,
    #                             url,
    #                             notes,
    #                             template_bound])

    # # Create the dataframe and return it
    # cols = ['org_id',
    #         'network_id',
    #         'name',
    #         'product_types',
    #         'network_tz',
    #         'tags',
    #         'enrollment_str',
    #         'url',
    #         'notes',
    #         'template_bound']
    # df_networks = pd.DataFrame(data=df_data, columns=cols)
    df_networks = pd.DataFrame.from_dict(df_data)

    return df_networks
