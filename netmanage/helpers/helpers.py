#!/usr/bin/env python3

"""
A library of generic helper functions.
"""

import ansible_runner
import glob
import ipaddress
import nmap
import numpy as np
import os
import pandas as pd
import re
import requests
import sqlite3 as sl
import sys
import time
import yaml
import json
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime as dt
from getpass import getpass
from tabulate import tabulate
from typing import Any, Dict, List, Tuple, Union


def ansible_create_collectors_df(
    hostgroups: List[str], collectors: List[str]
) -> pd.DataFrame:
    """
    Create a DataFrame where the index is the selected collectors and each row
    contains a comma-delimited string of selected hostgroups.

    Parameters
    ----------
    hostgroups : list of str
        A list of hostgroups, each of which is a comma-delimited string.
    collectors : list of str
        A list of one or more collectors, each of which is a comma-delimited
        string.

    Returns
    -------
    df_collectors : pd.DataFrame
        A DataFrame created from hostgroups and collectors.

    Examples
    --------
    >>> hostgroups = ['hostgroup1', 'hostgroup2']
    >>> collectors = ['collector1', 'collector2']
    >>> df_collectors = ansible_create_collectors_df(hostgroups, collectors)
    >>> print(df_collectors)
    """
    df_data = list()
    for c in collectors:
        df_data.append([c, ",".join(hostgroups)])
        df_collectors = pd.DataFrame(data=df_data, columns=["collector", "hostgroups"])
    df_collectors = df_collectors.set_index("collector")

    return df_collectors


def ansible_create_vars_df(
    hostgroups: List[str], private_data_dir: str
) -> pd.DataFrame:
    """
    Create a DataFrame containing the Ansible variables for each hostgroup.

    This function is designed to be used with the net-manage.ipynb. It reads
    all the host groups from the 'df_test', gets the Ansible variables for each
    group from the host file, creates a DataFrame containing the variables,
    then returns it.

    Parameters
    ----------
    hostgroups : list of str
        A list of hostgroups.
    private_data_dir : str
        The path to the Ansible private_data_dir, which is the directory
        containing the 'inventory' folder. The default is the current folder.

    Returns
    -------
    df_vars : pd.DataFrame
        A DataFrame containing the group variables.

    Examples
    --------
    >>> hostgroups = ['group1', 'group2']
    >>> private_data_dir = '/path/to/private/data/dir'
    >>> df_vars = ansible_create_vars_df(hostgroups, private_data_dir)
    >>> print(df_vars)
    """
    host_vars = dict()

    for g in hostgroups:
        group_vars = ansible_get_host_variables(g, private_data_dir)
        host_vars[g] = group_vars

    # Create a dictionary to store the variable data for each group
    df_data = dict()
    df_data["host_group"] = list()

    # Iterate through the keys for each group in 'host_vars', adding it as a
    # key to 'df_data'
    for key, value in host_vars.items():
        for k in value:
            if k != "ansible_user" and k != "ansible_password":
                df_data[k] = list()

    # Iterate through 'host_vars', populating 'df_data'
    for key, value in host_vars.items():
        df_data["host_group"].append(key)
        for item in df_data:
            if item != "host_group":
                result = value.get(item)
                df_data[item].append(result)

    df_vars = pd.DataFrame.from_dict(df_data)

    df_vars = df_vars.set_index("host_group")

    return df_vars


def ansible_get_all_hostgroup_os(private_data_dir: str) -> Dict[str, str]:
    """
    Get the Ansible OS for every hostgroup.

    Parameters
    ----------
    private_data_dir : str
        The path to the Ansible private_data_dir. This is the directory
        containing the 'inventory' folder. The default is the current folder.

    Returns
    -------
    groups_os : dict
        The Ansible OS for all host groups. The keys are host group names and
        the values are the corresponding Ansible OS.

    Examples
    --------
    >>> private_data_dir = '/path/to/private/data/dir'
    >>> groups_os = ansible_get_all_hostgroup_os(private_data_dir)
    >>> print(groups_os)
    """
    # Get all group variables
    groups_vars = ansible_get_all_host_variables(private_data_dir)

    groups_os = dict()

    for key, value in groups_vars.items():
        group_vars = value.get("vars")
        if group_vars and group_vars.get("ansible_network_os"):
            groups_os[key] = value["vars"]["ansible_network_os"]

    return groups_os


def ansible_get_all_host_variables(private_data_dir: str) -> Dict[str, str]:
    """
    Get the Ansible variables for all hostgroups in the inventory.

    Parameters
    ----------
    private_data_dir : str
        The path to the Ansible private_data_dir. This is the directory
        containing the 'inventory' folder. The default is the current folder.

    Returns
    -------
    groups_vars : dict
        The Ansible variables for all host groups. The keys are host group
        names and the values are the corresponding Ansible variables.

    Examples
    --------
    >>> private_data_dir = '/path/to/private/data/dir'
    >>> groups_vars = ansible_get_all_host_variables(private_data_dir)
    >>> print(groups_vars)
    """
    # Read the contents of the playbook into a dictionary
    with open(f"{private_data_dir}/inventory/hosts") as f:
        groups_vars = yaml.load(f, Loader=yaml.FullLoader)
    return groups_vars


def check_dir_existence(dir_path: str) -> bool:
    """
    Check whether a directory exists.

    Parameters
    ----------
    dir_path : str
        The path to the directory.

    Returns
    -------
    exists : bool
        A boolean to indicate whether the directory exists.

    Examples
    --------
    >>> dir_path = '/path/to/directory'
    >>> exists = check_dir_existence(dir_path)
    >>> print(exists)
    """
    exists = False
    if os.path.exists(dir_path):
        exists = True
    return exists


def convert_mask_to_cidr(netmask: str) -> str:
    """
    Convert a subnet mask to CIDR notation.

    Parameters
    ----------
    netmask : str
        A subnet mask in xxx.xxx.xxx.xxx format.

    Returns
    -------
    cidr : str
        The number of bits in the subnet mask (CIDR).

    Examples
    --------
    >>> netmask = '255.255.255.0'
    >>> cidr = convert_mask_to_cidr(netmask)
    >>> print(cidr)
    """
    cidr = sum(bin(int(x)).count("1") for x in netmask.split("."))
    return cidr


def create_dir(dir_path: str) -> None:
    """
    Create a directory.

    Parameters
    ----------
    dir_path : str
        The path to the directory.

    Returns
    -------
    None

    Examples
    --------
    >>> dir_path = '/path/to/new/directory'
    >>> create_dir(dir_path)
    """
    os.mkdir(dir_path)


def define_supported_validation_tables() -> List[str]:
    """
    Return a list of tables that are supported for validation.

    Returns
    -------
    supported_tables : list
        A list of supported tables.

    Examples
    --------
    >>> supported_tables = define_supported_validation_tables()
    >>> print(supported_tables)
    """
    supported_tables = dict()

    supported_tables["MERAKI_ORG_DEVICE_STATUSES"] = dict()
    supported_tables["MERAKI_ORG_DEVICE_STATUSES"]["status"] = "online"

    supported_tables["BIGIP_POOL_AVAILABILITY"] = dict()
    supported_tables["BIGIP_POOL_AVAILABILITY"]["availability"] = "available"

    supported_tables["BIGIP_POOL_MEMBER_AVAILABILITY"] = dict()
    supported_tables["BIGIP_POOL_MEMBER_AVAILABILITY"][
        "pool_member_state"
    ] = "available"

    supported_tables["BIGIP_VIP_AVAILABILITY"] = dict()
    supported_tables["BIGIP_VIP_AVAILABILITY"]["availability"] = "available"

    return supported_tables


