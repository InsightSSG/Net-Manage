#!/usr/bin/env python3

import ansible_runner
import json
import pandas as pd
from netmanage.helpers import helpers as hp
from typing import Dict


def run_adhoc_command(username: str,
                      password: str,
                      host_group: str,
                      nm_path: str,
                      private_data_dir: str,
                      cmd: str,
                      cmd_is_xml: bool) -> Dict[str, dict]:
    '''
    Runs an ad-hoc command on the specified hosts using Ansible.

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
    private_data_dir : str
        The path to the Ansible private data directory.
    cmd : str
        The command to run.
    cmd_is_xml : bool
        Whether the command is formatted as XML.

    Returns
    -------
    dict
        A dictionary containing the command output, where the keys are the
        devices and the value is a dictionary containing all of the data
        within the event that contains the 'runner_on_ok' value.

    Notes
    -----
    Ansible-runner returns a generator containing each event that Ansible
    executed. In order to conserve memory, this function searches for
    events that contain the 'event' key with a value of
    'runner_on_ok'. That key does not mean that the task succeeded,
    it just indicates that it is the event that contains the results of the
    task.

    That logic should be revisited if a use-case arises that necessitates
    returning other events to whichever function that is calling this
    function.

    Examples
    --------
    >>> cmd = '<show><system><info></info></system></show>'
    >>> cmd_is_xml = True
    >>> response = run_adhoc_command(username,
                                     password,
                                     host_group,
                                     nm_path,
                                     private_data_dir,
                                     cmd,
                                     cmd_is_xml)
    >>> for key in response:
    >>>        assert isinstance(response[key]['event'], str)

    >>> cmd = 'show system software status'
    >>> cmd_is_xml = False
    >>> response = run_adhoc_command(username,
                                     password,
                                     host_group,
                                     nm_path,
                                     private_data_dir,
                                     cmd,
                                     cmd_is_xml)
    >>> for key in response:
    >>>        assert isinstance(response[key]['event'], str)
    '''
    extravars = {'user': username,
                 'password': password,
                 'host_group': host_group,
                 'cmd': cmd,
                 'cmd_is_xml': cmd_is_xml}

    playbook = f'{nm_path}/playbooks/palo_alto_run_adhoc_command.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    result = dict()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            device = event['event_data']['remote_addr']
            result[device] = event

    return result


def get_all_interfaces(username: str,
                       password: str,
                       host_group: str,
                       nm_path: str,
                       private_data_dir: str) -> pd.DataFrame:
    '''
    Gets all interfaces on Palo Altos.

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
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the logical interfaces.

    Examples
    --------
    >>> df = get_all_interfaces(username,
                                password,
                                host_group,
                                nm_path,
                                play_path,
                                private_data_dir)
    >>> df.columns.to_list()
    ['device',
    'name',
    'zone',
    'fwd',
    'vsys',
    'dyn-addr',
    'addr6',
    'tag',
    'ip',
    'id',
    'addr']
    '''
    cmd = 'show interface all'
    cmd_is_xml = False

    response = run_adhoc_command(username,
                                 password,
                                 host_group,
                                 nm_path,
                                 private_data_dir,
                                 cmd,
                                 cmd_is_xml)

    # Create a dictionary to store the formatted cmd output for each device.
    result = dict()

    # Parse 'response', adding the cmd output for each device to 'result'.
    for device, event in response.items():
        output = json.loads(event['event_data']['res']['stdout'])
        if output['response']['result']['ifnet'].get('entry'):
            output = output['response']['result']['ifnet']['entry']
            result[device] = output
        else:
            result[device] = dict()

    # Use the data in 'result' to populate 'df_data', which will be used to
    # create the dataframe.
    df_data = dict()
    df_data['device'] = list()
    for device in result:
        for item in result[device]:
            df_data['device'].append(device)
            for key, value in item.items():
                if not df_data.get(key):
                    df_data[key] = list()
                df_data[key].append(value)

    # Create the dataframe.
    df = pd.DataFrame.from_dict(df_data).astype(str)

    return df


