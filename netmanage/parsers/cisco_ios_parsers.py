#!/usr/bin/env python3

import pandas as pd
import re

from netmanage.helpers import helpers as hp


def parse_facts(runner: dict) -> dict:
    """Gathers specified facts on Cisco IOS devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    facts : dict
        A dictionary where each key is a device in the host_group and the value
        is the requested facts.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Parse the output, store it in 'facts', and return it
    facts = dict()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]
            output = event_data["res"]["ansible_facts"]

            facts[device] = output

    return facts


def parse_bgp_neighbors(runner):
    """Parses the BGP neighbor summary output and returns it in a DataFrame.

    Parameters
    ----------
    runner : generator
        An Ansible runner generator.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the BGP neighbor summary.
    """
    if runner is None or runner.events is None:
        raise ValueError('The input is None or empty')

    rows = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            text = event_data['res']['stdout'][0]

            neighbors = text.split("BGP neighbor is")[1:]

            for neighbor in neighbors:
                local_host_search = re.search(
                    r"Local host: (\d+\.\d+\.\d+\.\d+)", neighbor)
                local_host = local_host_search.group(1) \
                    if local_host_search else None
                bgp_neighbor = re.search(
                    r"(\d+\.\d+\.\d+\.\d+)", neighbor).group(1)
                vrf_search = re.search(r"vrf (\w+)", neighbor)
                vrf = vrf_search.group(1) if vrf_search else None
                local_as_search = re.search(r"local AS (\d+)", neighbor)
                local_as = int(local_as_search.group(1)) \
                    if local_as_search else None
                remote_as = int(
                    re.search(r"remote AS (\d+)", neighbor).group(1))
                peer_group_search = re.search(
                    r"Member of peer-group ([\w+-]+)", neighbor)
                peer_group = peer_group_search.group(
                    1) if peer_group_search else None
                bgp_version = int(
                    re.search(r"BGP version (\d+)", neighbor).group(1))
                neighbor_id = re.search(
                    r"remote router ID (\d+\.\d+\.\d+\.\d+)", neighbor).\
                    group(1)
                bgp_state = re.search(r"BGP state = (\w+)", neighbor).group(1)
                bgp_state_timer_search = re.search(
                    r"BGP state = \w+, (.+)", neighbor)
                bgp_state_timer = bgp_state_timer_search.group(
                    1) if bgp_state_timer_search else None

                rows.append([device,
                             local_host,
                             bgp_neighbor,
                             vrf,
                             local_as,
                             remote_as,
                             peer_group,
                             bgp_version,
                             neighbor_id,
                             bgp_state,
                             bgp_state_timer])

    # Create DataFrame
    df = pd.DataFrame(rows, columns=["device",
                                     "local_host",
                                     "bgp_neighbor",
                                     "vrf",
                                     "local_as",
                                     "remote_as",
                                     "peer_group",
                                     "bgp_version",
                                     "neighbor_id",
                                     "bgp_state",
                                     "bgp_state_timer"])

    return df


def parse_config(facts: dict) -> pd.DataFrame:
    """Parses the config on Cisco IOS devices.

    Parameters
    ----------
    facts : dict
        A dictionary where each key is a device in the host_group and the value
        is the requested facts.

    Returns
    -------
    df : pandas.DataFrame
        A DataFrame containing the device configurations.
    """
    if facts is None or len(list(facts)) == 0:
        raise ValueError("The input is None or empty")

    configs = dict()
    for key, value in facts.items():
        configs[key] = value["ansible_net_config"]

    df = pd.DataFrame(list(configs.items()), columns=["device", "config"])

    return df


def parse_ospf_neighbors(runner: dict) -> pd.DataFrame:
    """Parses the OSPF neighbors output and returns it in a DataFrame.

    Parameters
    ----------
    runner : dict
        An Ansible runner generator.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the OSPF neighbors.
    """
    if runner is None or runner.events is None:
        raise ValueError('The input is None or empty')

    # Create the column headers.
    cols = ['neighbor',
            'neighbor_address',
            'interface_id',
            'area',
            'interface',
            'priority',
            'state',
            'state_changes',
            'dead_timer',
            'state_timer'
            ]

    # Create a dictionary to store the parsed output.
    df_data = dict()
    df_data['device'] = list()
    for col in cols:
        df_data[col] = list()

    # Parse the output, create the DataFrame and return it.
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

            for line in output:
                if 'interface address' in line:
                    df_data['device'].append(device)
                    if len(line.split(',')) == 3:
                        df_data['interface_id'].append(line.split()[-1])
                    else:
                        df_data['interface_id'].append('')
                    line = line.split()
                    df_data['neighbor'].append(line[1].strip(','))
                    df_data['neighbor_address'].append(line[4].strip(','))
                if 'area' in line:
                    line = line.split()
                    df_data['area'].append(line[3])
                    df_data['interface'].append(line[-1])
                if 'priority' in line:
                    line = line.split()
                    df_data['priority'].append(line[3].strip(','))
                    df_data['state'].append(line[6].strip(','))
                    df_data['state_changes'].append(line[-3])
                if 'Dead timer' in line:
                    df_data['dead_timer'].append(line.split()[-1])
                if 'for' in line:
                    df_data['state_timer'].append(line.split()[-1])

    # Create the dataframe and return it.
    df = pd.DataFrame(df_data).astype(str)

    return df


def parse_vrfs(runner: dict) -> pd.DataFrame:
    """Retrieve VRF information and return it as a DataFrame.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing VRF information, with columns ["device", "name",
        "vrf_id", "default_rd", "default_vpn_id"].
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Create a dictionary to store the parsed output.
    df_data = dict()
    df_data["device"] = list()
    df_data["Name"] = list()
    df_data["Default RD"] = list()
    df_data["Protocols"] = list()
    df_data["Interfaces"] = list()

    # Parse the output, create the DataFrame and return it.
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data['res']['stdout'][0].split('\n')

            # Gather the header indexes.
            try:
                header = output[0]
                rd_pos = header.index('Default RD')
                proto_pos = header.index('Protocols')
                inf_pos = header.index('Interfaces')
            except Exception as e:
                if str(e) == 'substring not found':  # Raised if no VRFs.
                    pass
                else:
                    print(f'{device}: {str(e)}')

            # Reverse 'output' to make it easier to parse.
            output.reverse()

            # Parse the output.
            counter = 0
            for line in output:
                if len(line.split()) > 1 and 'Default RD' not in line:
                    interfaces = list()
                    name = line[:rd_pos].strip()
                    default_rd = line[rd_pos:proto_pos].strip()
                    protocols = line[proto_pos:inf_pos].strip()
                    interfaces.append(line[inf_pos:].strip())
                    pos = counter
                    # Collect additional interfaces for the VRF.
                    while len(output[pos+1].split()) <= 1:
                        interfaces.append(output[pos+1].split()[0])
                        pos += 1
                    # Add the VRF to df_data.
                    df_data['device'].append(device)
                    df_data['Name'].append(name)
                    df_data['Default RD'].append(default_rd)
                    df_data['Protocols'].append(protocols)
                    df_data['Interfaces'].append(interfaces)
                counter += 1

    # Create the dataframe then reverse it to preserve the original order.
    df = pd.DataFrame(df_data)
    df = df.iloc[::-1].reset_index(drop=True)

    # Convert the data in the 'Interfaces' column from a list to a
    # space-delimited string.
    df['Interfaces'] = df['Interfaces'].apply(
        lambda x: ' '.join(x)).astype(str)

    return df


