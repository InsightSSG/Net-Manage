#!/usr/bin/env python3

'''
A collection of collectors for the NIOS (Infoblox) operating system.
'''

import ipaddress as ip
import pandas as pd
# import requests

from helpers import helpers as hp

from infoblox_client import connector


def create_connector(host, username, password, validate_certs=True):
    """Creates the connector to use to connect to the Infoblox grid.

    Parameters
    ----------
    host : str
        The host's IP address or FQDN
    username : str
        The user's username.
    password : str
        The user's password.
    validate_certs: bool
        Whether to validate certificates. Defaults to 'True'

    Notes
    ----------
    If 'validate_certs=False', then 'silent_ssl_warnings' will be set to
    'True'.

    Returns
    ----------
    nb : infoblox_client.connector.Connector
        The Infoblox Connector object.

    Examples
    ----------
    >>> conn = create_connector(host, username, password)
    >>> print(type(conn))
    <class 'infoblox_client.connector.Connector'>
    """
    opts = {'host': host,
            'username': username,
            'password': password,
            'ssl_verify': validate_certs}
    if not validate_certs:
        opts['silent_ssl_warnings'] = True
    conn = connector.Connector(opts)
    return conn


def get_network_containers(host,
                           username,
                           password,
                           paging=True,
                           validate_certs=True):
    '''
    Gets all network containers from an Infoblox API.

    Args:
        host (str):                 The host's IP address or FQDN
        username (str):             The user's username
        password (str):             The user's password
        paging (bool):              Whether to perform paging. Defaults to True
        validate_certs (bool):      Whether to validate SSL certs


    Returns:
        df_containers (DataFrame):  A DataFrame containing the network
                                    network containers
    '''
    # Create the connector to use to connect to the API
    conn = create_connector(host, username, password)

    # Get the network containers
    response = conn.get_object('networkcontainer', paging=paging)

    # Create the dictionary to store the data needed to create the DataFrame,
    # then interate over 'response' to create the keys
    df_data = dict()
    for item in response:
        for key, value in item.items():
            df_data[key] = list()

    # Populate 'df_data'
    for item in response:
        for key in df_data:
            df_data[key].append(item.get(key))

    df_containers = pd.DataFrame.from_dict(df_data)

    return df_containers


def get_networks_parent_containers(db_path):
    '''
    Gets the parent containers for all networks in an Infoblox Grid.

    Args:
        db_path (str):      The path to the database which contains the
                            'GET_NETWORKS' and 'GET_NETWORK_CONTAINER' tables
        networks (list):    A list of one or more networks

    Returns:
        df_parents (obj):   A dataframe containing the network container for
                            each network.
    '''
    # Connect to the database
    con = hp.connect_to_db(db_path)

    # Get the last timestamp for each network in the 'GET_NETWORKS' table.
    # (This function is always run after the 'get_networks' and
    # 'get_network_containers' collectors, so we only need the timestamp for
    # one of the tables.)
    table = 'INFOBLOX_GET_NETWORKS'
    query = f'SELECT DISTINCT timestamp FROM {table}'
    last_ts = pd.read_sql(query, con)['timestamp'].to_list()[-1]

    # Get all the networks
    query = ['SELECT network, network_view',
             f'FROM {table}',
             f'WHERE timestamp = "{last_ts}"']
    query = ' '.join(query)
    df_networks = pd.read_sql(query, con)

    # Get all the network containers
    table = 'INFOBLOX_GET_NETWORK_CONTAINERS'
    query = ['SELECT network, network_view',
             f'FROM {table}',
             f'WHERE timestamp = "{last_ts}"']
    query = ' '.join(query)
    df_containers = pd.read_sql(query, con)

    # Create a list of distinct network views
    views = df_containers['network_view'].to_list()
    views = [*set(views)]

    # Create a dictionary of the containers, where each key is a unique view,
    # and the value is a list of network containers, sorted from smallest to
    # largest
    containers = dict()
    for view in views:
        u_containers = df_containers.loc[df_containers['network_view'] == view]
        u_containers = u_containers['network'].to_list()
        u_containers = [ip.ip_network(_, strict=False) for _ in u_containers]
        u_containers = sorted(u_containers, key=ip.ip_network, reverse=True)
        containers[view] = u_containers

    # Iterate over the networks, mapping each network to its parent container
    # for its view. Infoblox supports nested containers, so the loop breaks
    # when the first valid parent is reached. (That is why 'u_containers' for
    # each view is sorted from the smallest to largest container.)
    parent_containers = list()
    not_found = list()
    for idx, row in df_networks.iterrows():
        found = False
        network = ip.ip_network(row['network'], strict=False)
        view = row['network_view']
        for container in containers[view]:
            if network.subnet_of(container):
                parent_containers.append(str(container))
                found = True
                break
        if not found:
            parent_containers.append('orphan')
            not_found.append(network)

    # Add the parent containers to 'df_networks'
    df_networks['network_container'] = parent_containers

    return df_networks