def get_arp_table(username: str,
                  password: str,
                  host_group: str,
                  nm_path: str,
                  private_data_dir: str,
                  interface: str = '') -> pd.DataFrame:
    '''
    Parses the Palo Alto ARP table and adds vendor OUIs.

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
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the ARP table and vendor OUIs.

    Other Parameters
    ----------------
    interface : str, optional
        The interface for which to return the ARP table. The default is to
        return the ARP table for all interfaces.

    Examples
    --------
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
    '''
    if interface:
        cmd = f"<show><arp><entry name='{interface}'/></arp></show>"
    else:
        cmd = "<show><arp><entry name='all'/></arp></show>"

    response = run_adhoc_command(username,
                                 password,
                                 host_group,
                                 nm_path,
                                 private_data_dir,
                                 cmd,
                                 True)

    # Create a dictionary to store the data for 'df'
    df_data = dict()
    df_data['device'] = list()

    # Populate 'df_data' from 'result'
    for device in response:
        output = json.loads(response[device]['event_data']['res']['stdout'])
        # An 'error' key indicates the interface does not exist.
        if not output['response']['result'].get('error'):
            if output['response']['result'].get('entries'):
                arp_table = output['response']['result']['entries']['entry']
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


def get_interface_ips(username: str,
                      password: str,
                      host_group: str,
                      nm_path: str,
                      private_data_dir: str) -> pd.DataFrame:
    '''Gets IP addresses on Palo Alto firewall interfaces.

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
    private_data_dir : str
        The path to the Ansible private data directory.

    Returns
    -------
    df : Pandas Dataframe
        A dataframe containing the IP addresses.

    Examples
    --------
    >>> df = get_ip_addresses(username,
                              password,
                              db_path,
                              host_group,
                              nm_path,
                              play_path,
                              private_data_dir,
                              timestamp)
    >>> df.columns.to_list()
    ['device',
    'name',
    'zone',
    'fwd',
    'vsys',
    'dyn-addr',
    'addr6',
    'tag',
    'ip',
    'id',
    'addr']
    '''
    # TODO: Optimize this function by setting 'get_all_interfaces' as a
    #       dependency. That way the same command does not need to be
    #       run twice (potentially) for two different collectors.
    df = get_all_interfaces(username,
                            password,
                            host_group,
                            nm_path,
                            private_data_dir)

    # Filter out interfaces that do not have an IP address.
    df = df[df['ip'] != 'N/A']

    # Add the subnets, network IPs, and broadcast IPs.
    addresses = df['ip'].to_list()
    result = hp.generate_subnet_details(addresses)
    df['subnet'] = result['subnet']
    df['network_ip'] = result['network_ip']
    df['broadcast_ip'] = result['broadcast_ip']

    return df


def get_logical_interfaces(username: str,
                           password: str,
                           host_group: str,
                           nm_path: str,
                           private_data_dir: str) -> pd.DataFrame:
    '''
    Gets the logical interfaces on Palo Altos.

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
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the logical interfaces.

    Examples
    --------
    >>> df = get_logical_interfaces(username,
                                    password,
                                    host_group,
                                    nm_path,
                                    play_path,
                                    private_data_dir)
    >>> df.columns.to_list()
    ['device',
    'name',
    'zone',
    'fwd',
    'vsys',
    'dyn-addr',
    'addr6',
    'tag',
    'ip',
    'id',
    'addr']
    '''
    cmd = 'show interface logical'
    cmd_is_xml = False

    response = run_adhoc_command(username,
                                 password,
                                 host_group,
                                 nm_path,
                                 private_data_dir,
                                 cmd,
                                 cmd_is_xml)

    # Create a dictionary to store the formatted cmd output for each device.
    result = dict()

    # Parse 'response', adding the cmd output for each device to 'result'.
    for device, event in response.items():
        output = json.loads(event['event_data']['res']['stdout'])
        if output['response']['result']['ifnet'].get('entry'):
            output = output['response']['result']['ifnet']['entry']
            result[device] = output
        else:
            result[device] = dict()

    # Use the data in 'result' to populate 'df_data', which will be used to
    # create the dataframe.
    df_data = dict()
    df_data['device'] = list()
    for device in result:
        for item in result[device]:
            df_data['device'].append(device)
            for key, value in item.items():
                if not df_data.get(key):
                    df_data[key] = list()
                df_data[key].append(value)

    # Create the dataframe.
    df = pd.DataFrame.from_dict(df_data).astype(str)

    return df


