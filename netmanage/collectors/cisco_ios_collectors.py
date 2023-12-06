#!/usr/bin/env python3

import ansible_runner
import pandas as pd

from netmanage.parsers import cisco_ios_parsers as parser


def gather_facts(
    username: str,
    password: str,
    host_group: str,
    play_path: str,
    private_data_dir: str,
    gather_info: dict,
) -> dict:
    """Gathers specified facts on Cisco IOS devices.

    Parameters
    ----------
    username : str
        The username to use for authentication.
    password : str
        The password to use for authentication.
    host_group : str
        The host group for which to gather facts.
    play_path : str
        The path to playbooks in Ansible.
    private_data_dir : str
        The path to private data directories in Ansible.
    gather_info : dict
        A nested dictionary containing either (or both) of the following keys:
        'subset' and/or 'network_subset'. The value of each of those keys is a
        list containing the subset of data to gather. A complete list can be
        found here:
        https://docs.ansible.com/ansible/latest/collections/cisco/ios/ios_facts_module.html

    Returns
    -------
    facts : dict
        A dictionary where each key is a device in the host_group and the value
        is the requested facts.

    Notes
    -------
    If a dictionary is empty then nothing will be returned. This is different
    from the default Ansible behavior. It is done this way to save memory.

    Examples:
    -------
    >>> gather_info = {'subset': ['config']}
    >>> facts = gather_facts(username,
    ...                      password,
    ...                      host_group,
    ...                      play_path,
    ...                      private_data_dir,
    ...                      gather_info)
    >>> for key, value in facts.items():
    >>>     for k, v in value.items():
    >>>         print(k, type(v))
    >>>     break
    >>> ansible_network_resources <class 'dict'>
    >>> ansible_net_gather_network_resources <class 'list'>
    >>> ansible_net_gather_subset <class 'list'>
    >>> ansible_net_config <class 'str'>
    >>> ansible_net_system <class 'str'>
    >>> ansible_net_model <class 'str'>
    >>> ansible_net_image <class 'str'>
    >>> ansible_net_version <class 'str'>
    >>> ansible_net_hostname <class 'str'>
    >>> ansible_net_api <class 'str'>
    >>> ansible_net_python_version <class 'str'>
    >>> ansible_net_iostype <class 'str'>
    >>> ansible_net_operatingmode <class 'str'>
    >>> ansible_net_serialnum <class 'str'>

    >>> gather_info =  {'subset': ['hardware', 'config'],
    ...                 'network_subset': ['hostname', 'snmp_server']}
    >>> facts = gather_facts(username,
    ...                      password,
    ...                      host_group,
    ...                      play_path,
    ...                      private_data_dir,
    ...                      gather_info)
    >>> for key in facts:
    ...     for k in facts[key]['ansible_network_resources']:
    ...         print(k, type(k))
    ...     break

    >>> hostname <class 'str'>
    >>> snmp_server <class 'str'>
    """
    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "gather_info": gather_info,
    }

    # Execute the pre-checks
    playbook = f"{play_path}/cisco_ios_gather_facts.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    return parser.parse_facts(runner)


def gather_basic_facts(
    username: str, password: str, host_group: str, play_path: str, private_data_dir: str
) -> pd.DataFrame:
    """
    Get 'minimum' facts like model number, hostname, etc, using Ansible's gather_facts.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the facts.
    """
    gather_info = {"subset": ["min"]}
    facts = gather_facts(
        username, password, host_group, play_path, private_data_dir, gather_info
    )

    # Parse results into df
    return parser.ios_parse_gather_basic_facts(facts)


def bgp_neighbors(
    username: str, password: str, host_group: str, play_path: str, private_data_dir: str
) -> pd.DataFrame:
    """Gets the BGP neighbors for all VRFs.

    Parameters
    ----------
    username : str
        The username to use for authentication.
    password : str
        The password to use for authentication.
    host_group : str
        The host group to query for VRF information.
    play_path : str
        The path to playbooks in Ansible.
    private_data_dir : str
        The path to private data directories in Ansible.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the BGP neighbor summary.
    """
    cmd = [
        "show ip bgp all neighbors ",
        " include BGP neighbor is",
        "Member of",
        "BGP version",
        "BGP state",
        "Local host",
    ]
    cmd = "|".join(cmd)

    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute the pre-checks
    playbook = f"{play_path}/cisco_ios_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.parse_bgp_neighbors(runner)


