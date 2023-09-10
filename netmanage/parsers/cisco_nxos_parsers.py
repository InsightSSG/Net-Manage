#!/usr/bin/env python3

import ipaddress
import pandas as pd
import re

from netmanage.helpers import helpers as hp


def nxos_diff_running_config(runner: dict) -> pd.DataFrame:
    """
    Parse the running-config diff for NXOS devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_diff : pd.DataFrame
        The diff.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    df_data = list()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")[3:]

            for line in output:
                df_data.append([device, line])

    # Create the dataframe and return it
    cols = ["device", "diff"]
    df_diff = pd.DataFrame(data=df_data, columns=cols)

    return df_diff


def nxos_parse_arp_table(runner: dict, nm_path: str) -> pd.DataFrame:
    """
    Parse the ARP table for Cisco NXOS devices and retrieve the OUI (vendor)
    for each MAC address. Optionally, perform a reverse DNS query for,
    hostnames but note that it may take several minutes for large datasets.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator
    nm_path : str
        The path to the Net-Manage repository.

    Returns
    -------
    df_arp : pd.DataFrame
        The ARP table as a pandas DataFrame.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Parse the output and add it to 'data'
    df_data = list()

    # Create a list of mac addresses (used for querying the vendor)
    macs = list()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")

            # Parse the output and add it to 'df_data'
            for line in output[1:]:
                line = line.split()
                address = line[0]
                age = line[1]
                mac = line[2]
                inf = line[3]
                macs.append(mac)
                row = [device, address, age, mac, inf]
                # Perform a reverse DNS lookup if requested
                # TODO: Convert this to a standalone function
                # if reverse_dns:
                #     try:
                #         rdns = socket.getnameinfo((address, 0), 0)[0]
                #     except Exception:
                #         rdns = 'unknown'
                #     row.append(rdns)
                df_data.append(row)

    cols = ["device", "ip_address", "age", "mac_address", "interface"]

    # TODO: Convert this to a standalone function
    # if reverse_dns:
    #     cols.append('reverse_dns')

    df_arp = pd.DataFrame(data=df_data, columns=cols)

    # Find the vendrs and add them to the dataframe
    df_vendors = hp.find_mac_vendors(macs, nm_path)
    df_arp["vendor"] = df_vendors["vendor"]

    return df_arp


