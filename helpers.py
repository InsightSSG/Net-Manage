#!/usr/bin/env python3

'''
A library of generic helper functions for dynamic runbooks.
'''

import ansible_runner
import os
import pandas as pd
from datetime import datetime as dt
from getpass import getpass
import yaml


def ansible_create_vars_df(test_dataframe, private_data_dir='.'):
    '''
    This function is created to be used with the maintenance tests notebooks.
    It reads all of the host groups from the 'df_test', gets the ansible
    variables for each group from the host file, creates a dataframe containing
    the variables, then returns it.

    Args:
        test_dataframe (DataFrame): The dataframe containing the tests.
        private_data_dir (str):     The path to the Ansible private_data_dir.
                                    It is the path that the 'inventory' folder
                                    is in. The default is the current folder.

    Returns:
        df_vars (DataFrame):        A dataframe containing the group variables
    '''
    host_groups = list()
    for c in test_dataframe.columns.to_list():
        for item in test_dataframe[c].to_list():
            if item not in host_groups and item != 'nan':
                host_groups.append(item)

    host_vars = dict()

    for g in host_groups:
        group_vars = ansible_get_host_variables(g, private_data_dir)
        host_vars[g] = group_vars

    # Create a dictionary to store the variable data for each group
    df_data = dict()
    df_data['host_group'] = list()

    # Iterate through the keys for each group in 'host_vars', adding it as a
    # key to 'df_data'
    for key, value in host_vars.items():
        for k in value:
            if k != 'ansible_user' and k != 'ansible_password':
                df_data[k] = list()

    # Iterate through 'host_vars', populating 'df_data'
    for key, value in host_vars.items():
        df_data['host_group'].append(key)
        for item in df_data:
            if item != 'host_group':
                result = value.get(item)
                df_data[item].append(result)

    df_vars = pd.DataFrame.from_dict(df_data)

    return df_vars


def ansible_get_hostgroup():
    '''
    Gets the Ansible hostgroup

    Args:
        None

    Returns:
        hostgroup (str): The Ansible hostgroup
    '''
    host_group = input('Enter the name of the host group in the hosts file: ')
    return host_group


def ansible_get_host_variables(host_group, private_data_dir):
    '''
    Gets the variables for a host or host group in the hosts file.

    Args:
        host_group (str):       The name of the host group
        private_data_dir (str): The path to the Ansible private_data_dir. This
                                is the path that the 'inventory' folder is in.
                                The default is the current folder.

    Returns:
        group_vars (dict):      The host group variables
    '''
    # Read the contents of the playbook into a dictionary
    with open(f'{private_data_dir}/inventory/hosts') as f:
        hosts = yaml.load(f, Loader=yaml.FullLoader)

    group_vars = hosts[host_group]['vars']

    return group_vars


def ansible_get_hostgroup_devices(hostgroup, host_files, quiet=True):
    '''
    Gets the devices inside an Ansible inventory hostgroup.
    Args:
        hostgroup (str):   The Ansible hostgroup
        host_files (list): The path to one or more Ansible host files
                           (I.e., ['inventory/hosts'])
        quiet (bool):      Whether to output the entire graph.
    Returns:
        devices (list):  A list of devices in the hostgroup
    '''
    graph = ansible_runner.interface.get_inventory('graph',
                                                   host_files,
                                                   quiet=True)
    graph = str(graph)
    for item in graph.split('@'):
        if hostgroup in item:
            item = item.split(':')[-1]
            item = item.split('|--')[1:-1]
            devices = [i.split('\\')[0] for i in item]
            break
    return devices


def get_creds():
    '''
    Gets the username and password to login to devices with.

    Args:
        None

    Returns:
        username (str): The username
        password (str): The password
    '''
    username = get_username()
    password = get_password()
    return username, password


def get_hostgroup():
    '''
    Gets the Ansible hostgroup

    Args:
        None

    Returns:
        hostgroup (str): The Ansible hostgroup
    '''
    host_group = input('Enter the name of the host group in the hosts file: ')
    return host_group


def get_username():
    '''
    Gets the username to login to a device with

    Args:
        None

    Returns:
        username (str): The username
    '''
    username = input('Enter the username to login to the devices with: ')

    return username


def get_password():
    '''
    Gets the password to login to a device with

    Args:
        None

    Returns:
        password (str): The password
    '''
    # Get the user's password and have them type it twice for verification
    pass1 = str()
    pass2 = None
    while pass1 != pass2:
        pass1 = getpass('Enter your password: ')
        pass2 = getpass('Confirm your password: ')
        if pass1 != pass2:
            print('Error: Passwords do not match.')
    password = pass1

    return password


