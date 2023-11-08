#!/usr/bin/env python3

import json
import pandas as pd
import xml.etree.ElementTree as ET
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
    if response is None:
        raise ValueError("The input is None or empty")

    df_data = dict()
    df_data['device'] = list()

    for device in response:
        output = response[device]['event_data']['res']['stdout']
        root = ET.fromstring(output)
        entries = root.find('.//entries')
        if entries is not None:
            for entry in entries.findall('entry'):
                df_data['device'].append(device)
                for item in entry:
                    key = item.tag
                    value = item.text
                    if not df_data.get(key):
                        df_data[key] = list()
                    df_data[key].append(value)

    df_vendors = hp.find_mac_vendors(df_data['mac'], nm_path)
    df_data['vendor'] = df_vendors['vendor'].to_list()

    df = pd.DataFrame.from_dict(df_data)

    return df


def parse_bgp_neighbors(response: dict) -> pd.DataFrame:
    # Create a dictionary to store the formatted data for each device.
    formatted_data = {
        'device': [],
        'remote-as': [],
        'local-as': [],
        'peer-group-name': [],
        'state': [],
        'local-ip': [],
        'peer-ip': [],
        'status-time': [],
        'ipv4': [],
        'ipv6': []
    }

    for device, data in response.items():
        for vsys, details in data.items():
            formatted_data['device'].append(device)
            formatted_data['remote-as'].append(details['remote-as'])
            formatted_data['local-as'].append(details['local-as'])
            formatted_data['peer-group-name'].append(
                details['peer-group-name'])
            formatted_data['state'].append(details['state'])
            formatted_data['local-ip'].append(details['local-ip'])
            formatted_data['peer-ip'].append(details['peer-ip'])
            formatted_data['status-time'].append(details['status-time'])
            formatted_data['ipv4'].append(details['ipv4'])
            formatted_data['ipv6'].append(details['ipv6'])

    # Convert the formatted_data dictionary to a pandas DataFrame
    df = pd.DataFrame(formatted_data)

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
    Parse 'show system info' command output from Palo Alto firewalls.

    Parameters
    ----------
    response : dict
        A dictionary containing the command output, where the keys are the
        devices and the value is a dictionary.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the hardware inventory.
    '''
    if response is None:
        raise ValueError("The input is None or empty")

    columns = ['device']
    data = dict()

    # The updated code directly processes the 'response' dictionary
    for device, output in response.items():
        data[device] = output

    for key, value in data.items():
        for k in value:
            if k not in columns:
                columns.append(k)

    df_data = dict()
    df_data['device'] = list()
    for col in columns:
        df_data[col] = list()

    for key, value in data.items():
        df_data['device'].append(key)
        for col in columns[1:]:  # Skip the 'device' column.
            df_data[col].append(value.get(col))

    df = pd.DataFrame(df_data)

    return df.astype(str)


def parse_logical_interfaces(response: dict) -> pd.DataFrame:
    '''
    Parse the logical interfaces on Palo Altos.

    Parameters
    ----------
    response : dict
        A dictionary containing the command output, where the keys are the
        devices and the value is an XML Element.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the logical interfaces.
    '''
    if response is None:
        raise ValueError("The input is None or empty")

    df_data = dict()
    df_data['device'] = list()
    columns = ['device']

    for device, output in response.items():
        for entry in output.findall('entry'):
            df_data['device'].append(device)
            for child in entry:
                if child.tag not in columns:
                    columns.append(child.tag)
                    df_data[child.tag] = list()
                df_data[child.tag].append(child.text if child.text else '')

    df = pd.DataFrame(df_data)

    return df.astype(str)


def parse_ospf_neighbors(response: dict) -> pd.DataFrame:
    if response is None:
        raise ValueError("The input is None or empty")

    # Initializing an empty list to collect rows
    rows_list = []

    for device, data in response.items():
        neighbors_data = data.get('neighbors', {})
        for neighbor_ip, neighbors in neighbors_data.items():
            for neighbor in neighbors:
                # Create a dictionary for each neighbor
                neighbor_dict = {
                    'device': device,
                    'neighbor_ip': neighbor_ip,
                    'areaId': neighbor.get('areaId', ''),
                    'ifaceName': neighbor.get('ifaceName', ''),
                    'nbrPriority': neighbor.get('nbrPriority', ''),
                    'nbrState': neighbor.get('nbrState', '')
                }
                # Append the dictionary to rows_list
                rows_list.append(neighbor_dict)

    # Create DataFrame from rows_list
    df = pd.DataFrame(rows_list)

    return df


def parse_physical_interfaces(response: dict) -> pd.DataFrame:
    '''
    Parse the physical interfaces on Palo Altos.

    Parameters
    ----------
    response : dict
        A dictionary containing the command output, where the keys are the
        devices and the value is a list of interface entries.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the physical interfaces.
    '''
    if response is None:
        raise ValueError("The input is None or empty")

    # Initialize data lists for each column
    int_name_list = []
    ip_list = []
    tag_list = []

    for device, entries in response.items():
        for entry in entries:
            int_name = entry.get("@name", "")
            ip = ""
            tag = ""
            layer3 = entry.get("layer3", {})
            if layer3:
                ip_entries = layer3.get("ip", {}).get("entry", [])
                if ip_entries:
                    ip = ip_entries[0].get("@name", "")
            else:  # This branch handles sub-interfaces
                ip_entries = entry.get("ip", {}).get("entry", [])
                if ip_entries:
                    ip = ip_entries[0].get("@name", "")
                tag = entry.get("tag", "")

            # Append the data to the lists
            int_name_list.append(int_name)
            ip_list.append(ip)
            tag_list.append(tag)

    # Create the DataFrame using the collected data
    df = pd.DataFrame({
        "int_name": int_name_list,
        "ip": ip_list,
        "tag": tag_list
    })

    return df.astype(str)


def parse_security_rules(df_rules: pd.DataFrame) -> pd.DataFrame:
    """
    Parse a list of all security rules from a Palo Alto firewall.

    Parameters
    ----------
    df_rules : pd.DataFrame
        A DataFrame containing the raw security rules.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the processed security rules.
    """

    if df_rules is None or df_rules.empty:
        raise ValueError("The input is None or empty")

    # Process the DataFrame to format values
    for column in df_rules.columns:
        df_rules[column] = df_rules[column].apply(lambda x: '|'.join([item.replace(',', ' ') for item in x]) if isinstance(x, list) else str(x))

    # Rename the 'destintaion_zone' column to 'destination_zone' if it exists
    if 'destintaion_zone' in df_rules.columns:
        df_rules.rename({'destintaion_zone': 'destination_zone'}, axis=1, inplace=True)

    return df_rules