def nxos_parse_fexes_table(runner: dict, nm_path: str) -> pd.DataFrame:
    """
    Parse the FEXes for Cisco 5Ks. This function is required for gathering
    interface data on devices with a large number of FEXes, as it helps
    prevent timeouts.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator
    nm_path : str
        The path to the Net-Manage repository.

    Returns
    -------
    df : pd.DataFrame
        The FEXes of the device. If there are no FEXes, an empty DataFrame
        will be returned.
    """
    # Define regular expressions to match each line
    regex_patterns = {
        'fex': r'FEX: (\d+)',
        'description': r'Description: ([\w-]+)',
        'state': r'state: (\w+)',
        'fex_version': r'FEX version: ([\d\.\(\)N]+)',
        'switch_version': r'Switch version: ([\d\.\(\)N]+)',
        'fex_interim_version': r'FEX Interim version: ([\d\.\(\)N]+)',
        'switch_interim_version': r'Switch Interim version: ([\d\.\(\)N]+)',
        'extender_serial': r'Extender Serial: (\w+)',
        'extender_model': r'Extender Model: ([\w-]+)',
        'part_no': r'Part No: ([\w-]+)',
        'card_id': r'Card Id: (\d+)',
        'mac_addr': r'Mac Addr: ([\w:]+)',
        'num_macs': r'Num Macs: (\d+)',
        'module_sw_gen': r'Module Sw Gen: (\d+)',
        'switch_sw_gen': r'Switch Sw Gen: (\d+)',
        'post_level': r'Post level: (\w+)',
        'pinning_mode': r'Pinning-mode: (\w+)',
        'max_links': r'Max-links: (\d+)',
        'fabric_port_for_control_traffic':
        r'Fabric port for control traffic: (\w+/\d+)',
        'fcoe_admin': r'FCoE Admin: (\w+)',
        'fcoe_oper': r'FCoE Oper: (\w+)',
        'fcoe_fex_aa_configured': r'FCoE FEX AA Configured: (\w+)'
    }

    # Updated regex pattern to handle multiple 'Fabric interface state' values
    fabric_interface_pattern = \
        r'Fabric interface state:(.+?)(?=Fex Port|Logs|$)'

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Create a dictionary to store FEX data from devices.
    device_fexes = dict()

    df = pd.DataFrame()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]
            device_fexes[device] = list()

            data = event_data["res"]["stdout"][0]

            # Split the data into chunks for each FEX
            fex_chunks = [f"FEX:{chunk}" for chunk in re.split(
                r'FEX:', data) if chunk.strip() != ""]

            all_parsed_data = []

            for chunk in fex_chunks:
                # Parse the main data of each FEX
                parsed_data = {}
                for key, pattern in regex_patterns.items():
                    match = re.search(pattern, chunk)
                    if match:
                        parsed_data[key] = match.group(1)
                    else:
                        parsed_data[key] = None

                # Extract fabric interface state
                fabric_interface_state_match = re.search(
                    fabric_interface_pattern, chunk, re.DOTALL)
                if fabric_interface_state_match:
                    parsed_data['fabric_interface_state'] = \
                        fabric_interface_state_match.group(
                        1).strip().replace("\n", "; ")
                else:
                    parsed_data['fabric_interface_state'] = None

                all_parsed_data.append(parsed_data)

            # Convert to dataframe
            df_multi_fex = pd.DataFrame(all_parsed_data)
            df_multi_fex['device'] = device

            # Reorder the columns to make 'device' the first column
            column_order = ['device'] + \
                [col for col in df_multi_fex if col != 'device']
            df_multi_fex = df_multi_fex[column_order]

            df = pd.concat([df_multi_fex, df], ignore_index=True)

    return df


def nxos_parse_bgp_neighbors(runner: dict) -> pd.DataFrame:
    """
    Parse the BGP neighbors for all VRFs on NXOS devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_bgp : pd.DataFrame
        The BGP neighbors as a pandas DataFrame.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Necessary to keep from exceeding 80-character line length
    address = ipaddress.ip_address

    # Phrase to search for to find the start of VRF neighbors
    phrase = "BGP summary information for VRF"

    df_data = list()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]
            device = event_data["remote_addr"]
            output = event_data["res"]["stdout"][0].split("\n")
            for line in output:
                if phrase in line:
                    vrf = line.split(",")[0].split()[-1]
                    pos = output.index(line) + 1
                    if pos < len(output):
                        while phrase not in output[pos]:
                            try:
                                if address(output[pos].split()[0]):
                                    row = output[pos].split()
                                    df_data.append(
                                        [
                                            device,
                                            vrf,
                                            row[0],
                                            row[1],
                                            row[2],
                                            row[3],
                                            row[4],
                                            row[5],
                                            row[6],
                                            row[7],
                                            row[8],
                                            row[9],
                                        ]
                                    )
                            except Exception:
                                pass
                            pos += 1
                            if pos == len(output):
                                break

    # Create dataframe and return it
    cols = [
        "device",
        "vrf",
        "neighbor_id",
        "version",
        "as",
        "msg_received",
        "message_sent",
        "table_version",
        "in_q",
        "out_q",
        "up_down",
        "state_pfx_rfx",
    ]
    df_bgp = pd.DataFrame(data=df_data, columns=cols)
    return df_bgp


def nxos_parse_cam_table(runner: dict, nm_path: str) -> pd.DataFrame:
    """
    Parse the CAM table for NXOS devices and add the vendor OUI.

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

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Define the RegEx pattern for a valid MAC address
    # pattern = '([0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4})'
    pattern = ".*[a-zA-Z0-9]{4}\\.[a-zA-Z0-9]{4}\\.[a-zA-Z0-9]{4}.*"

    # Create a list to store MAC addresses
    addresses = list()

    # Parse the output and add it to 'data'
    df_data = list()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0]

            output = re.findall(pattern, output)
            for line in output:
                mac = line.split()[2]
                interface = line.split()[-1]
                vlan = line.split()[1]
                df_data.append([device, interface, mac, vlan])

    # Create the dataframe and return it
    cols = ["device", "interface", "mac", "vlan"]
    df_cam = pd.DataFrame(data=df_data, columns=cols)

    # Get the OUIs and add them to df_cam
    addresses = df_cam["mac"].to_list()
    df_vendors = hp.find_mac_vendors(addresses, nm_path)
    df_cam["vendor"] = df_vendors["vendor"]

    # Return df_cam
    return df_cam