def parse_ios_parse_uplink_by_ip(
        df_ip: pd.DataFrame, df_cdp: pd.DataFrame) -> pd.DataFrame:
    """
    Search the hostgroup for a list of subnets (use /32 to search for a
    single IP). Once it finds them, it uses CDP and LLDP (if applicable) to try
    to find the uplink.

    If a list of IP addresses is not provided, it will attempt to find the
    uplinks for all IP addresses on the devices.

    Parameters
    ----------
    df_ip: pd.DataFrame
        IP addresses on the devices in the host group.
    df_cdp: pd.DataFrame
        The CDP neighbors for the device.

    Returns
    -------
    df_combined : pd.DataFrame
        A DataFrame containing the IP to remote port mapping.

    Notes
    -----
    This is a simple function that was written for a single use case. It has
    some limitations:

    1. There is not an option to specify the VRF (although it will still return
       the uplinks for every IP that meets the parameters).
    2. If CDP and LLDP are disabled or the table is not populated, it does not
       try alternative methods like interface descriptions and CAM tables. I
       can add those if there is enough interest in this function.

    TODOs:
    - Add alternative methods if CDP and LLDP do not work:
      - Interface descriptions
      - Reverse DNS (in the case of P2P IPs)
      - CAM table
    - Add an option to specify the VRF (low priority).
    """

    # Remove the sub-interfaces from df_ip
    local_infs = df_ip["Interface"].to_list()
    local_infs = [inf.split(".")[0] for inf in local_infs]
    df_ip["Interface"] = local_infs

    # Attempt to find the neighbors for the interfaces that have IPs
    df_data = list()

    for idx, row in df_ip.iterrows():
        device = row["Device"]
        inf = row["Interface"]
        neighbor_row = df_cdp.loc[
            (df_cdp["Device"] == device) & (df_cdp["Local Inf"] == inf)
        ]
        remote_device = list(neighbor_row["Neighbor"].values)
        if remote_device:
            remote_device = remote_device[0]
            remote_inf = list(neighbor_row["Remote Inf"].values)[0]
        else:
            remote_device = "unknown"
            remote_inf = "unknown"
        mgmt_ip = row["IP"]
        df_data.append([device, mgmt_ip, inf, remote_device, remote_inf])
    # Create a DataFrame and return it
    cols = ["Device", "IP", "Local Interface",
            "Remote Device", "Remote Interface"]
    df_combined = pd.DataFrame(data=df_data, columns=cols)

    return df_combined


