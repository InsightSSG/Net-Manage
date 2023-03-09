#!/usr/bin/env python3

import ansible_runner
import json
import pandas as pd
from helpers import helpers as hp


def run_adhoc_command(username,
                      password,
                      host_group,
                      nm_path,
                      private_data_dir,
                      cmd,
                      cmd_is_xml):
    """
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

    Notes
    ----------
    Ansible-runner returns a generator containing each event that Ansible
    executed. In order to conserve memory, this function searches for
    events that contain the 'event' key with a value of
    'runner_on_ok'. That key does not mean that the task succeeded,
    it just indicates that it is the event that contains the results of the
    task.

    That logic should be revisited if a use-case arises that necessitates
    returning other events to whichever function that is calling this
    function.

    Returns
    ----------
    result : dict
        A dictionary containing the command output, where the keys are the
        devices and the value is a dictionary containing all of the data
        within the event that contains the 'runner_on_ok' value (see notes
        above for more details).

    Examples
    ----------
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
    """
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


def get_arp_table(username,
                  password,
                  host_group,
                  nm_path,
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


def get_logical_interfaces(username,
                           password,
                           host_group,
                           nm_path,
                           private_data_dir):
    """Gets the logical interfaces on Palo Altos.

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
    ----------
    df : Pandas Dataframe
        A dataframe containing the logical interfaces.

    Examples
    ----------
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
    """
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
    df = pd.DataFrame.from_dict(df_data)

    return df


def get_physical_interfaces(username,
                            password,
                            host_group,
                            nm_path,
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