def nxos_parse_hostname(runner: dict) -> pd.DataFrame:
    """
    Parse the hostname for NXOS devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_name : pd.DataFrame
        The hostname as a pandas DataFrame.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    df_data = dict()
    df_data["device"] = list()
    df_data["hostname"] = list()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0]

            df_data["device"].append(device)
            df_data["hostname"].append(output)

    # Create the dataframe and return it
    df_name = pd.DataFrame.from_dict(df_data)

    return df_name


def nxos_parse_interface_descriptions(runner: dict) -> pd.DataFrame:
    """
    Parse NXOS interface descriptions.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_desc : pd.DataFrame
        The interface descriptions as a pandas DataFrame.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Create a list to store the rows for the dataframe
    df_data = list()
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")
            output = list(filter(None, output))
            # NXOS does not have consistent column widths. Therefore, we must
            # re-index the position of the 'Description' column every time it
            # occurs.
            for _ in output:
                if ("Port" in _ or "Interface" in _) and "Description" in _:
                    pos = _.index("Description")
                else:
                    inf = _.split()[0]
                    desc = _[pos:].strip()
                    df_data.append([device, inf, desc])

    # Create the dataframe and return it
    cols = ["device", "interface", "description"]
    df_desc = pd.DataFrame(data=df_data, columns=cols)
    return df_desc


def nxos_parse_interface_ips(runner: dict) -> pd.DataFrame:
    """
    Parse the IP addresses assigned to interfaces.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the interfaces and their corresponding IP
        addresses.
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

            counter = 0
            for line in output:
                if "IP Interface Status for VRF" in line:
                    vrf = line.split()[-1].strip('"')

                if "IP address:" in line:
                    pos = counter
                    inf = output[pos - 1].split(",")[0]
                    ip = line.split(",")[0].split()[-1]
                    subnet = line.split(",")[1].split()[2].split("/")[-1]
                    ip = f"{ip}/{subnet}"
                    row = [device, inf, ip, vrf]
                    df_data.append(row)

                counter += 1

    # Create a dataframe from df_data and return it
    cols = ["device", "interface", "ip", "vrf"]
    df = pd.DataFrame(data=df_data, columns=cols)

    # Add the subnets, network IPs, and broadcast IPs.
    addresses = df["ip"].to_list()

    df['ip'] = [_.split('/')[0] for _ in df['ip'].to_list()]

    result = hp.generate_subnet_details(addresses)
    df["subnet"] = result["subnet"]
    df["network_ip"] = result["network_ip"]
    df["broadcast_ip"] = result["broadcast_ip"]

    # Add a column containing the CIDR notation.
    cidrs = hp.subnet_mask_to_cidr(df["subnet"].to_list())
    df['cidr'] = cidrs
    df = df[['device',
             'interface',
             'ip',
             'cidr',
             'vrf',
             'subnet',
             'network_ip',
             'broadcast_ip']]

    return df


def nxos_parse_interface_status(runner: dict) -> pd.DataFrame:
    """
    Parse the interface status for NXOS devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_inf_status : pd.DataFrame
        The interface statuses as a pandas DataFrame.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Parse the output and add it to 'data'
    df_data = list()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")
            output = list(filter(None, output))

            # Get the positions of the header columns (except Port and Name)
            header = output[0]
            pos_status = header.index("Status")
            pos_vlan = header.index("Vlan")
            pos_duplex = header.index("Duplex")
            pos_speed = header.index("Speed")
            pos_type = header.index("Type")

            # Remove lines that repeat the header
            output = [_ for _ in output if "Port" not in _ and "type" not in _]

            # Parse the output and add it to 'df_data'
            for line in output[1:]:
                inf = line.split()[0]
                status = line[pos_status:pos_vlan]
                vlan = line[pos_vlan:pos_duplex]
                duplex = line[pos_duplex:pos_speed]
                speed = line[pos_speed:pos_type]
                inf_type = line[pos_type:]
                row = [device, inf, status, vlan, duplex, speed, inf_type]
                row = [_.strip() for _ in row]
                df_data.append(row)

    # Create the dataframe and return it
    cols = ["device", "interface", "status", "vlan", "duplex", "speed", "type"]

    df_inf_status = pd.DataFrame(data=df_data, columns=cols)

    return df_inf_status


