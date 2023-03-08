#!/usr/bin/env python3

import pandas as pd
from connectors import palo_alto_connectors as pc
from helpers import helpers as hp


def get_arp_table(username,
                  password,
                  host_group,
                  nm_path,
                  play_path,
                  private_data_dir,
                  interface=str()):
    """Parses the Palo Alto ARP table and adds vendor OUIs.

    Parameters
    ----------
    username : str
        The user's username.
    password : str
        The user's password.
    host_group : str
        The name of the Ansible inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    play_path : str
        The path to the directory containing Ansible playbooks
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    ----------
    df : Pandas Dataframe
        A dataframe containing the ARP table and vendor OUIs.

    Other Parameters
    ----------
    interface: str
        The interface for which to return the ARP table. The default is to
        return the ARP table for all interfaces.

    Examples
    ----------
    >>> df = get_arp_table(username,
                           password,
                           host_group,
                           nm_path,
                           play_path,
                           private_data_dir)
    >>> print(df.columns.to_list())
    ['device', 'status', 'ip', 'mac', 'ttl', 'interface', 'port', 'vendor']

    >>> df = get_arp_table(username,
                           password,
                           host_group,
                           nm_path,
                           play_path,
                           private_data_dir,
                           interface=interface)
    >>> print(df.columns.to_list())
    ['device', 'status', 'ip', 'mac', 'ttl', 'interface', 'port', 'vendor']
    """
    result = pc.get_arp_table(username,
                              password,
                              host_group,
                              play_path,
                              private_data_dir,
                              interface=interface)

    # Create a dictionary to store the data for 'df'
    df_data = dict()
    df_data['device'] = list()

    # Populate 'df_data' from 'result'
    for device in result:
        arp_table = result[device]
        for item in arp_table:
            df_data['device'].append(device)
            for key, value in item.items():
                if not df_data.get(key):
                    df_data[key] = list()
                df_data[key].append(value)

    # Get the vendors for the MAC addresses
    df_vendors = hp.find_mac_vendors(df_data['mac'], nm_path)
    df_data['vendor'] = df_vendors['vendor'].to_list()

    # Create the dataframe
    df = pd.DataFrame.from_dict(df_data)

    return df


def get_physical_interfaces(username,
                            password,
                            host_group,
                            play_path,
                            private_data_dir):
    """Gets the physical interfaces on Palo Altos.

    Parameters
    ----------
    username : str
        The user's username.
    password : str
        The user's password.
    host_group : str
        The name of the Ansible inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    play_path : str
        The path to the directory containing Ansible playbooks
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    ----------
    df : Pandas Dataframe
        A dataframe containing the physical interfaces.

    Examples
    ----------
    >>> df = get_physical_interfaces(username,
                                     password,
                                     host_group,
                                     nm_path,
                                     play_path,
                                     private_data_dir)
    >>> df.columns.to_list()
    ['device',
    'name',
    'duplex',
    'type',
    'state',
    'st',
    'mac',
    'mode',
    'speed',
    'id']
    """
    result = pc.get_physical_interfaces(username,
                                        password,
                                        host_group,
                                        play_path,
                                        private_data_dir)

    # Create a dictionary to store the data for 'df'.
    df_data = dict()
    df_data['device'] = list()

    # Populate 'df_data' from 'result'.
    for device in result:
        interfaces = result[device]
        for item in interfaces:
            df_data['device'].append(device)
            for key, value in item.items():
                if key != 'ae_member':  # Exclude aggregation groups.
                    if not df_data.get(key):
                        df_data[key] = list()
                    df_data[key].append(value)

    # Create the dataframe.
    df = pd.DataFrame.from_dict(df_data)

    return df