def get_database_tables(db_path: str) -> List[str]:
    """
    Get all of the tables out of the database.

    Parameters
    ----------
    db_path : str
        The path to the database.

    Returns
    -------
    tables : list
        A list of tables.

    Examples
    --------
    >>> db_path = '/path/to/database'
    >>> tables = get_database_tables(db_path)
    >>> print(tables)
    """
    # sqlite_schema used to be named sqlite_master. This method tries the new
    # name but will fail back to the old name if the user is on an older
    # version
    name_old = "master"
    name_new = "schema"
    con = connect_to_db(db_path)
    query1 = f'''select name from sqlite_{name_new}
                 where type = "table" and name not like "sqlite_%"'''
    query2 = f'''select name from sqlite_{name_old}
                 where type = "table" and name not like "sqlite_%"'''
    try:
        df_tables = pd.read_sql(query1, con)
    except Exception:
        df_tables = pd.read_sql(query2, con)
    tables = df_tables["name"].to_list()
    return tables


def get_database_views(db_path: str) -> List[str]:
    """
    Get all of the views out of the database.

    Parameters
    ----------
    db_path : str
        The path to the database.

    Returns
    -------
    views : list
        A list of views.

    Examples
    --------
    >>> db_path = '/path/to/database'
    >>> views = get_database_views(db_path)
    >>> print(views)
    """
    # sqlite_schema used to be named sqlite_master. This method tries the new
    # name but will fail back to the old name if the user is on an older
    # version
    name_old = "master"
    name_new = "schema"
    con = connect_to_db(db_path)
    query1 = f'''select name from sqlite_{name_new}
                 where type = "view" and name not like "sqlite_%"'''
    query2 = f'''select name from sqlite_{name_old}
                 where type = "view" and name not like "sqlite_%"'''
    try:
        df_views = pd.read_sql(query1, con)
    except Exception:
        df_views = pd.read_sql(query2, con)
    views = df_views["name"].to_list()
    return views


def ansible_get_hostgroup() -> str:
    """
    Get the Ansible hostgroup.

    Returns
    -------
    hostgroup : str
        The Ansible hostgroup.

    Examples
    --------
    >>> hostgroup = ansible_get_hostgroup()
    >>> print(hostgroup)
    """

    host_group = input("Enter the name of the host group in the hosts file: ")
    return host_group


def ansible_get_host_variables(host_group: str, private_data_dir: str) -> Dict:
    """
    Get the variables for a host or host group in the hosts file.

    Parameters
    ----------
    host_group : str
        The name of the host group.
    private_data_dir : str
        The path to the Ansible private_data_dir. This is the path that
        the 'inventory' folder is in. The default is the current folder.

    Returns
    -------
    group_vars : dict
        The host group variables.

    Examples
    --------
    >>> host_group = '<host_group>'
    >>> private_data_dir = '/path/to/private/data/dir'
    >>> group_vars = ansible_get_host_variables(host_group, private_data_dir)
    >>> print(group_vars)
    """
    # Read the contents of the playbook into a dictionary
    with open(f"{private_data_dir}/inventory/hosts") as f:
        hosts = yaml.load(f, Loader=yaml.FullLoader)

    group_vars = hosts[host_group]["vars"]

    return group_vars


def ansible_get_hostgroup_devices(
    hostgroup: str, host_files: List[str], quiet: bool = True
) -> List[str]:
    """
    Get the devices inside an Ansible inventory hostgroup.

    Parameters
    ----------
    hostgroup : str
        The Ansible hostgroup.
    host_files : list
        The path to one or more Ansible host files (e.g., ['inventory/hosts']).
    quiet : bool, optional
        Whether to output the entire graph. Defaults to True.

    Returns
    -------
    devices : list
        A list of devices in the hostgroup.

    Examples
    --------
    >>> hostgroup = '<hostgroup>'
    >>> host_files = ['inventory/hosts']
    >>> devices = ansible_get_hostgroup_devices(hostgroup, host_files)
    >>> print(devices)
    """
    graph = ansible_runner.interface.get_inventory("graph", host_files, quiet=True)
    graph = str(graph)
    for item in graph.split("@"):
        if hostgroup in item:
            item = item.split(":")[-1]
            item = item.split("|--")[1:-1]
            devices = [i.split("\\")[0] for i in item]
            break
    return devices


def ansible_group_hostgroups_by_os(private_data_dir: str) -> Dict[str, List[str]]:
    """
    Finds the ansible_network_os for all hostgroups that have defined it in the
    variables, then organizes the hostgroups by os.

    For example:

    groups_os['cisco.asa.asa'] = ['asa_group_1']
    groups_os['cisco.nxos.nxos'] = ['nxos_group_1', 'nxos_group_2']

    Parameters
    ----------
    private_data_dir : str
        The path to the Ansible private_data_dir. This is the path that the
        'inventory' folder is in. The default is the current folder.

    Returns
    -------
    hostgroup_by_os : dict
        A dictionary containing the hostgroups, grouped by OS.

    Examples
    --------
    >>> private_data_dir = '<private_data_dir>'
    >>> hostgroup_by_os = ansible_group_hostgroups_by_os(private_data_dir)
    >>> print(hostgroup_by_os)
    """
    # Get the OS for all Ansible hostgroups
    groups_os = ansible_get_all_hostgroup_os(private_data_dir)

    # Extract the OS and create dict for all hostgroups that have defined it
    groups_by_os = dict()
    for key, value in groups_os.items():
        if not groups_by_os.get(value):
            groups_by_os[value] = list()
        groups_by_os[value].append(key)
    return groups_by_os


