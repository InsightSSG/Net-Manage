#!/usr/bin/env python3

import json
import pandas as pd
from netmanage.helpers import helpers as hp


def parse_all_interfaces(response: dict) -> pd.DataFrame:
    '''
    Parse all interfaces on Palo Altos.

    Parameters
    ----------
    response : dict
        A dictionary containing the command output, where the keys are the
        devices and the value is a dictionary

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the logical interfaces.

    '''

    if response is None:
        raise ValueError("The input is None or empty")

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


def parse_arp_table(response: dict, nm_path: str) -> pd.DataFrame:
    '''
    Parses the Palo Alto ARP table and adds vendor OUIs.

    Parameters
    ----------
    response : dict
        A dictionary containing the command output, where the keys are the
        devices and the value is a dictionary
    nm_path : str
        The path to the Net-Manage repository.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the ARP table and vendor OUIs.

    Other Parameters
    ----------------
    interface : str, optional
        The interface for which to return the ARP table. The default is to
        return the ARP table for all interfaces.
    '''

    if response is None:
        raise ValueError("The input is None or empty")

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


def parse_bgp_neighbors(response: dict) -> pd.DataFrame:
    '''
    Parse BGP neighbors for Palo Alto firewalls.

    Parameters
    ----------
    response : dict
        A dictionary containing the command output, where the keys are the
        devices and the value is a dictionary

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the BGP peers.
    '''
    if response is None:
        raise ValueError("The input is None or empty")

    # Create a dictionary to store the formatted cmd output for each device.
    result = dict()

    # Parse 'response', adding the cmd output for each device to 'result'.
    for device, event in response.items():
        output = json.loads(event['event_data']['res']['stdout'])
        try:
            if output['response']['result'].get('entry'):
                output = output['response']['result']['entry']
                result[device] = output
        except Exception as e:
            if str(e) == "'NoneType' object has no attribute 'get'":
                pass
            else:
                print(f'{device}: {str(e)}')

    # Use the data in 'result' to populate 'df_data', which will be used to
    # create the dataframe.
    df_data = dict()
    df_data['device'] = list()
    for device in result:
        # If there is only one neighbor, then the Palo Alto API returns a
        # dictionary.
        if isinstance(result[device], dict):
            df_data['device'].append(device)
            for key, value in result[device].items():
                if not df_data.get(key):
                    df_data[key] = list()
                df_data[key].append(value)
        # If there is more than one neighbor, then the Palo Alto API returns a
        # list.
        else:
            for item in result[device]:
                df_data['device'].append(device)
                for key, value in item.items():
                    if not df_data.get(key):
                        df_data[key] = list()
                    df_data[key].append(value)

    # Create the dataframe.
    df = pd.DataFrame.from_dict(df_data).astype(str)

    return df


def parse_interface_ips(df: pd.DataFrame) -> pd.DataFrame:
    '''Parse IP addresses on Palo Alto firewall interfaces.

    Parameters
    ----------
    df : Pandas Dataframe
        A pd.DataFrame

    Returns
    -------
    df : Pandas Dataframe
        A dataframe containing the IP addresses.

    '''
    # TODO: Optimize this function by setting 'get_all_interfaces' as a
    #       dependency. That way the same command does not need to be
    #       run twice (potentially) for two different collectors.

    if df is None:
        raise ValueError("The input is None or empty")

    # Filter out interfaces that do not have an IP address.
    df = df[df['ip'] != 'N/A'].copy()

    # Add the subnets, network IPs, and broadcast IPs.
    addresses = df['ip'].to_list()
    result = hp.generate_subnet_details(addresses)
    df['subnet'] = result['subnet']
    df['network_ip'] = result['network_ip']
    df['broadcast_ip'] = result['broadcast_ip']

    # Split the 'ip' column to separate the IP and the CIDR notation
    df['cidr'] = df['ip'].str.split('/').str[1]
    df['ip'] = df['ip'].str.split('/').str[0]

    # Rearrange the columns to place 'cidr' column to the right of 'ip' column.
    cols = df.columns.tolist()
    ip_index = cols.index('ip')
    cols.insert(ip_index + 1, cols.pop(cols.index('cidr')))
    df = df[cols]

    return df


