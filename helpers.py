#!/usr/bin/env python3

'''
A library of generic helper functions for dynamic runbooks.
'''

import ansible_runner
import os
import pandas as pd
import sqlite3 as sl
import sys
import yaml
from datetime import datetime as dt
from getpass import getpass


def ansible_create_collectors_df(hostgroups, collectors):
    '''
    Creates a dataframe where the index is the selected collectors and each row
    contains a comma-delimited string of selected hostgroups.

    Args:
        hostgroups (list):          A comma-delimited list of hostgroups.
        collectors (list):          One or more collectors, comma-delimited

    Returns:
        df_collectors (DataFrame):  A DataFrame created from test_file
    '''
    df_data = list()
    for c in collectors:
        df_data.append([c, ','.join(hostgroups)])
        df_collectors = pd.DataFrame(data=df_data, columns=['collector',
                                                            'hostgroups'])
    df_collectors = df_collectors.set_index('collector')

    return df_collectors


def ansible_create_vars_df(hostgroups, private_data_dir):
    '''
    This function is created to be used with the maintenance tests notebooks.
    It reads all of the host groups from the 'df_test', gets the ansible
    variables for each group from the host file, creates a dataframe containing
    the variables, then returns it.
    Args:
        hostgroups (list):      A list of hostgroups.
        private_data_dir (str): The path to the Ansible private_data_dir.
                                It is the path that the 'inventory' folder
                                is in. The default is the current folder.
    Returns:
        df_vars (DataFrame):    A dataframe containing the group variables
    '''
    host_vars = dict()

    for g in hostgroups:
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

    df_vars = df_vars.set_index('host_group')

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


def ansible_get_hostgroups(inventories, quiet=True):
    '''
    Gets the devices inside an Ansible inventory hostgroup.
    Args:
        inventories (list): The path to one or more Ansible host files
                            (I.e., ['inventory/hosts'])
        quiet (bool):       Whether to output the entire graph.
    Returns:
        devices (list):  A list of devices in the hostgroup
    '''
    graph = ansible_runner.interface.get_inventory('graph',
                                                   inventories,
                                                   quiet=True)
    graph = str(graph).strip("('")
    # graph = list(filter(None, graph))
    hostgroups = list()
    graph = list(filter(None, graph.split('@')))
    # TODO: Write a better parser
    for item in graph:
        hostgroup = item.split(':')[0]
        hostgroups.append(hostgroup)
    return hostgroups


def connect_to_db(db):
    '''
    Opens a connection to the sqlite database.

    Args:
        db (str):   Path to the database

    Returns:
        con (ob):   Connection to the database
    '''
    try:
        con = sl.connect(db)
    except Exception as e:
        if str(e) == 'unable to open database file':
            print(f'Cannot connect to db "{db}". Does directory exist?')
            sys.exit()
        else:
            print(f'Caught exception "{str(e)}"')
            sys.exit()
    return con


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


def read_table(db_path, table):
    '''
    Reads all columns for the latest timestamp from a database table.

    Args:
        db_path (str):  The full path to the database
        table (str):    The table name

    Returns:
        df (df):        A Pandas dataframe containing the data
    '''
    con = connect_to_db(db_path)
    df_ts = pd.read_sql(f'select timestamp from {table} limit 1', con)
    ts = df_ts['timestamp'].to_list()[-1]
    df = pd.read_sql(f'select * from {table} where timestamp = "{ts}"', con)
    con.close()
    return df


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
    # TODO: Finish this function. (Note: I thought about adding a check to
    #       manually delete any files in extravars at beginning and end of
    #       each run, but users might not want that.)


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


def set_dependencies(selected):
    '''
    Ensures that dependent collectors are added to the selection. For example,
    collecting 'f5_vip_destinations' requires collecting 'f5_vip_availability'.
    If a user has selected the former without selecting the latter, then this
    function adds the latter (in the proper order) to the selection.

    Args:
        selected (list): The list of selected collectors

    Returns:
        selected (list): The updated list of selected collectors
    '''
    s = selected
    if 'f5_vip_destinations' in s and 'f5_vip_availability' not in s:
        pos = s.index('f5_vip_destinations')
        s.insert(pos, 'f5_vip_availability')
    return selected


def set_vars():
    '''
    Prompts the user for the required variables for running collectors and
    validators. Several defaults are presented.

    Note: The 'inventories' argument is a list of inventory file. Right now,
          the function statically defines it as
          ['private_data_dir/inventory/hosts']. If people want to use different
          file names or more than one file name, that functionality can be
          added later.

    Args:
        None

    Returns:
        db_path, inventories, nm_path, out_path, private_data_dir
    '''
    default_db = f'{str(dt.now()).split()[0]}.db'
    default_nm_path = '~/source/repos/InsightSSG/Net-Manage/'

    db = input(f'Enter the name of the database: [{default_db}]')
    nm_path = input(f'Enter path to Net-Manage repository [{default_nm_path}]')
    private_data_dir = input('Enter the path to the private data directory:')

    default_out_path = f'{private_data_dir}/output'
    out_path = input(f'Enter the path to store results: [{default_out_path}]')

    if not db:
        db = default_db
    if not nm_path:
        nm_path = default_nm_path
    if not out_path:
        out_path = default_out_path

    # username, password = hp.get_creds()

    db = os.path.expanduser(db)
    nm_path = os.path.expanduser(nm_path)
    out_path = os.path.expanduser(out_path)
    private_data_dir = os.path.expanduser(private_data_dir)
    db_path = f'{out_path}/{db}'

    # TODO: Add support for a custom inventory file name
    # TODO: Add support for more than one inventory file (Ansible-Runner
    #       supports that, but I am not sure how common it is)
    inventories = [f'{private_data_dir}/inventory/hosts']

    return db, db_path, inventories, nm_path, out_path, private_data_dir


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
