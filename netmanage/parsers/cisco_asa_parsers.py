#!/usr/bin/env python3

import pandas as pd

from netmanage.helpers import helpers as hp


def asa_parse_interface_ips(runner: dict) -> pd.DataFrame:
    """
    Parses the interface IPs for Cisco ASA devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner generator.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the interface IP addresses.
    """
    # Parse the results
    df_data = list()
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            output = event_data["res"]["stdout"][0].split("\n")

            output = [_.strip("\t") for _ in output]

            output = [
                _
                for _ in output
                if _.split()[0] == "Interface"
                or " ".join(_.split()[:2]) == "IP address"
            ]

            counter = 0
            for line in output:
                counter += 1
                line = line.split(",")
                if line[0].split()[0] == "Interface" and '"' in line[0].split()[-1]:
                    inf = line[0].split()[1]
                    nameif = line[0].split()[2].strip('"')

                    _line = output[counter]
                    if "unassigned" in _line:
                        ip = "unassigned"
                        netmask = "unassigned"
                    else:
                        ip = _line.split(",")[0].split()[-1]
                        netmask = _line.split(",")[-1].split()[-1]
                        cidr = hp.convert_mask_to_cidr(netmask)
                        ip = f"{ip}/{cidr}"

                    row = [device, inf, ip, cidr, nameif]
                    df_data.append(row)
    # Create a dataframe from df_data and return it
    cols = ["device", "interface", "ip", "cidr", "nameif"]
    df = pd.DataFrame(data=df_data, columns=cols)

    # Filter out interfaces that do not have an IP address.
    df = df[df["ip"] != "unassigned"]

    # Add the subnets, network IPs, and broadcast IPs.
    addresses = df["ip"].to_list()
    result = hp.generate_subnet_details(addresses)
    df["subnet"] = result["subnet"]
    df["network_ip"] = result["network_ip"]
    df["broadcast_ip"] = result["broadcast_ip"]

    return df


def asa_parse_inventory(runner: dict) -> pd.DataFrame:
    """
    Parses the inventory for Cisco ASA devices.

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
    columns = ["device", "name", "description", "pid", "vid", "serial", "ip"]
    df_data = dict()
    for col in columns:
        df_data[col] = list()

    # Parse the output and add it to 'df_data'
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]
            device_ip = hp.ansible_host_to_ip(device)

            data = event_data["res"]["stdout"][0].split("\n")

            # Iterate through data (each hardware entry has 3 lines).
            for i in range(0, len(data), 3):
                df_data["device"].append(device)
                df_data["ip"].append(device_ip)
                # Split the first line to extract name and description
                name_desc = data[i].split(", DESCR: ")
                df_data["name"].append(
                    name_desc[0]
                    .replace('NAME: "', "")
                    .replace("Name: ", "")
                    .replace('"', "")
                    .strip()
                )
                df_data["description"].append(name_desc[1].replace('"', "").strip())

                # Split the second line to extract PID, VID and SN
                pid_vid_sn = data[i + 1].split(", ")
                df_data["pid"].append(pid_vid_sn[0].replace("PID: ", "").strip())
                df_data["vid"].append(pid_vid_sn[1].replace("VID: ", "").strip())

                # If SN value is "SN:", replace with an empty string.
                sn_value = pid_vid_sn[2].replace("SN: ", "").strip()
                if sn_value == "SN:":
                    sn_value = ""
                df_data["serial"].append(sn_value)

    # Create the DataFrame and return it.
    df = pd.DataFrame(df_data)

    return df


def asa_parse_gather_basic_facts(results: dict) -> pd.DataFrame:
    """
    Parses the results from cisco_asa_collectors.basic_facts.

    Parameters
    ----------
    results : dict
        A dictionary containing the results from
        cisco_asa_collectors.gather_basic_facts.

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
