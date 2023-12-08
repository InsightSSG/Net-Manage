#!/usr/bin/env python3

import ansible_runner
import pandas as pd

from netmanage.parsers import cisco_asa_parsers as parser


def gather_facts(
    username: str,
    password: str,
    host_group: str,
    play_path: str,
    private_data_dir: str,
    gather_info: dict,
) -> dict:
    """Gathers specified facts on Cisco ASA devices.

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
        A nested dictionary containing either (or both) of thek following keys:
        'subset' and/or 'network_subset'. The value of each of those keys is a
        list containing the subset of data to gather. A complete list can be
        found here:
        https://docs.ansible.com/ansible/latest/collections/cisco/asa/asa_facts_module.html

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
    playbook = f"{play_path}/cisco_asa_gather_facts.yml"
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
    return parser.asa_parse_gather_basic_facts(facts)


def get_interface_ips(
    username: str, password: str, host_group: str, play_path: str, private_data_dir: str
) -> pd.DataFrame:
    """
    Gets the IP addresses assigned to interfaces on Cisco ASA devices.

    Parameters
    ----------
    username : str
        The username to login to devices
    password : str
        The password to login to devices
    host_group : str
        The inventory host group
    play_path : str
        The path to the playbooks directory
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the interfaces and IPs, subnet and network
        addresses related to each IP.
    """
    cmd = "show interface summary | include Interface|IP address"
    extravars = {
        "username": username,
        "password": password,
        "host_group": host_group,
        "commands": cmd,
    }

    # Execute the command
    playbook = f"{play_path}/cisco_asa_run_commands.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.asa_parse_interface_ips(runner)


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
    return parser.asa_parse_inventory(runner)