def map_tests_to_os(private_data_dir,
                    nm_path,
                    test_file):
    '''
    Maps the tests specified in 'test_file' to the Ansible OS.

    Args:
        private_data_dir (str):     The Ansible private data directory
        nm_path (str):              The path to the Net-Manage repository
        test_file (str):            The path to the file containing tests

    Returns:
        df_collectors (DataFrame):       A DataFrame created from test_file
        df_vars (DataFrame):        A DataFrame mapping the tests to Ansible OS
        nm_path (str):              The path to the Net-Manage repository
        play_path (str):            The path to the Ansible playbooks
        test_map (dict):            A pre-defined dict for storing test results
    '''
    nm_path = os.path.expanduser(nm_path)
    play_path = f'{nm_path}/playbooks'
    os.chdir(nm_path)

    # Set the Ansible private data directory
    private_data_dir = os.path.expanduser(private_data_dir)

    # Set the path to the inventory/hosts file
    inv_path = f'{private_data_dir}/inventory/hosts'

    # Create a dictionary mapping ansible_network_os to the appropriate
    # playbook. This dictionary is statically defined in case there is a need
    # to specify a non-standard playbook for a future test. This dictionary
    # will also be used to store the results of each test.

    # TODO: Write results directly to a database. This method is not Pythonic,
    # is hard to modify, and forces all test results to be loaded into memory.

    # test_map = dict()

    # test_map['pre_post_checks'] = dict()
    # test_map['pre_post_checks']['cisco.ios.ios'] = dict()
    # test_map['pre_post_checks']['cisco.nxos.nxos'] = dict()
    # test_map['pre_post_checks']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_pre_post_checks.yml'

    # test_map['find_uplink_by_ip'] = dict()
    # test_map['find_uplink_by_ip']['cisco.ios.ios'] = dict()
    # test_map['find_uplink_by_ip']['cisco.ios.ios']['playbook'] = \
    #     'cisco_ios_run_commands.yml'
    # test_map['find_uplink_by_ip']['cisco.nxos.nxos'] = dict()
    # test_map['find_uplink_by_ip']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'

    # test_map['port_channel_data'] = dict()
    # test_map['port_channel_data']['cisco.ios.ios'] = dict()
    # test_map['port_channel_data']['cisco.ios.ios']['playbook'] = \
    #     'cisco_ios_run_commands.yml'
    # test_map['port_channel_data']['cisco.nxos.nxos'] = dict()
    # test_map['port_channel_data']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'

    # test_map['vrfs'] = dict()
    # test_map['vrfs']['cisco.ios.ios'] = dict()
    # test_map['vrfs']['cisco.ios.ios']['playbook'] = \
    #     'cisco_ios_run_commands.yml'
    # test_map['vrfs']['cisco.nxos.nxos'] = dict()
    # test_map['vrfs']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'

    # test_map['interface_description'] = dict()
    # test_map['interface_description']['cisco.ios.ios'] = dict()
    # test_map['interface_description']['cisco.ios.ios']['playbook'] = \
    #     'cisco_ios_run_commands.yml'
    # test_map['interface_description']['cisco.nxos.nxos'] = dict()
    # test_map['interface_description']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'

    # test_map['interface_status'] = dict()
    # test_map['interface_status']['cisco.ios.ios'] = dict()
    # test_map['interface_status']['cisco.ios.ios']['playbook'] = \
    #     'cisco_ios_run_commands.yml'
    # test_map['interface_status']['cisco.nxos.nxos'] = dict()
    # test_map['interface_status']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'

    # test_map['trunk_status'] = dict()
    # test_map['trunk_status']['cisco.ios.ios'] = dict()
    # test_map['trunk_status']['cisco.ios.ios']['playbook'] = \
    #     'cisco_ios_run_commands.yml'
    # test_map['trunk_status']['cisco.nxos.nxos'] = dict()
    # test_map['trunk_status']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'

    # test_map['vpc_state'] = dict()
    # test_map['vpc_state']['cisco.ios.ios'] = dict()
    # test_map['vpc_state']['cisco.nxos.nxos'] = dict()
    # test_map['vpc_state']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'

    # test_map['vpc_status'] = dict()
    # test_map['vpc_status']['cisco.ios.ios'] = dict()
    # test_map['vpc_status']['cisco.nxos.nxos'] = dict()
    # test_map['vpc_status']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'

    # test_map['vlan_database'] = dict()
    # test_map['vlan_database']['cisco.ios.ios'] = dict()
    # test_map['vlan_database']['cisco.ios.ios']['playbook'] = \
    #     'cisco_ios_run_commands.yml'
    # test_map['vlan_database']['cisco.nxos.nxos'] = dict()
    # test_map['vlan_database']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'

    # test_map['arp_table'] = dict()
    # test_map['arp_table']['cisco.ios.ios'] = dict()
    # test_map['arp_table']['cisco.ios.ios']['playbook'] = \
    #     'cisco_ios_run_commands.yml'
    # test_map['arp_table']['cisco.nxos.nxos'] = dict()
    # test_map['arp_table']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'
    # test_map['arp_table']['paloaltonetworks.panos'] = dict()
    # test_map['arp_table']['paloaltonetworks.panos']['playbook'] = \
    #     'palo_alto_run_command.yml'

    # test_map['cam_table'] = dict()
    # test_map['cam_table']['cisco.ios.ios'] = dict()
    # test_map['cam_table']['cisco.ios.ios']['playbook'] = \
    #     'cisco_ios_run_commands.yml'
    # test_map['cam_table']['cisco.nxos.nxos'] = dict()
    # test_map['cam_table']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'

    # test_map['routes'] = dict()
    # test_map['routes']['cisco.ios.ios'] = dict()
    # test_map['routes']['cisco.ios.ios']['playbook'] = \
    #     'cisco_ios_run_commands.yml'
    # test_map['routes']['cisco.nxos.nxos'] = dict()
    # test_map['routes']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'

    # test_map['route_neighbors'] = dict()
    # test_map['route_neighbors']['cisco.ios.ios'] = dict()
    # test_map['route_neighbors']['cisco.ios.ios']['playbook'] = \
    #     'cisco_ios_run_commands.yml'
    # test_map['route_neighbors']['cisco.nxos.nxos'] = dict()
    # test_map['route_neighbors']['cisco.nxos.nxos']['playbook'] = \
    #     'cisco_nxos_run_commands.yml'

    # Read the spreadsheet containing tests and save the tests to a dataframe
    df_collectors = pd.read_excel(test_file, sheet_name='tests')

    # df_collectors = df_collectors.T  # Transpose rows and columns
    df_collectors = df_collectors.dropna(axis=1, how='all')
    df_collectors = df_collectors.astype(str)

    # Create a dataframe containing the variables for host groups
    df_vars = ansible_create_vars_df(df_collectors, private_data_dir)

    # Get the devices in each hostgroup and add them to df_vars as a new column
    hostgroup_devices = list()
    for idx, row in df_vars.iterrows():
        hostgroup = row['host_group']
        devices = ansible_get_hostgroup_devices(hostgroup, [inv_path])
        devices = ','.join(devices)
        hostgroup_devices.append(devices)
    df_vars['devices'] = hostgroup_devices

    return df_collectors, df_vars, nm_path, play_path