def get_networks(host,
                 username,
                 password,
                 paging=True,
                 validate_certs=True):
    '''
    Gets all network containers from an Infoblox API.

    Args:
        host (str):                 The host's IP address or FQDN
        username (str):             The user's username
        password (str):             The user's password
        paging (bool):              Whether to perform paging. Defaults to True
        validate_certs (bool):      Whether to validate SSL certs


    Returns:
        df_networks (DataFrame):    A DataFrame containing the network
                                    network containers
    '''
    # Create the connector to use to connect to the API
    conn = create_connector(host,
                            username,
                            password,
                            validate_certs=validate_certs)

    # Get the network containers
    response = conn.get_object('network', paging=paging)

    # Create the dictionary to store the data needed to create the DataFrame,
    # then interate over 'response' to create the keys
    df_data = dict()
    for item in response:
        for key, value in item.items():
            df_data[key] = list()

    # Populate 'df_data'
    for item in response:
        for key in df_data:
            df_data[key].append(item.get(key))

    df_networks = pd.DataFrame.from_dict(df_data)

    return df_networks


def get_vlan_ranges(host,
                    username,
                    password,
                    paging=True,
                    validate_certs=True):
    '''
    Gets all VLAN ranges from an Infoblox API.

    Args:
        host (str):                 The host's IP address or FQDN
        username (str):             The user's username
        password (str):             The user's password
        paging (bool):              Whether to perform paging. Defaults to True
    validate_certs: bool
        Where to validate certs. Defaults to True

    Returns:
        df (DataFrame):             A DataFrame containing the VLAN ranges
    '''
    # Create the connector to use to connect to the API
    conn = create_connector(host,
                            username,
                            password,
                            validate_certs=validate_certs)

    # Get the network containers
    response = conn.get_object('vlanrange', paging=paging)

    # Create the dictionary to store the data needed to create the DataFrame,
    # then interate over 'response' to create the keys
    df_data = dict()
    for item in response:
        for key in item:
            df_data[key] = list()

    # Populate 'df_data'
    for item in response:
        for key in df_data:
            df_data[key].append(item.get(key))

    df = pd.DataFrame.from_dict(df_data).astype('str')

    return df


def get_vlans(host,
              username,
              password,
              paging=True,
              validate_certs=True):
    '''
    Gets all VLAN from an Infoblox API.

    Args:
        host (str):                 The host's IP address or FQDN
        username (str):             The user's username
        password (str):             The user's password
        paging (bool):              Whether to perform paging. Defaults to True
        validate_certs (bool):      Whether to validate SSL certs


    Returns:
        df (DataFrame):             A DataFrame containing the VLANs
    '''
    # Create the connector to use to connect to the API
    conn = create_connector(host,
                            username,
                            password,
                            validate_certs=validate_certs)

    # Get the network containers
    response = conn.get_object('vlan', paging=paging)

    # Create the dictionary to store the data needed to create the DataFrame,
    # then interate over 'response' to create the keys
    df_data = dict()
    for item in response:
        for key in item:
            df_data[key] = list()

    # Populate 'df_data'
    for item in response:
        for key in df_data:
            df_data[key].append(item.get(key))

    df = pd.DataFrame.from_dict(df_data).astype('str')

    return df
