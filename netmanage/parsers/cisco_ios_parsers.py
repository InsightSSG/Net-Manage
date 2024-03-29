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
        raise ValueError("The input is None or empty")

    rows = list()

    # Regex pattern to match both IPv4 and IPv6 addresses
    ip_pattern = r"(\d+\.\d+\.\d+\.\d+|[0-9a-fA-F:]{3,39})"

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            text = event_data["res"]["stdout"][0]

            neighbors = text.split("BGP neighbor is")[1:]

            for neighbor in neighbors:
                local_host_search = re.search(f"Local host: {ip_pattern}", neighbor)
                local_host = local_host_search.group(1) if local_host_search else None
                bgp_neighbor = re.search(ip_pattern, neighbor).group(1)
                vrf_search = re.search(r"vrf (\w+)", neighbor)
                vrf = vrf_search.group(1) if vrf_search else None
                local_as_search = re.search(r"local AS (\d+)", neighbor)
                local_as = int(local_as_search.group(1)) if local_as_search else None
                remote_as = int(re.search(r"remote AS (\d+)", neighbor).group(1))
                peer_group_search = re.search(
                    r"Member of peer-group ([\w+-]+)", neighbor
                )
                peer_group = peer_group_search.group(1) if peer_group_search else None
                bgp_version = int(re.search(r"BGP version (\d+)", neighbor).group(1))
                neighbor_id = re.search(
                    r"remote router ID (\d+\.\d+\.\d+\.\d+)", neighbor
                ).group(1)
                bgp_state = re.search(r"BGP state = (\w+)", neighbor).group(1)
                bgp_state_timer_search = re.search(r"BGP state = \w+, (.+)", neighbor)
                bgp_state_timer = (
                    bgp_state_timer_search.group(1) if bgp_state_timer_search else None
                )

                rows.append(
                    [
                        device,
                        local_host,
                        bgp_neighbor,
                        vrf,
                        local_as,
                        remote_as,
                        peer_group,
                        bgp_version,
                        neighbor_id,
                        bgp_state,
                        bgp_state_timer,
                    ]
                )

    # Create DataFrame
    df = pd.DataFrame(
        rows,
        columns=[
            "device",
            "local_host",
            "bgp_neighbor",
            "vrf",
            "local_as",
            "remote_as",
            "peer_group",
            "bgp_version",
            "neighbor_id",
            "bgp_state",
            "bgp_state_timer",
        ],
    )

    return df