def ios_parse_arp_table(runner: dict, nm_path: str) -> pd.DataFrame:
    """
    Parses the IOS ARP table and add the vendor OUI.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator
    nm_path : str
        The path to the Net-Manage repository.

    Returns
    -------
    df_arp : pd.DataFrame
        The ARP table and vendor OUI as a pandas DataFrame.
    """

    if nm_path is None:
        raise ValueError("The input nm_path is None or empty")

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Create the column headers. I do not like to hard code these, but they
    # should be modified from Cisco's format before being stored in a
    # database. I suppose it is not strictly necessary to do so, but
    # "Age (min)" and "Hardware Addr" do not make for good column headers.
    columns = ["device", "protocol", "address",
               "age", "mac", "inf_type", "interface"]

    # Parse the output and add it to 'data'
    df_data = list()
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")

            for line in output[1:]:
                row = [device] + line.split()
                df_data.append(row)

    # Create the DataFrame
    df_arp = pd.DataFrame(data=df_data, columns=columns)

    # Parses the vendor OUIs
    df_vendors = hp.find_mac_vendors(df_arp["mac"], nm_path)

    # Add the vendor OUIs to df_cam as a column, and return the dataframe.
    df_arp["vendor"] = df_vendors["vendor"]

    return df_arp


def ios_parse_cam_table(runner: dict, nm_path: str) -> pd.DataFrame:
    """
    Parses the IOS CAM table and add the vendor OUI.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator
    nm_path : str
        The path to the Net-Manage repository.

    Returns
    -------
    df_cam : pd.DataFrame
        The CAM table and vendor OUI as a pandas DataFrame.
    """

    if nm_path is None:
        raise ValueError("The input nm_path is None or empty")

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Create the column headers. I do not like to hard code these, but they
    # should be modified from Cisco's format before being stored in a
    # database. I suppose it is not strictly necessary to do so, but
    # "Mac Address" and "Type" do not make good column headers.
    columns = ["device", "vlan", "mac", "inf_type", "ports"]

    # Parse the output and add it to 'data'
    df_data = list()
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")
            # columns = list(filter(None, output[0].split('  ')))
            # columns.insert(0, 'device')
            # columns = [_.strip() for _ in columns]

            for line in output[2:-1]:
                row = [device] + line.split()
                df_data.append(row)

    # Create the DataFrame
    df_cam = pd.DataFrame(data=df_data, columns=columns)

    # Parses the vendor OUIs
    df_vendors = hp.find_mac_vendors(df_cam["mac"], nm_path)

    # Add the vendor OUIs to df_cam as a column, and return the dataframe.
    df_cam["vendor"] = df_vendors["vendor"]

    return df_cam


