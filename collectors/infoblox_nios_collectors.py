#!/usr/bin/env python3

'''
A collection of collectors for the NIOS (Infoblox) operating system.
'''

import pandas as pd
# import requests

from infoblox_client import connector


def create_connector(host, username, password):
    '''
    Creates the connector to use to connect to the Infoblox grid.

    Args:
        host (str):     The host's IP address or FQDN
        username (str): The user's username
        password (str): The user's password

    Returns:
        conn (obj):     The connector
    '''
    opts = {'host': host, 'username': username, 'password': password}
    conn = connector.Connector(opts)
    return conn


def disable_ssl_cert_warning(validate_certs):
    '''
    Disables warnings for SSL cert validation, if the user has passed
    'validate_certs=False' to a function.

    # TODO: There does not seem to be a way to force cert verification on some
    #       of the infoblox-client objects. Until this is fixed (or we
    #       find a workaround), SSL cert validation warnings will be shown.
    #       That way the user will at least know if cert validation is
    #       disabled.

    Args:
        validate_certs (bool):  Whether to validate SSL certs

    Returns:
        None
    '''
    if not validate_certs:
        # requests.packages.urllib3.disable_warnings()
        pass


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
    # If the user has passed 'validate_certs=False', then disable SSL cert
    # warnings.
    disable_ssl_cert_warning(validate_certs)

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
    # If the user has passed 'validate_certs=False', then disable SSL cert
    # warnings.
    disable_ssl_cert_warning(validate_certs)

    # Create the connector to use to connect to the API
    conn = create_connector(host, username, password)

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