def cdp_neighbors(
    username: str, password: str, host_group: str, play_path: str, private_data_dir: str
) -> pd.DataFrame:
    """Gets the CDP neighbors for IOS devices.

    Parameters
    ----------
    username : str
        The username to use for authentication.
    password : str
        The password to use for authentication.
    host_group : str
        The host group to query for VRF information.
    play_path : str
        The path to playbooks in Ansible.
    private_data_dir : str
        The path to private data directories in Ansible.

    Returns
    -------
    df : pandas.DataFrame
        A DataFrame containing the CDP neighbors.
    """
    params = [
        "-------------------------",
        "Device ID",
        "Entry address",
        "IP address",
        "IPv6 address",
        "Platform",
        "Interface",
        "Duplex",
        "Management",
    ]
    params = "|".join(params)

    cmd = f"show cdp nei detail | include {params}"

    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute the pre-checks
    playbook = f"{play_path}/cisco_ios_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.parse_cdp_neighbors(runner)


def inventory(
    username: str, password: str, host_group: str, play_path: str, private_data_dir: str
) -> pd.DataFrame:
    """
    Get the inventory for Cisco IOS and IOS-XE devices.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the interfaces and IP addresses.
    """
    cmd = "show inventory"
    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute the command
    playbook = f"{play_path}/cisco_ios_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.ios_parse_inventory(runner)


def get_config(
    username: str, password: str, host_group: str, play_path: str, private_data_dir: str
) -> pd.DataFrame:
    """Gets the config on Cisco IOS devices.

    Parameters
    ----------
    username : str
        The username to use for authentication.
    password : str
        The password to use for authentication.
    host_group : str
        The host group for which to gather configs.
    play_path : str
        The path to playbooks in Ansible.
    private_data_dir : str
        The path to private data directories in Ansible.

    Returns
    -------
    df : pandas.DataFrame
        A DataFrame containing the device configurations.
    """
    gather_info = {"subset": ["config"]}
    facts = gather_facts(
        username, password, host_group, play_path, private_data_dir, gather_info
    )

    # Parse results into df
    return parser.parse_config(facts)


def get_vrfs(
    username: str, password: str, host_group: str, play_path: str, private_data_dir: str
) -> pd.DataFrame:
    """Retrieve VRF information and return it as a DataFrame.

    Parameters
    ----------
    username : str
        The username to use for authentication.
    password : str
        The password to use for authentication.
    host_group : str
        The host group to query for VRF information.
    play_path : str
        The path to playbooks in Ansible.
    private_data_dir : str
        The path to private data directories in Ansible.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing VRF information, with columns ["device", "name",
        "vrf_id", "default_rd", "default_vpn_id"].
    """
    cmd = "show vrf"
    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute the pre-checks
    playbook = f"{play_path}/cisco_ios_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.parse_vrfs(runner)


def ospf_neighbors(
    username: str, password: str, host_group: str, play_path: str, private_data_dir: str
) -> pd.DataFrame:
    """Gets the OSPF neighbors for all VRFs.

    Parameters
    ----------
    username : str
        The username to use for authentication.
    password : str
        The password to use for authentication.
    host_group : str
        The host group to query for VRF information.
    play_path : str
        The path to playbooks in Ansible.
    private_data_dir : str
        The path to private data directories in Ansible.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing the OSPF neighbors.
    """
    cmd = [
        "show ip ospf neighbor detail",
        "include interface address|area|priority|for|Dead timer",
    ]
    cmd = " | ".join(cmd)
    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute the pre-checks
    playbook = f"{play_path}/cisco_ios_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.parse_ospf_neighbors(runner)