def define_collectors(hostgroup: str) -> Dict[str, Any]:
    """
    Creates a list of collectors.

    Parameters
    ----------
    hostgroup : str
        The name of the hostgroup.

    Returns
    -------
    available : dict
        The collectors supported by the hostgroup.

    Examples
    --------
    >>> hostgroup = '<hostgroup>'
    >>> available = define_collectors(hostgroup)
    >>> print(available)
    """
    # TODO: Find a more dynamic way to create this dictionary
    collectors = {
        "arp_table": [
            "bigip",
            "cisco.ios.ios",
            "cisco.nxos.nxos",
            "paloaltonetworks.panos",
        ],
        "basic_facts": [
            "cisco.asa.asa",
            "cisco.ios.ios",
            "cisco.nxos.nxos",
            "paloaltonetworks.panos",
        ],
        "bgp_neighbors": ["cisco.ios.ios", "cisco.nxos.nxos", "paloaltonetworks.panos"],
        "cam_table": ["cisco.ios.ios", "cisco.nxos.nxos"],
        "cdp_neighbors": ["cisco.ios.ios", "cisco.nxos.nxos"],
        "config": ["cisco.ios.ios"],
        "devices_inventory": ["cisco.dnac"],
        "device_cdp_lldp_neighbors": ["meraki"],
        "devices_modules": ["cisco.dnac"],
        "fexes_table": ["cisco.nxos.nxos"],
        "hardware_inventory": [
            "bigip",
            "cisco.asa.asa",
            "cisco.ios.ios",
            "cisco.nxos.nxos",
            "paloaltonetworks.panos",
        ],
        "infoblox_get_network_containers": ["nios"],
        "infoblox_get_network_parent_containers": ["nios"],
        "infoblox_get_networks": ["nios"],
        "infoblox_get_vlan_ranges": ["nios"],
        "infoblox_get_vlans": ["nios"],
        "lldp_neighbors": ["cisco.nxos.nxos"],
        "logs": ["bigip"],
        "ncm_serial_numbers": ["solarwinds"],
        "network_appliance_vlans": ["meraki"],
        "npm_containers": ["solarwinds"],
        "npm_group_members": ["solarwinds"],
        "npm_group_names": ["solarwinds"],
        "npm_node_ids": ["solarwinds"],
        "npm_node_ips": ["solarwinds"],
        "npm_node_machine_types": ["solarwinds"],
        "npm_node_os_versions": ["solarwinds"],
        "npm_node_vendors": ["solarwinds"],
        "npm_nodes": ["solarwinds"],
        "ospf_neighbors": ["cisco.ios.ios", "paloaltonetworks.panos"],
        "node_availability": ["bigip"],
        "pool_availability": ["bigip"],
        "pool_member_availability": ["bigip"],
        "pool_summary": ["bigip"],
        "panorama_managed_devices": ["paloaltonetworks.panos"],
        "self_ips": ["bigip"],
        "appliance_uplink_statuses": ["meraki"],
        "vip_availability": ["bigip"],
        "vip_destinations": ["bigip"],
        #  'vip_summary': ['bigip'],
        "vlans": ["bigip", "cisco.ios.ios", "cisco.nxos.nxos", "infoblox_nios"],
        "networks": ["infoblox_nios"],
        "network_containers": ["infoblox_nios"],
        "networks_parent_containers": ["infoblox_nios"],
        "vlan_ranges": ["infoblox_nios"],
        "interface_description": ["bigip", "cisco.ios.ios", "cisco.nxos.nxos"],
        "interface_ip_addresses": [
            "cisco.asa.asa",
            "cisco.ios.ios",
            "cisco.nxos.nxos",
            "paloaltonetworks.panos",
        ],
        "interface_ipv6_addresses": ["cisco.ios.ios"],
        "interface_status": ["cisco.nxos.nxos"],
        "interface_summary": ["bigip", "cisco.nxos.nxos"],
        "network_clients": ["meraki"],
        "network_devices": ["meraki"],
        "network_device_statuses": ["meraki"],
        "organizations": ["meraki"],
        "org_devices": ["meraki"],
        "org_device_statuses": ["meraki"],
        "org_networks": ["meraki"],
        "security_rules": ["paloaltonetworks.panos"],
        "switch_port_statuses": ["meraki"],
        "switch_lldp_neighbors": ["meraki"],
        "switch_port_usages": ["meraki"],
        "appliance_ports": ["meraki"],
        "switch_ports": ["meraki"],
        "ipam_prefixes": ["netbox"],
        "all_interfaces": ["paloaltonetworks.panos"],
        "logical_interfaces": ["paloaltonetworks.panos"],
        "physical_interfaces": ["paloaltonetworks.panos"],
        "port_channel_data": ["cisco.nxos.nxos"],
        "vpc_state": ["cisco.nxos.nxos"],
        "vrfs": ["cisco.ios.ios", "cisco.nxos.nxos"],
    }

    available = list()
    for key, value in collectors.items():
        if hostgroup in value:
            available.append(key)
    return available


def f5_create_authentication_token(
    device: str,
    username: str,
    password: str,
    loginProviderName: str = "tmos",
    verify: bool = True,
) -> str:
    """
    Creates an authentication token to use for F5 REST API calls.

    Parameters
    ----------
    device : str
        The device name or IP address.
    username : str
        The user's username.
    password : str
        The user's password.
    loginProviderName : str, optional
        The value to use for 'loginProviderName'. Defaults to 'tmos'.
        It should only need to be changed if F5 documentation or support
        says it is necessary.
    verify : bool, optional
        Whether to verify certs. Defaults to 'True'. Should only be set
        to 'False' if it is a dev environment or the F5 is using
        self-signed certificates.

    Returns
    -------
    token : str
        The authentication token.
    """
    # Create the URL used for creating the authentication token
    url = f"{device}/mgmt/shared/authn/login"

    # Request the token
    content = {
        "username": username,
        "password": password,
        "loginProviderName": loginProviderName,
    }
    response = requests.post(url, json=content, verify=verify)
    token = response.json()["token"]["token"]

    # Sleep for 1.5 seconds. This is required due to F5 bug ID1108181
    # https://cdn.f5.com/product/bugtracker/ID1108181.html
    time.sleep(1.5)

    # Return the token
    return token


def find_mac_vendors(macs: List[str], nm_path: str) -> pd.DataFrame:
    """
    Finds the vendor OUI for a list of MAC addresses.

    Parameters
    ----------
    macs : list
        A list containing the MAC addresses for which to find the OUIs.
    nm_path : str
        The path to the Net-Manage repository.

    Returns
    -------
    df : DataFrame
        A Pandas DataFrame containing two columns. The first is the MAC
        address, and the second is the corresponding vendor.

    Notes
    -----
    There is a Python library to do this, but it is quite slow.

    It might seem inefficient to parse the OUIs from a text file on an
    as-needed basis. However, testing found that the operation only takes
    about 250ms, and the size of the resulting dataframe is only
    approximately 500KB.

    Examples
    --------
    >>> import os
    >>> macs = ['00:50:56:bd:52:79', 'c4:34:6b:b9:99:32']
    >>> home_dir = os.path.expanduser('~')
    >>> nm_path = f'{home_dir}/source/repos/InsightSSG/Net-Manage'
    >>> df = find_mac_vendors(macs, nm_path)
    >>> print(df.to_dict())
    {'mac': {0: '00:50:56:bd:52:79', 1: 'c4:34:6b:b9:99:32'},
    'vendor': {0: 'VMware, Inc.', 1: 'Hewlett Packard'}}
    """
    # Convert MAC addresses to base 16 by removing special characters.
    addresses = ["".join(filter(str.isalnum, _)).upper() for _ in macs]

    # Create a list to store vendors
    vendors = list()

    # Check if the list of OUIs exists and/or needs to be updated.
    df_ouis = update_ouis(nm_path)

    # Search df_ouis for the vendor and add it to 'vendors'.
    for address in addresses:
        vendor = df_ouis.loc[df_ouis["base"] == address[:6]]["vendor"]
        if len(vendor) >= 1:
            vendors.append(vendor.squeeze())
        else:
            vendors.append("unknown")

    # Create the dataframe.
    df = pd.DataFrame()
    df["mac"] = macs
    df["vendor"] = vendors

    return df


def generate_subnet_details(
    addresses: List[str],
    return_keys: List[str] = ["subnet", "network_ip", "broadcast_ip", "subnet_mask"],
) -> Dict[str, List[str]]:
    """Generates the subnet, network, and broadcast IPs for a list of IPs.

    Parameters
    ----------
    addresses : list of str
        List of IP addresses in the format {ip}/{subnet_mask_length} or
        {ip} {subnet_mask}.
    return_keys : list of str, optional
        List of keys to return.

    Returns
    -------
    dict
        A dictionary with details about each IP address.
    """
    subnet = []
    network_ip = []
    broadcast_ip = []
    subnet_mask = []

    for ip in addresses:
        if " " in ip:  # For 'IP SUBNET_MASK' format
            ip_address, mask = ip.split()
            ip_obj = ipaddress.ip_interface(
                f'{ip_address}/{ipaddress.IPv4Network("0.0.0.0/"+mask).prefixlen}'
            )
        else:  # For 'IP/SUBNET_MASK_LENGTH' format
            ip_obj = ipaddress.ip_interface(ip)

        subnet.append(str(ip_obj.network))
        network_ip.append(str(ip_obj.network.network_address))
        brd = str(ipaddress.IPv4Address(int(ip_obj.network.broadcast_address)))
        broadcast_ip.append(brd)
        mask = str(ip_obj.netmask)
        subnet_mask.append(mask)

    return {
        return_keys[0]: subnet_mask,
        return_keys[1]: network_ip,
        return_keys[2]: broadcast_ip,
    }