def parse_cdp_neighbors(runner):
    """Parses the CDP neighbors and returns them in a DataFrame.

    Parameters
    ----------
    runner : generator
        An Ansible runner generator.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the CDP neighbors.
    """
    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Create a dictionary to store the raw data.
    df_data = dict()
    df_data["Device"] = list()
    df_data["Device ID"] = list()
    df_data["Platform"] = list()
    df_data["IPv4 Entry Address"] = list()
    df_data["IPv6 Entry Address"] = list()
    df_data["Capabilities"] = list()
    df_data["Interface"] = list()
    df_data["Port ID (outgoing port)"] = list()
    df_data["Duplex"] = list()
    df_data["IPv4 Management Address"] = list()
    df_data["IPv6 Management Address"] = list()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0]

            output = output.split("-------------------------")
            output = list(filter(None, output))
            output = [_.split("\n") for _ in output]
            output = [list(filter(None, _)) for _ in output]

            for item in output:
                counter = 0
                df_data["Device"].append(device)
                # Define variables that do not always appear.
                capabilities = str()
                duplex = str()
                ipv4_addr = str()
                ipv6_addr = str()
                ipv4_mgmt_addr = str()
                ipv6_mgmt_addr = str()

                # Iterate over the CDP neighbor, populating variables.
                for line in item:
                    if "Device ID" in line:
                        df_data["Device ID"].append(line.split()[-1])

                    if "Entry address(es)" in line:
                        if "IP address" in item[counter + 1]:
                            ipv4_addr = item[counter + 1].split(": ")[-1].strip()
                        if "IPv6 address" in item[counter + 1]:
                            ipv6_addr = item[counter + 1].split(": ")[-1].strip()
                        if "IPv6 address" in item[counter + 2]:
                            ipv6_addr = item[counter + 2].split(": ")[-1].strip()

                    if "Platform" in line:
                        next_char = line.split("Platform:")[1].lstrip()[0]
                        if next_char == ",":
                            df_data["Platform"].append(str())
                        else:
                            df_data["Platform"].append(
                                line.split("Platform: ")[-1].split(",")[0].strip()
                            )

                    if "Capabilities" in line:
                        capabilities = line.split("Capabilities: ")[-1].strip()

                    if "Interface" in line:
                        df_data["Interface"].append(line.split(": ")[1].split(",")[0])

                    if "Port ID (outgoing port)" in line:
                        df_data["Port ID (outgoing port)"].append(
                            line.split(": ")[-1].strip()
                        )

                    if "Duplex" in line:
                        duplex = line.split(": ")[-1].strip()

                    if "Management address(es)" in line:
                        try:
                            if "IP address" in item[counter + 1]:
                                ipv4_mgmt_addr = (
                                    item[counter + 1].split(": ")[-1].strip()
                                )
                        except IndexError:
                            pass

                        try:
                            if "IPv6 address" in item[counter + 1]:
                                ipv6_mgmt_addr = (
                                    item[counter + 1].split(": ")[-1].strip()
                                )
                        except IndexError:
                            pass

                        try:
                            if "IPv6 address" in item[counter + 2]:
                                ipv6_mgmt_addr = (
                                    item[counter + 2].split(": ")[-1].strip()
                                )
                        except Exception:
                            pass

                    counter += 1

                # Add variables that do not always appear, so that arrays are
                # equal length.
                df_data["Capabilities"].append(capabilities)
                df_data["Duplex"].append(duplex)
                df_data["IPv4 Entry Address"].append(ipv4_addr)
                df_data["IPv6 Entry Address"].append(ipv6_addr)
                df_data["IPv4 Management Address"].append(ipv4_mgmt_addr)
                df_data["IPv6 Management Address"].append(ipv6_mgmt_addr)

    return pd.DataFrame(df_data).astype(str)


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
        raise ValueError("The input is None or empty")

    # Create the column headers.
    cols = [
        "neighbor",
        "neighbor_address",
        "interface_id",
        "area",
        "interface",
        "priority",
        "state",
        "state_changes",
        "dead_timer",
        "state_timer",
    ]

    # Create a dictionary to store the parsed output.
    df_data = dict()
    df_data["device"] = list()
    for col in cols:
        df_data[col] = list()

    # Parse the output, create the DataFrame and return it.
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")

            for line in output:
                if "interface address" in line:
                    df_data["device"].append(device)
                    if len(line.split(",")) == 3:
                        df_data["interface_id"].append(line.split()[-1])
                    else:
                        df_data["interface_id"].append("")
                    line = line.split()
                    df_data["neighbor"].append(line[1].strip(","))
                    df_data["neighbor_address"].append(line[4].strip(","))
                if "area" in line:
                    line = line.split()
                    df_data["area"].append(line[3])
                    df_data["interface"].append(line[-1])
                if "priority" in line:
                    line = line.split()
                    df_data["priority"].append(line[3].strip(","))
                    df_data["state"].append(line[6].strip(","))
                    df_data["state_changes"].append(line[-3])
                if "Dead timer" in line:
                    df_data["dead_timer"].append(line.split()[-1])
                if "for" in line:
                    df_data["state_timer"].append(line.split()[-1])

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

            output = event_data["res"]["stdout"][0].split("\n")

            # Gather the header indexes.
            try:
                header = output[0]
                rd_pos = header.index("Default RD")
                proto_pos = header.index("Protocols")
                inf_pos = header.index("Interfaces")
            except Exception as e:
                if str(e) == "substring not found":  # Raised if no VRFs.
                    pass
                else:
                    print(f"{device}: {str(e)}")

            # Reverse 'output' to make it easier to parse.
            output.reverse()

            # Parse the output.
            counter = 0
            for line in output:
                if len(line.split()) > 1 and "Default RD" not in line:
                    interfaces = list()
                    name = line[:rd_pos].strip()
                    default_rd = line[rd_pos:proto_pos].strip()
                    protocols = line[proto_pos:inf_pos].strip()
                    interfaces.append(line[inf_pos:].strip())
                    pos = counter
                    # Collect additional interfaces for the VRF.
                    while len(output[pos + 1].split()) <= 1:
                        interfaces.append(output[pos + 1].split()[0])
                        pos += 1
                    # Add the VRF to df_data.
                    df_data["device"].append(device)
                    df_data["Name"].append(name)
                    df_data["Default RD"].append(default_rd)
                    df_data["Protocols"].append(protocols)
                    df_data["Interfaces"].append(interfaces)
                counter += 1

    # Create the dataframe then reverse it to preserve the original order.
    df = pd.DataFrame(df_data)
    df = df.iloc[::-1].reset_index(drop=True)

    # Convert the data in the 'Interfaces' column from a list to a
    # space-delimited string.
    df["Interfaces"] = df["Interfaces"].apply(lambda x: " ".join(x)).astype(str)

    return df