def nxos_parse_interface_summary(df_inf: pd.DataFrame,
                                 con, ts) -> pd.DataFrame:
    """
    Parse a summary of the interfaces on a NXOS devices. The summary includes
    the interface status, description, associated MACs, and vendor OUIs.

    Parameters
    ----------
    df_inf: pd.DataFrame
        DataFrame of the interfaces on a NXOS devices
    con: db connection
        db connection
    ts: timestamp
        timestamp

    Returns
    -------
    df_summary : pd.DataFrame
        The summaries of interfaces on the devices as a pandas DataFrame.
    """
    # Get the interface statuses, descriptions and cam table

    if df_inf is None or len(df_inf) == 0:
        raise ValueError("The input is None or empty")

    df_data = dict()
    df_data["device"] = list()
    df_data["interface"] = list()
    df_data["status"] = list()
    df_data["description"] = list()
    df_data["vendors"] = list()
    df_data["macs"] = list()

    for idx, row in df_inf.iterrows():
        device = row["device"]
        inf = row["interface"]
        status = row["status"]

        query = f'''SELECT mac,vendor
                    FROM nxos_cam_table
                    WHERE timestamp = "{ts}"
                       AND device = "{device}"
                       AND interface = "{inf}"'''
        df_macs = pd.read_sql(query, con)
        if len(df_macs) > 0:
            macs = df_macs["mac"].to_list()
            macs = "|".join(macs)

            vendors = list()
            for idx, row in df_macs.iterrows():
                vendor = row["vendor"]
                if vendor:
                    vendor = vendor.replace(",", str())
                    if vendor not in vendors:
                        vendors.append(vendor)

            vendors = "|".join(vendors)

            # vendors = str()
            # for idx, row in df_macs.iterrows():
            #     vendor = row['vendor']
            #     if len(vendors) == 0:
            #         if vendor:
            #             vendors = vendor
            #     elif vendor:
            #         if not vendors:
            #             vendors = vendor
            #         else:
            #             vendors = vendors + f' {vendor}'
            #     else:
            #         pass

        else:
            macs = str()
            vendors = str()

        query = f'''SELECT description
                    FROM nxos_interface_description
                    WHERE timestamp = "{ts}"
                       AND device = "{device}"
                       AND interface = "{inf}"'''
        desc = pd.read_sql(query, con)
        if len(desc) > 0:
            desc = desc["description"].to_list()[0]
        else:
            desc = str()

        df_data["device"].append(device)
        df_data["interface"].append(inf)
        df_data["status"].append(status)
        df_data["description"].append(desc)
        df_data["vendors"].append(vendors)
        df_data["macs"].append(macs)

    con.close()

    df_summary = pd.DataFrame.from_dict(df_data)
    df_summary = df_summary[
        ["device", "interface", "status", "description", "vendors", "macs"]
    ]

    return df_summary