def ios_parse_cdp_neighbors(runner: dict) -> pd.DataFrame:
    """
    Parses the CDP neighbors for a Cisco IOS device.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_cdp : pd.DataFrame
        A DataFrame containing the CDP neighbors.
    """
    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Parse the results
    cdp_data = list()
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")
            pos = 1  # Used to account for multiple connections to same device
            for line in output:
                if "Device ID" in line:
                    remote_device = line.split("(")[0].split()[2].split(".")[0]
                    local_inf = output[pos].split()[1].strip(",")
                    remote_inf = output[pos].split()[-1]
                    row = [device, local_inf, remote_device, remote_inf]
                    cdp_data.append(row)
                pos += 1
    # Create a dataframe from cdp_data and return the results
    cols = ["Device", "Local Inf", "Neighbor", "Remote Inf"]
    df_cdp = pd.DataFrame(data=cdp_data, columns=cols)
    return df_cdp


def ios_parse_interface_descriptions(runner: dict) -> pd.DataFrame:
    """
    Get IOS interface descriptions.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_desc : pd.DataFrame
        A DataFrame containing the interface descriptions.
    """

    df_data = list()
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")
            # Parses the position of the 'Description' column
            # (we cannot split by spaces because some
            # interface descriptions have spaces in them).
            pos = output[0].index("Description")
            for line in output[1:]:
                inf = line.split()[0]
                desc = line[pos:]
                df_data.append([device, inf, desc])

    # Create the dataframe and return it
    cols = ["device", "interface", "description"]
    df_desc = pd.DataFrame(data=df_data, columns=cols)
    return df_desc


def ios_parse_interface_ips(runner: dict) -> pd.DataFrame:
    """
    Parses the IP addresses assigned to interfaces.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the interfaces and IP addresses.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Parse the results
    df_data = list()
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")
            output.reverse()  # Reverse the output to make it easier to iterate
            counter = 0
            for line in output:
                if "Internet address" in line:
                    pos = counter
                    if "VPN Routing/Forwarding" in output[pos - 1]:
                        vrf = output[pos - 1].split()[-1].strip('"')
                    else:
                        vrf = "None"
                    ip = line.split()[-1]
                    inf = output[pos + 1].split()[0]
                    row = [device, inf, ip, vrf]
                    df_data.append(row)
                counter += 1

    # Create a dataframe from df_data and return it
    df_data.reverse()
    cols = ["device", "interface", "ip", "vrf"]
    df = pd.DataFrame(data=df_data, columns=cols)

    # Add the subnets, network IPs, and broadcast IPs.
    addresses = df['ip'].to_list()

    df['ip'] = [_.split('/')[0] for _ in df['ip'].to_list()]

    result = hp.generate_subnet_details(addresses)
    df["subnet"] = result["subnet"]
    df["network_ip"] = result["network_ip"]
    df["broadcast_ip"] = result["broadcast_ip"]

    return df


def ios_parse_vlan_db(runner: dict) -> pd.DataFrame:
    """
    Parses the VLAN database for Cisco IOS devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the VLAN database.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    df_data = list()
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")

            # Create the column headers
            cols = ["device"] + output[0].split()[:3]
            cols = [_.lower() for _ in cols]

            # Removed wrapped interfaces
            output = [_ for _ in output[1:] if _[0] != " "]

            # Add the VLANs to 'df_data'
            for line in output:
                row = [device] + line.split()[:3]
                df_data.append(row)

    # Create the dataframe and return it
    df = pd.DataFrame(data=df_data, columns=cols)
    return df