def ios_find_uplink_by_ip(
    username: str,
    password: str,
    host_group: str,
    play_path: str,
    private_data_dir: str,
    subnets: list = [],
) -> pd.DataFrame:
    """
    Search the hostgroup for a list of subnets (use /32 to search for a
    single IP). Once it finds them, it uses CDP and LLDP (if applicable) to try
    to find the uplink.

    If a list of IP addresses is not provided, it will attempt to find the
    uplinks for all IP addresses on the devices.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    subnets : list, optional
        A list of one or more subnets to search for. Use CIDR notation. Use /32
        to search for individual IPs. If no list is provided, the function will
        try to find the uplinks for all IP addresses on the devices.

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
    # Get the IP addresses on the devices in the host group
    df_ip = ios_get_interface_ips(
        username, password, host_group, play_path, private_data_dir
    )

    # Get the CDP neighbors for the device
    df_cdp = ios_get_cdp_neighbors(
        username, password, host_group, play_path, private_data_dir
    )

    # Parse results into df
    return parser.ios_parse_uplink_by_ip(df_ip, df_cdp)


def ios_get_arp_table(
    username: str,
    password: str,
    host_group: str,
    nm_path: str,
    play_path: str,
    private_data_dir: str,
) -> pd.DataFrame:
    """
    Get the IOS ARP table and add the vendor OUI.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.

    Returns
    -------
    df_arp : pd.DataFrame
        The ARP table and vendor OUI as a pandas DataFrame.
    """
    cmd = "show ip arp"
    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute the pre-checks
    playbook = f"{play_path}/cisco_ios_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.ios_parse_arp_table(runner, nm_path)


def ios_get_cam_table(
    username: str,
    password: str,
    host_group: str,
    nm_path: str,
    play_path: str,
    private_data_dir: str,
    interface: str = None,
) -> pd.DataFrame:
    """
    Get the IOS CAM table and add the vendor OUI.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    interface : str, optional
        The interface (defaults to all interfaces).

    Returns
    -------
    df_cam : pd.DataFrame
        The CAM table and vendor OUI as a pandas DataFrame.
    """
    if interface:
        cmd = f"show mac address-table interface {interface}"
    else:
        cmd = "show mac address-table | begin Vlan"
    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute the pre-checks
    playbook = f"{play_path}/cisco_ios_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.ios_parse_cam_table(runner, nm_path)


def ios_get_cdp_neighbors(
    username: str,
    password: str,
    host_group: str,
    play_path: str,
    private_data_dir: str,
    interface: str = "",
) -> pd.DataFrame:
    """
    Get the CDP neighbors for a Cisco IOS device.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    interface : str, optional
        The interface to get the neighbor entry for. If not specified, it will
        get all neighbors.

    Returns
    -------
    df_cdp : pd.DataFrame
        A DataFrame containing the CDP neighbors.
    """
    cmd = "show cdp neighbor detail | include Device ID|Interface"
    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute the command
    playbook = f"{play_path}/cisco_ios_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.ios_parse_cdp_neighbors(runner)


def ios_get_interface_descriptions(
    username: str,
    password: str,
    host_group: str,
    play_path: str,
    private_data_dir: str,
    interface: str = None,
) -> pd.DataFrame:
    """
    Get IOS interface descriptions.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    interface : str, optional
        The interface (defaults to all interfaces).

    Returns
    -------
    df_desc : pd.DataFrame
        A DataFrame containing the interface descriptions.
    """
    # Get the interface descriptions and add them to df_cam
    cmd = "show interface description"
    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute 'show interface description' and parse the results
    playbook = f"{play_path}/cisco_ios_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.ios_parse_interface_descriptions(runner)


def ios_get_interface_ips(
    username: str, password: str, host_group: str, play_path: str, private_data_dir: str
) -> pd.DataFrame:
    """
    Get the IP addresses assigned to interfaces.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the interfaces and IP addresses.
    """
    cmd = [
        "show ip interface",
        "|",
        "include line protocol|Internet address is|VPN Routing",
    ]
    cmd = " ".join(cmd)
    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute the command
    playbook = f"{play_path}/cisco_ios_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.ios_parse_interface_ips(runner)


def ios_get_interface_ipv6_ips(
    username: str, password: str, host_group: str, play_path: str, private_data_dir: str
) -> pd.DataFrame:
    """
    Get the IPv6 addresses assigned to interfaces.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the interfaces and IP addresses.
    """
    cmd = "show ipv6 interface | include line protocol|subnet is|VPN Routing"
    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute the command
    playbook = f"{play_path}/cisco_ios_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.ios_parse_interface_ipv6_ips(runner)


def ios_get_vlan_db(
    username: str, password: str, host_group: str, play_path: str, private_data_dir: str
) -> pd.DataFrame:
    """
    Gets the VLAN database for Cisco IOS devices.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the VLAN database.
    """
    # Get the interface descriptions and add them to df_cam
    cmd = "show vlan brief | exclude ----"
    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute 'show interface description' and parse the results
    playbook = f"{play_path}/cisco_ios_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.ios_parse_vlan_db(runner)