def nxos_parse_inventory(runner: dict) -> pd.DataFrame:
    """
    Parse the inventory for NXOS devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_inventory : pd.DataFrame
        A DataFrame containing the output of the 'show inventory | json'
        command.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Create a list for holding the inventory items
    data = list()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]
            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0]["TABLE_inv"]["ROW_inv"]

            # Add the inventory items to the 'data' list
            for item in output:
                item["device"] = device
                data.append(item)

    # Create a dictionary for storing the output
    df_data = dict()

    # Create the dictionary keys
    for item in data:
        for key in item:
            if not df_data.get(key):
                df_data[key] = list()

    # Add the inventory items to 'df_data'
    for item in data:
        for key in df_data:
            df_data[key].append(item.get(key))

    # Create and return the dataframe
    df_inventory = pd.DataFrame.from_dict(df_data)

    return df_inventory


def nxos_parse_logs(runner: dict) -> pd.DataFrame:
    """
    Parse the latest log messages for NXOS devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_logs : pd.DataFrame
        The latest log messages as a pandas DataFrame.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Parse the output and add it to 'data'
    df_data = list()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")

            for line in output:
                _time = line[:21].strip()
                _msg = line[21:].strip()
                df_data.append([device, _time, _msg])

    # Create the dataframe and return it
    cols = ["device", "time", "message"]

    df_logs = pd.DataFrame(data=df_data, columns=cols)

    return df_logs


def nxos_parse_port_channel_data(runner: dict) -> pd.DataFrame:
    """
    Parse port-channel data (output from 'show port-channel database')
    for Cisco NXOS devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_po_data : pd.DataFrame
        The port-channel data as a pandas DataFrame.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Define the dataframe columns
    cols = [
        "device",
        "interface",
        "total_ports",
        "up_ports",
        "age",
        "port_1",
        "port_2",
        "port_3",
        "port_4",
        "port_5",
        "port_6",
        "port_7",
        "port_8",
        "first_operational_port",
        "last_bundled_member",
        "last_unbundled_member",
    ]

    # Create a dictionary to store the data for creating the dataframe
    df_data = dict()
    for c in cols:
        df_data[c] = list()

    # Parse the output and add it to 'data'
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")

            # output.append(str())  # For finding the end of database entries
            output = [_ for _ in output if _ != "Legend:"]
            output = [_ for _ in output if '"*":' not in _]

            # TODO: Re-write this using regex to 1) make it more concise, and
            # 2) avoid iterating over 'output' twice

            # Create a list to store database entries
            entries = list()

            pos = 0
            for line in output:
                if line[:12] == "port-channel":
                    interface = line
                    entry = [interface, device]
                    counter = pos + 1
                    while output[counter][:4] == "    ":
                        entry.append(output[counter])
                        counter += 1
                        if counter == len(output):
                            break
                    entries.append(entry)
                pos += 1

            for entry in entries:
                entry = [_.strip() for _ in entry]
                interface = entry[0]
                device = entry[1]
                # Create a counter for tracking port numbers
                counter = 0
                # Create an 8-element list of empty strings for ports
                ports = list()
                for i in range(1, 9):
                    ports.append(str())
                # Define empty strings for vars that might not exist
                total_ports = str()
                up_ports = str()
                first_op_port = str()
                last_bundled = str()
                last_unbundled = str()
                age = str()
                for line in entry[2:]:
                    if "ports in total" in line:
                        total_ports = line.split()[0]
                        up_ports = line.split(",")[-1].split()[0]
                    if "First operational" in line:
                        first_op_port = line.split()[-1]
                    if "Last bundled" in line:
                        last_bundled = line.split()[-1]
                    if "Last unbundled" in line:
                        last_unbundled = line.split()[-1]
                    if "Age of the" in line:
                        age = line.split()[-1]
                    if "]" in line:
                        port = line.split("Ports:")[-1].strip()
                        ports[counter] = port
                        counter += 1

                # Fill in ports list with ports that exist
                port_num = 1
                for p in ports:
                    key = f"port_{str(port_num)}"
                    df_data[key].append(p)
                    port_num += 1
                # Add remaining variables to df_data
                df_data["interface"].append(interface)
                df_data["device"].append(device)
                df_data["total_ports"].append(total_ports)
                df_data["up_ports"].append(up_ports)
                df_data["age"].append(age)
                df_data["first_operational_port"].append(first_op_port)
                df_data["last_bundled_member"].append(last_bundled)
                df_data["last_unbundled_member"].append(last_unbundled)

    df_po_data = pd.DataFrame.from_dict(df_data)
    # Set dataframe columns to desired order (from 'cols' list)
    df_po_data = df_po_data[cols]

    return df_po_data


def nxos_parse_vlan_db(runner: dict) -> pd.DataFrame:
    """
    Parse the VLAN database for NXOS devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_vlans : pd.DataFrame
        The VLAN database as a pandas DataFrame.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Parse the output and add it to 'data'
    df_data = list()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")

            # Get the position of "Ports" column
            pos = output[0].index("Ports")

            for line in output[1:]:
                v_id = line.split()[0]
                name = line.split()[1]
                status = line.split()[2]
                ports = line[pos:].strip()
                df_data.append([device, v_id, name, status, ports])

    # Create the dataframe and return it
    cols = ["device", "id", "name", "status", "ports"]

    df_vlans = pd.DataFrame(data=df_data, columns=cols)

    return df_vlans


