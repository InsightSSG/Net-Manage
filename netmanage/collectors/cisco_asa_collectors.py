#!/usr/bin/env python3

import ansible_runner
import pandas as pd

from netmanage.parsers import cisco_asa_parsers as parser


def get_interface_ips(username: str,
                      password: str,
                      host_group: str,
                      play_path: str,
                      private_data_dir: str) -> pd.DataFrame:
    '''
    Gets the IP addresses assigned to interfaces on Cisco ASA devices.

    Parameters
    ----------
    username : str
        The username to login to devices
    password : str
        The password to login to devices
    host_group : str
        The inventory host group
    play_path : str
        The path to the playbooks directory
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the interfaces and IPs, subnet and network
        addresses related to each IP.
    '''
    cmd = 'show interface summary | include Interface|IP address'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the command
    playbook = f'{play_path}/cisco_asa_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.asa_parse_interface_ips(runner)


def inventory(username: str,
              password: str,
              host_group: str,
              play_path: str,
              private_data_dir: str) -> pd.DataFrame:
    '''
    Get the inventory for Cisco IOS and IOS-XE devices.

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

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the interfaces and IP addresses.
    '''
    cmd = 'show inventory'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the command
    playbook = f'{play_path}/cisco_ios_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.asa_parse_inventory(runner)