def parse_inventory(response: dict) -> pd.DataFrame:
    '''
    Parse 'show system info' command on Palo Alto firewalls.

    Parameters
    ----------
    response : dict
        A dictionary containing the command output, where the keys are the
        devices and the value is a dictionary

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the hardware inventory.

    '''
    if response is None:
        raise ValueError("The input is None or empty")

    # Create a list to store columns. This method accounts for the fact that
    # not all devices return the same data.
    columns = ['device']

    # Create a dictionary to store the output. This will allow us to iterate
    # over all the output and collect the column headers before populating the
    # dataframe.
    data = dict()

    # Parse 'response', adding the cmd output for each device to 'result'.
    for device, event in response.items():
        output = json.loads(event['event_data']['res']['stdout'])
        if output['response']['result'].get('system'):
            output = output['response']['result'].get('system')
            data[device] = output

    # Iterate over the output, adding all column names to 'columns'.
    for key, value in data.items():
        for k in value:
            if k not in columns:
                columns.append(k)

    # Create a dictionary to store the formatted data for the dataframe.
    df_data = dict()
    df_data['device'] = list()
    for col in columns:
        df_data[col] = list()

    # Iterate over the output, adding all data to 'df_data'.
    for key, value in data.items():
        df_data['device'].append(key)
        for col in columns[1:]:  # Skip the 'device' column.
            df_data[col].append(value.get(col))

    # Create the dataframe and return it.
    df = pd.DataFrame(df_data)

    return df.astype(str)


def parse_logical_interfaces(response: pd.DataFrame) -> pd.DataFrame:
    '''
    Parse the logical interfaces on Palo Altos.

    Parameters
    ----------
    response : dict
        A dictionary containing the command output, where the keys are the
        devices and the value is a dictionary

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the logical interfaces.

    '''

    if response is None:
        raise ValueError("The input is None or empty")

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


def parse_ospf_neighbors(response: dict) -> pd.DataFrame:
    '''
    Parse OSPF neighbors for Palo Alto firewalls.

    Parameters
    ----------
    response : dict
        A dictionary containing the command output, where the keys are the
        devices and the value is a dictionary

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the OSPF neighbors.
    '''
    if response is None:
        raise ValueError("The input is None or empty")

    # Create a dictionary to store the formatted cmd output for each device.
    result = dict()

    # Parse 'response', adding the cmd output for each device to 'result'.
    for device, event in response.items():
        output = json.loads(event['event_data']['res']['stdout'])
        if output['response']['result'].get('entry'):
            output = output['response']['result']['entry']
            result[device] = output

    # Use the data in 'result' to populate 'df_data', which will be used to
    # create the dataframe.
    df_data = dict()
    df_data['device'] = list()
    for device in result:
        # If there is only one neighbor, then the Palo Alto API returns a
        # dictionary.
        if isinstance(result[device], dict):
            df_data['device'].append(device)
            for key, value in result[device].items():
                if not df_data.get(key):
                    df_data[key] = list()
                df_data[key].append(value)
        # If there is more than one neighbor, then the Palo Alto API returns a
        # list.
        else:
            for item in result[device]:
                df_data['device'].append(device)
                for key, value in item.items():
                    if not df_data.get(key):
                        df_data[key] = list()
                    df_data[key].append(value)

    # Create the dataframe.
    df = pd.DataFrame.from_dict(df_data).astype(str)

    return df


def parse_physical_interfaces(response: dict) -> pd.DataFrame:
    '''
    Parse the physical interfaces on Palo Altos.

    Parameters
    ----------
    response : dict
        A dictionary containing the command output, where the keys are the
        devices and the value is a dictionary

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the physical interfaces.


    '''

    if response is None:
        raise ValueError("The input is None or empty")

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


def parse_security_rules(runner: dict) -> pd.DataFrame:
    '''
    Parse a list of all security rules from a Palo Alto firewall.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_rules : pd.DataFrame
        A DataFrame containing the security rules.
    '''

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

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