def nxos_parse_vpc_state(runner: dict) -> pd.DataFrame:
    """
    Parse the VPC state for NXOS devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_vpc_state : pd.DataFrame
        The VPC state information as a pandas DataFrame.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Parse the output and add it to 'data'
    data = dict()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]
            device = event_data["remote_addr"]
            output = event_data["res"]["stdout"][0].split("\n")

            # Remove empty lines
            output = list(filter(None, output))
            # Remove 'vPC Peer-link status'
            output = [_ for _ in output if _ != "vPC Peer-link status"]

            data[device] = dict()
            data[device]["device"] = device
            for line in output:
                col_name = line.split(":")[0].strip()
                data[device][col_name] = line.split(":")[1].strip()

    df_data = dict()
    df_data["device"] = list()
    for key in data:
        for k in data[key]:
            df_data[k] = list()

    for device in data:
        for key in df_data:
            df_data[key].append(data[device].get(key))

    df_vpc_state = pd.DataFrame.from_dict(df_data)

    return df_vpc_state


def nxos_parse_vrfs(runner: dict) -> pd.DataFrame:
    """
    Parse the VRFs on Nexus devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner genrator

    Returns
    -------
    df_vrfs : pd.DataFrame
        A DataFrame containing the VRFs.
    """

    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Parse the output and add it to 'data'
    df_data = list()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")

            # Pre-define variables, since not all VRFs contain all parameters
            name = str()
            vrf_id = str()
            state = str()
            description = str()
            vpn_id = str()
            route_domain = str()
            max_routes = str()

            pos = 0
            for line in output:
                if "VRF-Name" in line:
                    pos = output.index(line) + 1
                    line = line.split(",")
                    line = [_.split(":")[-1].strip() for _ in line]
                    name = line[0]
                    vrf_id = line[1]
                    state = line[2]
                    while "Table-ID" not in output[pos]:
                        if "Description:" in output[pos]:
                            description = output[pos + 1].strip()
                        if "VPNID" in output[pos]:
                            vpn_id = output[pos].split(": ")[-1]
                        if "RD:" in output[pos]:
                            route_domain = output[pos].split()[-1]
                        if "Max Routes" in output[pos]:
                            _ = output[pos].split(": ")
                            max_routes = _[1].split()[0].strip()
                            min_threshold = _[-1]
                        pos += 1
                    row = [
                        device,
                        name,
                        vrf_id,
                        state,
                        description,
                        vpn_id,
                        route_domain,
                        max_routes,
                        min_threshold,
                    ]
                    df_data.append(row)

    # Create the DataFrame columns
    cols = [
        "device",
        "name",
        "vrf_id",
        "state",
        "description",
        "vpn_id",
        "route_domain",
        "max_routes",
        "min_threshold",
    ]

    # Create the dataframe and return it
    df_vrfs = pd.DataFrame(data=df_data, columns=cols)

    return df_vrfs