def get_creds(prompt: str = "") -> Tuple[str, str]:
    """
    Gets the username and password to use for authentication.

    Parameters
    ----------
    prompt : str, optional
        A one-word description to use inside the prompt. For example, if
        prompt == 'device', then the user would be presented with the full
        prompt of 'Enter the username to use for device authentication.' If no
        prompt is passed to the function, then the generic prompt will be used.
        Defaults to ''.

    Returns
    -------
    username : str
        The username.
    password : str
        The password.
    """
    username = get_username(prompt)
    password = get_password(prompt)
    return username, password


def ansible_get_hostgroups(inventories: List[str], quiet: bool = True) -> List[str]:
    """
    Gets the devices inside an Ansible inventory hostgroup.

    Parameters
    ----------
    inventories : list of str
        The path to one or more Ansible host files (e.g.,
        ['inventory/hosts']).
    quiet : bool, optional
        Whether to output the entire graph. Defaults to True.

    Returns
    -------
    devices : list of str
        A list of devices in the hostgroup.
    """
    graph = ansible_runner.interface.get_inventory("graph", inventories, quiet=True)
    graph = str(graph).strip("('")
    # graph = list(filter(None, graph))
    hostgroups = list()
    graph = list(filter(None, graph.split("@")))
    # TODO: Write a better parser
    for item in graph:
        hostgroup = item.split(":")[0]
        hostgroups.append(hostgroup)
    return hostgroups


def connect_to_db(db: str) -> sl.Connection:
    """
    Opens a connection to the sqlite database.

    Parameters
    ----------
    db : str
        Path to the database

    Returns
    -------
    con : sl.Connection
        Connection to the database
    """
    try:
        con = sl.connect(db)
    except Exception as e:
        if str(e) == "unable to open database file":
            print(f'Cannot connect to db "{db}". Does directory exist?')
            sys.exit()
        else:
            print(f'Caught exception "{str(e)}"')
            sys.exit()
    return con


def create_sqlite_regexp_function(conn: sl.Connection) -> None:
    """
    Creates a SQLite3 function that allows REGEXP queries. More details can be
    found at the following URLs:
    - 'https://tinyurl.com/mwxz2dn8'
    - 'https://tinyurl.com/ye285mnj'

    Parameters
    ----------
    conn : sqlite3.Connection
        An object for connecting to the sqlite3 database.

    Returns
    -------
    None
    """

    # This function is credited to Stack Overflow user 'unutbu':
    # - https://tinyurl.com/ye285mnj
    def regexp(expr, item):
        reg = re.compile(expr)
        return reg.search(item) is not None

    conn.create_function("REGEXP", 2, regexp)
    conn.commit()


def get_dir_timestamps(path: str) -> Dict[str, dt]:
    """
    Gets the timestamp for all files and folders in a directory.

    This function is not recursive.

    Parameters
    ----------
    path : str
        The path to search.

    Returns
    -------
    result : dict
        A dictionary for each file or folder, where the key is the file or
        folder name and the value is a datetime object containing the
        timestamp.

    Examples
    --------
    >>> from pprint import pprint
    >>> path = '/tmp/test/'
    >>> result = get_dir_timestamps(path)
    >>> pprint(result)
    {'/tmp/test/test.txt': datetime.datetime(2023, 3, 7, 16, 15, 9),
    '/tmp/test/test2.txt': datetime.datetime(2023, 3, 7, 16, 16, 4)}
    """
    files = glob.glob(f"{path}/*")

    result = dict()
    for file in files:
        ts = time.ctime(os.path.getctime(file)).split()
        ts = " ".join([ts[1], ts[2], ts[-1], ts[3]])
        result[file] = dt.strptime(ts, "%b %d %Y %H:%M:%S")

    return result


def get_first_last_timestamp(db_path: str, table: str, col_name: str) -> pd.DataFrame:
    """
    Gets the first and last timestamp from a database table for each unique
    entry in a column.

    Parameters
    ----------
    db_path : str
        The path to the database.
    table : str
        The table name.
    col_name : str
        The column name to search by (e.g., 'device', 'networkId', etc).

    Returns
    -------
    df_stamps : DataFrame
        A DataFrame containing the first and last timestamp for each unique
        entry in the specified column.
    """
    df_data = dict()
    df_data[col_name] = list()
    df_data["first_ts"] = list()
    df_data["last_ts"] = list()

    # Get the unique entries for col_name (usually a device name, MAC address,
    # etc). This is necessary since the first timestamp in the table won't
    # always have all the entries for that table (devices might be added or
    # removed, ARP tables might change, and so on)
    con = sl.connect(db_path)
    query = f"select distinct {col_name} from {table}"
    df_uniques = pd.read_sql(query, con)
    uniques = df_uniques[col_name].to_list()

    # Create a dictionary to store the first and last timestamps for col_name.
    # This will be used to create df_stamps
    # df_data = dict()

    query = f"select distinct timestamp from {table}"
    timestamps = pd.read_sql(query, con)["timestamp"].to_list()

    for unique in uniques:
        stamps = list()
        for ts in timestamps:
            query = f'''select timestamp from {table}
                        where timestamp = "{ts}" and {col_name} = "{unique}"'''
            for item in pd.read_sql(query, con)["timestamp"].to_list():
                stamps.append(item)
        df_data[col_name].append(unique)
        df_data["first_ts"].append(stamps[0])
        df_data["last_ts"].append(stamps[-1])

    # This is an alternative way to collect the first and last timestamps for
    # each col_name. It does not utilize an index (assuming the table has one),
    # but the speed was about the same. I am leaving it here to do more
    # testing with in the future.

    # for unique in uniques:
    #     query = f'''select distinct timestamp from {table}
    #                 where {col_name} = "{unique}"'''
    #     df_stamps = pd.read_sql(query, con)
    #     stamps = df_stamps['timestamp'].to_list()
    #     df_data[col_name].append(unique)
    #     df_data['first_ts'].append(stamps[0])
    #     df_data['last_ts'].append(stamps[-1])
    con.close()

    df_stamps = pd.DataFrame.from_dict(df_data)

    return df_stamps


def get_username(prompt: str = "") -> str:
    """
    Gets the username to use for authentication.

    Parameters
    ----------
    prompt : str, optional
        A one-word description to use inside the prompt. For example, if
        prompt == 'device', then the user would be presented with the full
        prompt of 'Enter the username to use for device authentication.' If
        no prompt is passed to the function, then the generic prompt will be
        used. Default is an empty string.

    Returns
    -------
    username : str
        The username.
    """
    # Create the full prompt
    if not prompt:
        f_prompt = "Enter the username to use for authentication: "
    else:
        f_prompt = f"Enter the username to use for {prompt} authentication: "

    # Get the user's username
    username = input(f_prompt)

    return username