def get_physical_interfaces(username: str,
                            password: str,
                            host_group: str,
                            nm_path: str,
                            private_data_dir: str) -> pd.DataFrame:
    '''
    Gets the physical interfaces on Palo Altos.

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
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the physical interfaces.

    Examples
    --------
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
    '''
    cmd = 'show interface hardware'
    cmd_is_xml = False
    response = run_adhoc_command(username,
                                 password,
                                 host_group,
                                 nm_path,
                                 private_data_dir,
                                 cmd,
                                 cmd_is_xml)

    # Create a dictionary to store the formatted cmd output for each device.
    result = dict()

    # Parse 'response', adding the cmd output for each device to 'result'.
    for device, event in response.items():
        event_data = event['event_data']
        output = event_data['res']['stdout']
        output = json.loads(output)
        if output['response']['result']['hw'].get('entry'):
            output = output['response']['result']['hw']['entry']
            result[device] = output
        else:  # Just in case no results are returned for some reason.
            result[device] = dict()

    # Use the data in 'result' to populate 'df_data', which will be used to
    # create the dataframe.
    df_data = dict()
    df_data['device'] = list()
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


def get_security_rules(username: str,
                       password: str,
                       host_group: str,
                       play_path: str,
                       private_data_dir: str,
                       device_group: str = 'shared') -> pd.DataFrame:
    '''
    Get a list of all security rules from a Palo Alto firewall.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    device_group : str, optional
        The device group to query. Defaults to 'shared'.

    Returns
    -------
    df_rules : pd.DataFrame
        A DataFrame containing the security rules.
    '''
    extravars = {'user': username,
                 'password': password,
                 'device_group': device_group,
                 'host_group': host_group}

    playbook = f'{play_path}/palo_alto_get_security_rules.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Create the 'df_data' dictionary. It will be used to create the dataframe
    df_data = dict()
    df_data['device'] = list()

    # Create a list to store the unformatted details for each rule
    rules = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']
            output = event_data['res']['gathered']

            for item in output:
                item['device'] = device
                rules.append(item)
                for key in item:
                    if not df_data.get(key):
                        df_data[key] = list()

    # Iterate over the rule details, using the keys in dict_keys to create the
    # 'df_data' dictionary, which will be used to create the dataframe
    for item in rules:
        for key in df_data:
            # If a key in a rule has a value that is a list, then convert it to
            # a string by joining it with '|' as a delimiter. We do not want to
            # use commas a delimiter, since that can cause issues when
            # exporting the data to CSV files.
            if isinstance(item.get(key), list):
                # Some keys have a value that is a list, with commas inside the
                # list items. For example, source_user might look like this:
                # ['cn=name,ou=firewall,ou=groups,dc=dcname,dc=local']. That
                # creates an issue when exporting to a CSV file. Therefore,
                # the commas inside list items will be replaced with a space
                # before joining the list.
                _list = item.get(key)
                _list = [_.replace(',', ' ') for _ in _list]

                # Join the list using '|' as a delimiter
                df_data[key].append('|'.join(_list))
            # If the key's value is not a list, then convert it to a string
            # and append it to the key in 'df_data'
            else:
                df_data[key].append(str(item.get(key)))

    # Create the dataframe and return it
    df_rules = pd.DataFrame.from_dict(df_data)

    # Rename the 'destintaion_zone' column to 'destination_zone'
    df_rules.rename({'destintaion_zone': 'destination_zone'},
                    axis=1,
                    inplace=True)

    return df_rules