def parse_ios_parse_uplink_by_ip(
    df_ip: pd.DataFrame, df_cdp: pd.DataFrame
) -> pd.DataFrame:
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
    cols = ["Device", "IP", "Local Interface", "Remote Device", "Remote Interface"]
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
    columns = ["device", "protocol", "address", "age", "mac", "inf_type", "interface"]

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
    # df_data = list()
    df_data = dict()
    df_data['device'] = list()
    df_data['interface'] = list()
    df_data['description'] = list()
    df_data['ip'] = list()
    df_data['encapsulation'] = list()
    df_data['tag'] = list()
    df_data['vrf'] = list()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")

            counter = 0
            for line in output:
                counter += 1
                try:
                    if line.split()[0] == 'interface':
                        if output[counter].split()[0] in ('ip',
                                                          'description',
                                                          'encapsulation',
                                                          'vrf'):
                            interface = line.split()[-1]
                            ip = str()
                            block = output[counter:counter+4]
                            description = str()
                            encapsulation = str()
                            tag = str()
                            vrf = 'None'
                            for item in block:
                                if item.split()[0] == 'interface':
                                    break
                                elif 'ip address' in item:
                                    ip = item.split('ip address ')[-1].strip()
                                elif item.split()[0] == 'encapsulation':
                                    encapsulation = item.split()[-2]
                                    tag = item.split()[-1]
                                elif item.split()[0] == 'vrf':
                                    vrf = item.split()[-1]
                                elif item.split()[0] == 'description':
                                    description = item.split('description ')[-1].strip()
                            try:
                                if ip and ip != 'no ip address':
                                    df_data['device'].append(device)
                                    df_data['interface'].append(interface)
                                    df_data['description'].append(description)
                                    df_data['ip'].append(ip)
                                    df_data['encapsulation'].append(encapsulation)
                                    df_data['tag'].append(tag)
                                    df_data['vrf'].append(vrf)
                            except Exception as e:
                                print(f'{device}: {str(e)}: {", ".join(block)}')
                except IndexError:
                    pass

    # Create a dataframe from df_data.
    df = pd.DataFrame(df_data)

    # Add the subnets, network IPs, and broadcast IPs.
    addresses = df["ip"].to_list()
    result = hp.generate_subnet_details(addresses)
    df["subnet"] = result["subnet"]
    df["network_ip"] = result["network_ip"]
    df["broadcast_ip"] = result["broadcast_ip"]

    # Add a column containing the CIDR notation.
    cidrs = hp.subnet_mask_to_cidr(df["subnet"].to_list())
    df["cidr"] = cidrs
    df = df[
        [
            "device",
            "interface",
            "description",
            "ip",
            "cidr",
            "vrf",
            "subnet",
            "network_ip",
            "broadcast_ip",
        ]
    ]

    # Remove the cidr notation or subnet mask from the 'ip' column.
    df['ip'] = [_.split('/')[0].split(' ')[0] for _ in df['ip'].to_list()]

    return df.astype(str)