def set_filepath(filepath):
    '''
    Creates a filename with the date and time added to a path the user
    provides. The function assumes the last "." in a filename is the extension.

    Args:
        filepath (str):     The base filepath. Do not include the date; that
                            will be added dynamically at runtime.

    Returns:
        filepath (str):     The full path to the modified filename.
    '''
    # Convert '~' to the user's home folder
    if '~' in filepath:
        filepath = filepath.replace('~', os.path.expanduser('~'))
    # Set the prefix in YYYY-MM-DD_HHmm format
    prefix = dt.now().strftime("%Y-%m-%d_%H%M")
    # Extract the base path to the filename
    filepath = filepath.split('/')
    filename = filepath[-1]
    if len(filepath) > 2:
        filepath = '/'.join(filepath[:-1])
    else:
        filepath = filepath[0]
    # Extract the filename and extension from 'filepath'
    filename = filename.split('.')
    extension = filename[-1]
    if len(filename) > 2:
        filename = '.'.join(filename[:-1])
    else:
        filename = filename[0]
    # Return the modified filename
    filepath = f'{filepath}/{prefix}_{filename}.{extension}'
    return filepath


def suppress_extravars(extravars):
    '''
    ansible_runner.run stores extravars to a file named 'extravars' then saves
    it to the local drive. The file is unencrypted, so any sensitive data, like
    usernames and password, are stored in plain text.

    People have complained about this for years. Finally, starting in version
    2.x, the devs added the 'suppress_env_files' arg. This keeps extravars from
    being stored locally.

    The sole purpose of this function is to ensure that legacy Ansible-Runner
    commands add that argument. *All ansible_runner.run args should be passed
    to this function, no exceptions.*




    
    If they do not use extravars, then just pass an empty dict.
    This will ensure the functions are secure if someone adds extravars to them
    later.

    Args:
        extravars (dict):       A dictionary containing the extravars. If your
                                function does not use it, then pass an empty
                                dict instead.

    Returns: extravars (dict):  'extravars' with the 'suppress_env_files' key.
    '''
    # if not extravars.get('')


def get_net_manage_path():
    '''
    Set the absolute path to the Net-Manage repository.

    Args:
        None

    Returns:
        nm_path (str):  The absolute path to the Net-Manage repository.
    '''
    nm_path = input("Enter the absolute path to the Net-Manage repository: ")
    nm_path = os.path.expanduser(nm_path)
    return nm_path


def get_tests_file():
    '''
    Set the absolute path to the Net-Manage repository.

    Args:
        None

    Returns:
        t)path (str):   The absolute path to the file containing tests to run.
    '''
    t_file = input("Enter the absolute path to the Net-Manage repository: ")
    t_file = os.path.expanduser(t_file)
    return t_file
