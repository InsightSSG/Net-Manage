#!/usr/bin/env python3

'''
A library of functions for collecting data from network devices.
'''

import ansible_runner
import ipaddress
import pandas as pd
import re
import sqlite3 as sl

from helpers import helpers as hp


def panos_get_security_rules(username,
                             password,
                             host_group,
                             play_path,
                             private_data_dir,
                             device_group='shared'):
    '''
    Gets a list of all security rules from a Palo Alto firewall.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        device_group (str):     The device group to query. Defaults to 'shared'

    Returns:
        df_rules (DataFrame):   A dataframe containing the rules
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