def ios_parse_interface_ipv6_ips(runner: dict) -> pd.DataFrame:
    """
    Parses the IPv6 addresses assigned to interfaces.

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

    # Lists to hold data
    devices = list()
    interfaces = list()
    ips = list()
    vrfs = list()

    # Parse the results
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            lines = event_data["res"]["stdout"][0].split("\n")

            idx = 0
            while idx < len(lines):
                line = lines[idx]
                # Detecting interface lines
                if "line protocol is" in line:
                    interface = line.split()[0]
                    ip = ""
                    vrf = ""

                    # Checking for the next lines to see if they contain IPs
                    next_line_idx = idx + 1
                    if (
                        next_line_idx < len(lines)
                        and "subnet is" in lines[next_line_idx]
                    ):
                        ip = lines[next_line_idx].split(",")[0].strip()

                        # Checking for VRF in the subsequent line
                        if (
                            next_line_idx + 1 < len(lines)
                            and "VPN Routing/Forwarding" in lines[next_line_idx + 1]
                        ):
                            vrf = lines[next_line_idx + 1].split('"')[1].strip()

                    devices.append(device)
                    interfaces.append(interface)
                    ips.append(ip)
                    vrfs.append(vrf)

                    idx = next_line_idx + 2 if vrf else next_line_idx + 1
                else:
                    idx += 1

    # Create the dataframe.
    df = pd.DataFrame(
        {"device": devices, "interface": interfaces, "ip": ips, "vrf": vrfs}
    )

    return df

    # Add the subnets, network IPs, and broadcast IPs.
    addresses = df["ip"].to_list()
    result = hp.generate_subnet_details(addresses)
    df["subnet"] = result["subnet"]
    df["network_ip"] = result["network_ip"]
    df["broadcast_ip"] = result["broadcast_ip"]

    # Add a column containing the CIDR notation.
    cidrs = hp.subnet_mask_to_cidr(df["subnet"].to_list())
    df["cidr"] = cidrs
    df = df[
        [
            "device",
            "interface",
            "ip",
            "cidr",
            "vrf",
            "subnet",
            "network_ip",
            "broadcast_ip",
        ]
    ]

    return df


def ios_parse_inventory(runner: dict) -> pd.DataFrame:
    """
    Parses the inventory for Cisco IOS and IOS-XE devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner generator.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the inventory data.
    """
    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Create a dictionary to store the inventory data.
    columns = ["device", "name", "description", "pid", "vid", "serial"]
    df_data = {col: [] for col in columns}

    # Parse the output and add it to 'df_data'
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]
            device = event_data["remote_addr"]

            data = list(filter(None, event_data["res"]["stdout"][0].split("\n")))

            if data:
                for i in range(0, len(data)):
                    # Handling the "NAME: ... , DESCR: ..." lines
                    if data[i].startswith("NAME: "):
                        try:
                            df_data["device"].append(device)
                            # Split the first line to extract name, description
                            name_desc = data[i].split(", DESCR: ")
                            df_data["name"].append(
                                name_desc[0]
                                .replace('NAME: "', "")
                                .replace('"', "")
                                .strip()
                            )
                            df_data["description"].append(
                                name_desc[1].replace('"', "").strip()
                            )

                            # Next line will have the PID, VID, SN data
                            pid_vid_sn = data[i + 1].split(", ")
                            df_data["pid"].append(
                                pid_vid_sn[0].replace("PID: ", "").strip()
                            )
                            df_data["vid"].append(
                                pid_vid_sn[1].replace("VID: ", "").strip()
                            )
                            sn_value = pid_vid_sn[2].replace("SN: ", "").strip()
                            if sn_value == "SN:":
                                sn_value = ""
                            df_data["serial"].append(sn_value)

                        except (IndexError, ValueError):
                            print(f"Error processing: {data[i]}")
                            continue

    # Create the DataFrame and return it.
    df = pd.DataFrame(df_data)
    return df


def ios_parse_gather_basic_facts(results: dict) -> pd.DataFrame:
    """
    Parses the results from cisco_ios_collectors.basic_facts.

    Parameters
    ----------
    results : dict
        A dictionary containing the results from
        cisco_ios_collectors.gather_basic_facts.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the facts.
    """
    # Create a dictionary to store the parsed data.
    df_data = dict()
    df_data["device"] = list()

    # Create keys for df_data.
    for key, value in results.items():
        for k in value:
            if not df_data.get(k):
                df_data[k] = list()

    # Populate df_data.
    for key, value in results.items():
        df_data["device"].append(key)
        for key in df_data:
            if key != "device":
                df_data[key].append(value.get(key))

    # Create the DataFrame and return it.
    df = pd.DataFrame(df_data)
    df = df.astype(str)

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
    if not df_data:
        return pd.DataFrame()
    df = pd.DataFrame(data=df_data, columns=cols)
    return df