def get_password(prompt: str = "") -> str:
    """
    Gets the password to use for authentication.

    Parameters
    ----------
    prompt : str, optional
        A one-word description to use inside the prompt. For example, if
        prompt == 'device', then the user would be presented with the full
        prompt of 'Enter the username to use for device authentication.' If
        no prompt is passed to the function, then the generic prompt will be
        used. Default is an empty string.

    Returns
    -------
    password : str
        The password.
    """
    # Create the full prompt
    if not prompt:
        f_prompt = "Enter the password to use for authentication: "
    else:
        f_prompt = f"Enter the password to use for {prompt} authentication: "

    # Get the user's password and have them type it twice for verification
    pass1 = str()
    pass2 = None
    while pass1 != pass2:
        pass1 = getpass(f_prompt)
        pass2 = getpass("Confirm your password: ")
        if pass1 != pass2:
            print("Error: Passwords do not match.")
    password = pass1

    return password


def meraki_get_api_key() -> str:
    """
    Gets the Meraki API key.

    Returns
    -------
    api_key : str
        The user's API key.
    """
    api_key = getpass("Enter your Meraki API key: ")
    return api_key


def move_cols_to_end(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    Moves one or more columns on a dataframe to be the end. For example,
    if the dataframe columns are ['A', 'C', 'B'], then this function can be
    used to re-order them to ['A', 'B', 'C'].

    Parameters
    ----------
    df : pd.DataFrame
        The Pandas dataframe to re-order.
    cols : list of str
        A list of one or more columns to move. If more than one column is
        specified, they will be added to the end in the order that is in
        the list.

    Returns
    -------
    pd.DataFrame
        The re-ordered DataFrame.
    """
    for c in cols:
        df[c] = df.pop(c)
    return df


def read_table(db_path: str, table: str) -> pd.DataFrame:
    """
    Reads all columns for the latest timestamp from a database table.

    Parameters
    ----------
    db_path : str
        The full path to the database.
    table : str
        The table name.

    Returns
    -------
    df : pd.DataFrame
        A Pandas dataframe containing the data.
    """
    con = connect_to_db(db_path)
    df_ts = pd.read_sql(f"select timestamp from {table} limit 1", con)
    ts = df_ts["timestamp"].to_list()[-1]
    df = pd.read_sql(f'select * from {table} where timestamp = "{ts}"', con)
    con.close()
    return df


def scan_targets(targets: list, max_threads: int = 10) -> dict:
    """
    Use nmap to perform a ping scan on a list of targets.

    Parameters
    ----------
    targets : list
        A list of target subnets or IP addresses.
    max_threads : int, optional
        Maximum number of parallel threads, by default 10.

    Returns
    -------
    dict
        A dictionary with target as the key and list of alive hosts as the
        value.

    Examples
    --------
    >>> targets = ["192.168.1.0/24", "192.168.2.0/24"]
    >>> alive_hosts = scan_targets(targets)
    >>> print(alive_hosts)
    """

    def scan_subnet(target: str) -> list:
        """
        Scan a single subnet or IP address.

        Parameters
        ----------
        target : str
            The target subnet or IP address.

        Returns
        -------
        list
            A list of alive hosts in the target.
        """
        scanner = nmap.PortScanner()
        scanner.scan(hosts=target, arguments="-sn")
        return [host for host in scanner.all_hosts()]

    results = {}

    with ThreadPoolExecutor(max_threads) as executor:
        for target, alive_hosts in zip(targets, executor.map(scan_subnet, targets)):
            results[target] = alive_hosts

    return results


def set_dependencies(selected: List[str]) -> List[str]:
    """
    Define collector dependencies.

    Parameters
    ----------
    selected : list[str]
        The list of selected collectors.

    Returns
    -------
    list[str]
        The updated list of selected collectors.

    """

    def get_execution_order(job: str, collectors: dict) -> List[str]:
        order = []
        if job not in collectors:
            return [job]
        for dependency in collectors[job]["dependencies"]:
            order.extend(get_execution_order(dependency, collectors))
        order.append(job)
        return order

    def combine_execution_orders(jobs: List[str], collectors: dict) -> List[str]:
        combined_order = []

        for job in jobs:
            combined_order.extend(get_execution_order(job, collectors))

        # Deduplicate while preserving order
        seen = set()
        deduplicated_order = [
            j for j in combined_order if j not in seen and not seen.add(j)
        ]
        return deduplicated_order

    # Define dependencies.
    collectors = {
        "bgp_neighbors": {"dependencies": ["interface_ip_addresses"]},
        "devices_modules": {"dependencies": ["devices_inventory"]},
        "interface_summary": {
            "dependencies": ["cam_table", "interface_description", "interface_status"]
        },
        "get_device_statuses": {"dependencies": ["get_organizations"]},
        "vip_destinations": {"dependencies": ["vip_availability"]},
        "infoblox_get_networks_parent_containers": {
            "dependencies": ["infoblox_get_networks", "infoblox_get_network_containers"]
        },
        "device_statuses": {"dependencies": ["organizations"]},
        "network_appliance_vlans": {"dependencies": ["org_networks"]},
        "network_device_statuses": {"dependencies": ["org_device_statuses"]},
        "network_devices": {"dependencies": ["organizations"]},
        "org_devices": {"dependencies": ["organizations"]},
        "org_device_statuses": {"dependencies": ["org_networks"]},
        "org_networks": {"dependencies": ["organizations"]},
        "switch_lldp_neighbors": {"dependencies": ["switch_port_statuses"]},
        "switch_port_usages": {"dependencies": ["switch_port_statuses"]},
        "switch_port_statuses": {"dependencies": ["org_devices", "organizations"]},
        "vpn_statuses": {"dependencies": ["organizations"]},
    }

    selected = combine_execution_orders(selected, collectors)

    return selected


def set_filepath(filepath: str) -> str:
    """
    Creates a filename with the date and time added to a path the user
    provides. The function assumes the last "." in a filename is the extension.

    Parameters
    ----------
    filepath : str
        The base filepath. Do not include the date; that will be added
        dynamically at runtime.

    Returns
    -------
    filepath : str
        The full path to the modified filename.
    """
    # Convert '~' to the user's home folder
    if "~" in filepath:
        filepath = filepath.replace("~", os.path.expanduser("~"))
    # Set the prefix in YYYY-MM-DD_HHmm format
    prefix = dt.now().strftime("%Y-%m-%d_%H%M")
    # Extract the base path to the filename
    filepath = filepath.split("/")
    filename = filepath[-1]
    if len(filepath) > 2:
        filepath = "/".join(filepath[:-1])
    else:
        filepath = filepath[0]
    # Extract the filename and extension from 'filepath'
    filename = filename.split(".")
    extension = filename[-1]
    if len(filename) > 2:
        filename = ".".join(filename[:-1])
    else:
        filename = filename[0]
    # Return the modified filename
    filepath = f"{filepath}/{prefix}_{filename}.{extension}"
    return filepath


def suppress_extravars(extravars: dict) -> dict:
    """
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

    Parameters
    ----------
    extravars : dict
        A dictionary containing the extravars. If your function does not use
        it, then pass an empty dict instead.

    Returns
    -------
    extravars : dict
        'extravars' with the 'suppress_env_files' key.
    """
    # TODO: Finish this function. (Note: I thought about adding a check to
    #       manually delete any files in extravars at beginning and end of
    #       each run, but users might not want that.)


def get_net_manage_path() -> str:
    """
    Set the absolute path to the Net-Manage repository.

    Returns
    -------
    nm_path : str
        The absolute path to the Net-Manage repository.
    """
    nm_path = input("Enter the absolute path to the Net-Manage repository: ")
    nm_path = os.path.expanduser(nm_path)
    return nm_path


def set_db_timestamp() -> str:
    """
    Sets a timestamp in the form the database expects.

    Returns
    -------
    timestamp : str
        A timestamp in the YYYY-MM-DD_hhmm format.
    """
    timestamp = dt.now()
    timestamp = timestamp.strftime("%Y-%m-%d_%H%M")
    return timestamp


def set_vars() -> Tuple[str, str, List[str], str, str, str]:
    """
    Prompts the user for the required variables for running collectors and
    validators. Several defaults are presented.

    Note: The 'inventories' argument is a list of inventory files. Currently,
    the function statically defines it as ['private_data_dir/inventory/hosts'].
    If users want to use different file names or more than one file name,
    that functionality can be added later.

    Returns
    -------
    api_key : str
        The api key.
    db_path : str
        The path to the database.
    inventories : list of str
        The list of inventory files.
    nm_path : str
        The path to the nm.
    out_path : str
        The path for output.
    private_data_dir : str
        The private data directory.
    """
    default_db = f"{str(dt.now()).split()[0]}.db"
    default_nm_path = "~/source/repos/InsightSSG/Net-Manage/"

    db = input(f"Enter the name of the database: [{default_db}]")
    nm_path = input(f"Enter path to Net-Manage repository [{default_nm_path}]")
    private_data_dir = input("Enter the path to the private data directory:")

    npm_server = input("Enter the URL of the Solarwinds NPM server:")
    npm_username = input("Enter the username for Solarwinds NPM:")
    npm_password = getpass("Enter the password for Solarwinds NPM:")

    default_out_path = f"{private_data_dir}/output"
    out_path = input(f"Enter the path to store results: [{default_out_path}]")

    api_key = meraki_get_api_key()

    if not db:
        db = default_db
    if not nm_path:
        nm_path = default_nm_path
    if not out_path:
        out_path = default_out_path

    if not npm_server:
        npm_server = str()
    if not npm_username:
        npm_username = str()
    if not npm_password:
        npm_password = str()

    db = os.path.expanduser(db)
    nm_path = os.path.expanduser(nm_path)
    out_path = os.path.expanduser(out_path)
    private_data_dir = os.path.expanduser(private_data_dir)
    db_path = f"{out_path}/{db}"

    # TODO: Add support for a custom inventory file name
    # TODO: Add support for more than one inventory file (Ansible-Runner
    #       supports that, but I am not sure how common it is)
    inventories = [f"{private_data_dir}/inventory/hosts"]

    return (
        api_key,
        db,
        db_path,
        inventories,
        npm_server,
        npm_username,
        npm_password,
        nm_path,
        out_path,
        private_data_dir,
    )


def get_tests_file() -> str:
    """
    Set the absolute path to the Net-Manage repository.

    Returns
    -------
    t_path : str
        The absolute path to the file containing tests to run.
    """
    t_file = input("Enter the absolute path to the Net-Manage repository: ")
    t_file = os.path.expanduser(t_file)
    return t_file


def get_user_meraki_input() -> (
    Tuple[List[str], List[str], List[str], int, int, Union[int, str]]
):
    """
    Gets and parses user input when they select collectors for Meraki
    organizations.

    Returns
    -------
    orgs : list
        A list of one or more organizations. Defaults to an empty list.
    networks : list
        A list of one or more networks. Defaults to an empty list.
    macs : list
        A list of one or more MAC addresses. Partial addresses are accepted.
        Defaults to an empty list.
    timespan : int
        The lookback timespan in seconds. Defaults to 1 day (86400 seconds).
        If a user has an * between numbers, it will multiply them. It does not
        perform any other calculation (addition, subtraction, etc).
    per_page : int
        The number of results to return per page. Defaults to 10. It is
        recommended to leave it at 10, as increasing the number of results
        can reduce performance. However, increasing it might be worth trying
        when working with large datasets.
    total_pages : int or str
        The total number of pages to return. If input is 'all', returns as
        'all'. Otherwise, converts the input into an integer. Defaults to
        'all'.
    """
    orgs = input("Enter a comma-delimited list of organizations to query: ") or list()
    if orgs:
        orgs = [_.strip() for _ in orgs.split(",")]

    networks = input("Enter a comma-delimited list of networks to query: ") or list()
    if networks:
        networks = [_.strip() for _ in networks.split(",")]

    macs = input("Enter a comma-delimited list of MAC addresses: ") or list()
    if macs:
        macs = [_.strip() for _ in macs.split(",")]

    timespan = input("Enter the lookback timespan in seconds: ") or "86400"
    timespan = np.prod([int(_) for _ in timespan.split("*")])

    per_page = int(input("Enter the number of results per page: ") or 10)

    total_pages = input("Enter the total number of pages to return: ") or "all"
    if total_pages[0].isdigit() or total_pages[0] == "-":
        total_pages = int(total_pages)

    return orgs, networks, macs, timespan, per_page, total_pages


def is_valid_ip(ip: str) -> bool:
    """
    Check if a string is a valid IPv4 or IPv6 address or CIDR notation.

    Parameters
    ----------
    ip : str
        The string to be checked for being a valid IP address or CIDR notation.

    Returns
    -------
    bool
        Returns True if the string is a valid IPv4 or IPv6 address or CIDR
        notation, otherwise False.

    Examples
    --------
    >>> is_valid_ip_or_cidr('192.168.1.1')
    True
    >>> is_valid_ip_or_cidr('192.168.1.0/24')
    True
    >>> is_valid_ip_or_cidr('2001:0db8:85a3:0000:0000:8a2e:0370:7334')
    True
    >>> is_valid_ip_or_cidr('2001:0db8::/32')
    True
    >>> is_valid_ip_or_cidr('N/A')
    False
    >>> is_valid_ip_or_cidr('invalid_ip')
    False
    """
    try:
        ipaddress.ip_network(ip, strict=False)
        return True
    except ValueError:
        return False


def meraki_map_network_to_organization(network: str, db_path: str) -> str:
    """
    Gets the organization ID for a network.

    Parameters
    ----------
    network : str
        A network ID.
    db_path : str
        The path to the database.

    Returns
    -------
    org_id : str
        The organization ID.
    """
    query = f"""SELECT distinct timestamp, organizationId
                FROM MERAKI_ORG_NETWORKS
                WHERE id = "{network}"
                ORDER BY timestamp desc
                LIMIT 1
             """
    con = sl.connect(db_path)
    result = pd.read_sql(query, con)
    con.close()

    org_id = result["organizationId"].to_list()[0]

    return org_id


def meraki_parse_organizations(
    db_path: str, orgs: list = None, table: str = None
) -> list:
    """
    Parses a list of organizations that are passed to certain Meraki
    collectors.

    Parameters
    ----------
    db_path : str
        The path to the database to store results.
    orgs : list, optional
        One or more organization IDs. If none are specified, then the
        networks for all orgs will be returned. Defaults to None.
    table : str, optional
        The database table to query. Defaults to None.

    Returns
    -------
    organizations : list
        A list of organizations.
    """
    con = sl.connect(db_path)
    organizations = list()
    if orgs:
        for org in orgs:
            df_orgs = pd.read_sql(
                f'select distinct id from {table} \
                where id = "{org}"',
                con,
            )
            organizations.append(df_orgs["id"].to_list().pop())
    else:
        df_orgs = pd.read_sql(f"select distinct id from {table}", con)
        for org in df_orgs["id"].to_list():
            organizations.append(org)
    con.close()

    return organizations


def sql_get_table_schema(db_path: str, table: str) -> pd.DataFrame:
    """
    Gets the schema of a table.

    Parameters
    ----------
    db_path : str
        The path to the database.
    table : str
        The table from which to get the schema.

    Returns
    -------
    df_schema : pd.DataFrame
        The table schema. If the table does not exist then an empty dataframe
        will be returned.
    """
    query = f'pragma table_info("{table}")'

    con = sl.connect(db_path)
    df_schema = pd.read_sql(query, con)

    return df_schema


def download_ouis(path: str) -> None:
    """
    Downloads vendor OUIs from https://standards-oui.ieee.org/.

    The results will be stored in a text file located at 'path'.

    Parameters
    ----------
    path : str
        The full path to the filename to store the results.

    Raises
    ----------
    FileNotFoundError
        If the directory in the path does not exist.
    IsADirectoryError
        If a filename was not included in 'path'.

    Examples
    ----------
    >>> path = '/tmp/ouis.txt'
    >>> download_ouis(path)
    """
    url = "https://standards-oui.ieee.org/"
    response = requests.get(url, stream=True)
    with open(path, "wb") as txt:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                txt.write(chunk)


def subnet_mask_to_cidr(masks: list) -> list:
    """Convert a list of subnet masks to CIDR notation.

    Parameters
    ----------
    masks : list
        A list of subnet masks.

    Returns
    -------
    cidrs : list
        A list of subnet masks converted to CIDR notation.

    """
    cidrs = list()
    for mask in masks:
        cidr = ipaddress.ip_network(f"0.0.0.0/{mask}")
        cidrs.append(cidr.prefixlen)
    return cidrs


def tabulate_df_head(df: pd.DataFrame) -> None:
    """
    Print the first 5 rows of a DataFrame as a table.

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to print.

    Returns
    -------
    None
        This function does not return anything, it simply prints the table.
    """
    table_data = df.head().to_dict("records")

    print(tabulate(table_data, headers="keys", tablefmt="psql"))


def tz_abbreviation_to_pytz(tz_string):
    """Convert timezone abbreviation to a format recognized by pytz."""

    tz_map = {
        "ACDT": "Australia/Adelaide",
        "ACST": "Australia/Darwin",
        "ACT": "America/Sao_Paulo",  # Ambiguous
        "ADT": "America/Halifax",
        "AEDT": "Australia/Sydney",
        "AEST": "Australia/Brisbane",
        "AFT": "Asia/Kabul",
        "AKDT": "America/Juneau",
        "AKST": "America/Anchorage",
        "AMST": "America/Campo_Grande",  # Ambiguous
        "AMT": "America/Boa_Vista",  # Ambiguous
        "ART": "America/Argentina/Buenos_Aires",
        "AST": "America/Puerto_Rico",  # Ambiguous
        "AWST": "Australia/Perth",
        "AZOST": "Atlantic/Azores",
        "AZT": "Asia/Baku",
        "BDT": "Asia/Dhaka",
        "BIOT": "Indian/Chagos",
        "BIT": "Pacific/Enderbury",
        "BOT": "America/La_Paz",
        "BRST": "America/Sao_Paulo",
        "BRT": "America/Rio_Branco",
        "BST": "Europe/London",  # Ambiguous
        "BTT": "Asia/Thimphu",
        "CAT": "Africa/Harare",
        "CCT": "Indian/Cocos",
        "CDT": "America/Chicago",
        "CEST": "Europe/Paris",
        "CET": "Europe/Berlin",
        "CHADT": "Pacific/Chatham",
        "CHAST": "Pacific/Chatham",
        "CLST": "America/Santiago",
        "CLT": "America/Santiago",
        "COST": "America/Bogota",
        "COT": "America/Bogota",
        "CST": "America/Chicago",  # Ambiguous
        "CT": "Asia/Shanghai",
        "CVT": "Atlantic/Cape_Verde",
        "CWST": "Australia/Eucla",
        "CXT": "Indian/Christmas",
        "DAVT": "Antarctica/Davis",
        "DDUT": "Antarctica/DumontDUrville",
        "DFT": "Europe/Paris",
        "EASST": "Pacific/Easter",
        "EAST": "Pacific/Easter",
        "EAT": "Africa/Nairobi",
        "ECT": "Pacific/Galapagos",
        "EDT": "America/New_York",
        "EEST": "Europe/Bucharest",
        "EET": "Europe/Helsinki",
        "EGST": "America/Scoresbysund",
        "EGT": "America/Scoresbysund",
        "EIT": "Asia/Jayapura",
        "EST": "America/New_York",  # Ambiguous
        "FET": "Europe/Kaliningrad",
        "FJT": "Pacific/Fiji",
        "FKST": "Atlantic/Stanley",
        "FKT": "Atlantic/Stanley",
        "FNT": "America/Noronha",
        "GALT": "Pacific/Galapagos",
        "GAMT": "Pacific/Gambier",
        "GET": "Asia/Tbilisi",
        "GFT": "America/Cayenne",
        "GILT": "Pacific/Tarawa",
        "GIT": "Pacific/Gambier",
        "GMT": "Etc/GMT",
        "GST": "Asia/Dubai",  # Ambiguous
        "GYT": "America/Guyana",
        "HADT": "America/Adak",
        "HAEC": "Europe/Paris",
        "HAST": "Pacific/Honolulu",
        "HKT": "Asia/Hong_Kong",
        "HMT": "Asia/Kolkata",
        "HOVT": "Asia/Hovd",
        "ICT": "Asia/Bangkok",
        "IDT": "Asia/Jerusalem",
        "IOT": "Indian/Chagos",
        "IRDT": "Asia/Tehran",
        "IRKT": "Asia/Irkutsk",
        "IRST": "Asia/Tehran",
        "IST": "Asia/Kolkata",  # Ambiguous
        "JST": "Asia/Tokyo",
        "KGT": "Asia/Bishkek",
        "KOST": "Pacific/Kosrae",
        "KRAT": "Asia/Krasnoyarsk",
        "KST": "Asia/Seoul",
        "LHST": "Australia/Lord_Howe",
        "LINT": "Pacific/Kiritimati",
        "MAGT": "Asia/Magadan",
        "MART": "Pacific/Marquesas",
        "MAWT": "Antarctica/Mawson",
        "MDT": "America/Denver",
        "MEST": "Europe/Paris",
        "MET": "Europe/Berlin",  # Ambiguous
        "MHT": "Pacific/Majuro",
        "MIST": "Antarctica/Macquarie",
        "MIT": "Pacific/Marquesas",
        "MMT": "Asia/Yangon",
        "MSK": "Europe/Moscow",
        "MST": "America/Denver",  # Ambiguous
        "MUT": "Indian/Mauritius",
        "MVT": "Indian/Maldives",
        "MYT": "Asia/Kuala_Lumpur",
        "NCT": "Pacific/Noumea",
        "NDT": "America/St_Johns",
        "NFT": "Pacific/Norfolk",
        "NOVT": "Asia/Novosibirsk",
        "NPT": "Asia/Kathmandu",
        "NST": "America/St_Johns",  # Ambiguous
        "NT": "America/St_Johns",
        "NUT": "Pacific/Niue",
        "NZDT": "Pacific/Auckland",
        "NZST": "Pacific/Auckland",
        "OMST": "Asia/Omsk",
        "ORAT": "Asia/Oral",
        "PDT": "America/Los_Angeles",
        "PET": "America/Lima",
        "PETT": "Asia/Kamchatka",
        "PGT": "Pacific/Port_Moresby",
        "PHOT": "Pacific/Enderbury",
        "PHT": "Asia/Manila",
        "PKT": "Asia/Karachi",
        "PMDT": "America/Miquelon",
        "PMST": "America/Miquelon",
        "PONT": "Pacific/Pohnpei",
        "PST": "America/Los_Angeles",  # Ambiguous
        "PYST": "America/Asuncion",
        "PYT": "America/Asuncion",
        "RET": "Indian/Reunion",
        "ROTT": "Antarctica/Rothera",
        "SAKT": "Asia/Sakhalin",
        "SAMT": "Europe/Samara",
        "SAST": "Africa/Johannesburg",
        "SBT": "Pacific/Guadalcanal",
        "SCT": "Indian/Mahe",
        "SGT": "Asia/Singapore",
        "SLT": "Asia/Colombo",
        "SRET": "Asia/Srednekolymsk",
        "SRT": "America/Paramaribo",
        "SST": "Pacific/Pago_Pago",
        "SYOT": "Antarctica/Syowa",
        "TAHT": "Pacific/Tahiti",
        "THA": "Asia/Bangkok",
        "TFT": "Indian/Kerguelen",
        "TJT": "Asia/Dushanbe",
        "TKT": "Pacific/Fakaofo",
        "TLT": "Asia/Dili",
        "TMT": "Asia/Ashgabat",
        "TRT": "Europe/Istanbul",
        "TVT": "Pacific/Funafuti",
        "UCT": "Etc/UCT",
        "ULAT": "Asia/Ulaanbaatar",
        "USZ1": "Europe/Kaliningrad",
        "UTC": "Etc/UTC",
        "UYST": "America/Montevideo",
        "UYT": "America/Montevideo",
        "UZT": "Asia/Tashkent",
        "VET": "America/Caracas",
        "VLAT": "Asia/Vladivostok",
        "VOLT": "Europe/Volgograd",
        "VOST": "Antarctica/Vostok",
        "VUT": "Pacific/Efate",
        "WAKT": "Pacific/Wake",
        "WAST": "Africa/Windhoek",
        "WAT": "Africa/Lagos",
        "WEST": "Europe/Lisbon",
        "WET": "Europe/Lisbon",
        "WIT": "Asia/Jakarta",
        "WST": "Pacific/Apia",
        "YAKT": "Asia/Yakutsk",
        "YEKT": "Asia/Yekaterinburg",
        "Z": "Etc/UTC",
    }

    # Extract the timezone abbreviation using regex
    match = re.search(r"\b([A-Z]{3,5})\b", tz_string)
    if match:
        tz_abbreviation = match.group(1)
        # Return None if abbreviation not in the map
        return tz_map.get(tz_abbreviation, None)

    return None


def update_ouis(nm_path: str) -> pd.DataFrame:
    """
    Download or update vendor OUIs and save them to a file.

    The data is pulled from https://standards-oui.ieee.org/ and saved to a
    text file named 'ouis.txt'. If 'ouis.txt' does not exist or is more
    than one week old, then it will be downloaded.

    Parameters
    ----------
    nm_path : str
        The path to the Net-Manage repository.

    Notes
    ----------
    There is a Python library to do this, but it is quite slow.

    It might seem inefficient to parse the OUIs from a text file on an
    as-needed basis. However, testing found that the operation only takes
    about 250ms, and the size of the resulting dataframe is only
    approximately 500KB.

    Returns
    ----------
    df : DataFrame
        A Pandas DataFrame containing two columns. The first is the MAC
        address base in base16 format, and the second is the corresponding
        vendor OUI.

    Examples
    ----------
    >>> df = update_ouis(nm_path)
    >>> print(df[:2].to_dict())
    {'mac_base': {0: '002272', 1: '00D0EF'},
    'vendor_oui': {0: 'American Micro-Fuel Device Corp.', 1: 'IGT'}}
    """
    # Check if 'ouis.txt' exists in 'nm_path', and, if so, get the timestamp.
    files = get_dir_timestamps(nm_path)

    # Check if 'ouis.txt' needs to be downloaded.
    download = False
    if f"{nm_path}/ouis.txt" not in files:
        download = True
    else:
        delta = (dt.now().date() - files[f"{nm_path}/ouis.txt"].date()).days
        if delta > 7:
            download = True

    # Download 'ouis.txt', if applicable.
    if download:
        download_ouis(f"{nm_path}/ouis.txt")

    # Read 'ouis.txt' and extract the base16 and vendor combinations.
    with open(f"{nm_path}/ouis.txt", "r") as txt:
        data = txt.read()
    pattern = ".*base 16.*"
    data = re.findall(pattern, data)
    data = [[_.split()[0], _.split("\t")[-1]] for _ in data]
    df = pd.DataFrame(data=data, columns=["base", "vendor"])

    return df


def validate_table(table: str, db_path: str, diff_col: List[str]) -> None:
    """
    Validates a table, based on the columns that the user passes to the
    function.

    Args:
        table : str
            The table to validate.
        db_path : str
            The path to the database.
        diff_col : list of str
            The column to diff. It should contain two items:
            - item1: The column to diff (e.g., 'status').
            - item2: The expected state (e.g., 'online').
    """
    # Get the first and last timestamps from the table
    con = sl.connect(db_path)
    query = f"select distinct timestamp from {table}"
    df_stamps = pd.read_sql(query, con)
    stamps = df_stamps["timestamp"].to_list()
    first_ts = stamps[0]
    last_ts = stamps[-1]

    # Execute the queries and diff the results
    query1 = f'{diff_col[0]} = "{diff_col[1]}" and timestamp = "{first_ts}"'
    query2 = f'{diff_col[0]} = "{diff_col[1]}" and timestamp = "{last_ts}"'
    query = f"""select *
                from {table}
                where {query1}
                except
                select *
                from {table}
                where {query2}
                """
    df_diff = pd.read_sql(query, con)
    return df_diff


def convert_lists_to_json_in_df(df):
    """
    Convert columns containing lists in a DataFrame to JSON strings.

    Parameters:
    - df (pd.DataFrame): Input DataFrame

    Returns:
    - pd.DataFrame: Updated DataFrame with lists converted to JSON strings
    """

    # Function to check if an element is a list and then convert to JSON
    def convert_list_to_json(element):
        if isinstance(element, list):
            return json.dumps(element)
        return element

    # Apply the function to each column in the DataFrame
    for col in df.columns:
        df[col] = df[col].apply(convert_list_to_json)

    return df


# def is_jupyter():
#     try:
#         return get_ipython().__class__.__name__ == 'ZMQInteractiveShell'  # noqa
#     except NameError:
#         return False


def is_jupyter():
    # Alternate implementation of is_jupyter that does not create lint errors.
    # This needs to be tested.
    try:
        from IPython import get_ipython

        if "IPKernelApp" not in get_ipython().config:  # Kernel not running in IPython
            return False
    except Exception:  # get_ipython() doesn't exist, IPython not loaded
        return False
    return True


def ansible_host_to_ip(hostname):
    # Create a DataLoader instance
    loader = DataLoader()
    inventory_file = f"{os.environ.get('private_data_directory')}/inventory/hosts"
    # Create an InventoryManager instance with the provided inventory file
    inventory = InventoryManager(loader=loader, sources=inventory_file)
    
    # Find the host in the inventory
    host = inventory.get_host(hostname)
    if host:
        # Extract the host's IP address
        host_address = str(host.vars.get('ansible_host'))
        if host_address:
            return host_address
    return hostname
