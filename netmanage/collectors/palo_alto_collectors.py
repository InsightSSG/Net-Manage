#!/usr/bin/env python3

import ansible_runner
import pandas as pd
from typing import Dict
from netmanage.helpers import palo_alto_helpers as pah
from netmanage.parsers import palo_alto_parsers as parser


def run_adhoc_command(
    username: str,
    password: str,
    host_group: str,
    nm_path: str,
    private_data_dir: str,
    cmd: str,
    cmd_is_xml: bool,
    serial: str = "",
) -> Dict[str, dict]:
    """
    Runs an ad-hoc command on the specified hosts using Ansible.

    Parameters
    ----------
    username : str
        The user's username.
    password : str
        The user's password.
    host_group : str
        The name of the Ansible inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    private_data_dir : str
        The path to the Ansible private data directory.
    cmd : str
        The command to run.
    cmd_is_xml : bool
        Whether the command is formatted as XML.
    serial : str, optional
        The serial number of the device to run the command on. This is ignored
        if the device(s) in the host_group are not Panoramas.

    Returns
    -------
    dict
        A dictionary containing the command output, where the keys are the
        devices and the value is a dictionary containing all of the data
        within the event that contains the 'runner_on_ok' value.

    Notes
    -----
    Ansible-runner returns a generator containing each event that Ansible
    executed. In order to conserve memory, this function searches for
    events that contain the 'event' key with a value of
    'runner_on_ok'. That key does not mean that the task succeeded,
    it just indicates that it is the event that contains the results of the
    task.

    That logic should be revisited if a use-case arises that necessitates
    returning other events to whichever function that is calling this
    function.

    Examples
    --------
    >>> cmd = '<show><system><info></info></system></show>'
    >>> cmd_is_xml = True
    >>> response = run_adhoc_command(username,
                                     password,
                                     host_group,
                                     nm_path,
                                     private_data_dir,
                                     cmd,
                                     cmd_is_xml)
    >>> for key in response:
    >>>        assert isinstance(response[key]['event'], str)

    >>> cmd = 'show system software status'
    >>> cmd_is_xml = False
    >>> response = run_adhoc_command(username,
                                     password,
                                     host_group,
                                     nm_path,
                                     private_data_dir,
                                     cmd,
                                     cmd_is_xml)
    >>> for key in response:
    >>>        assert isinstance(response[key]['event'], str)
    """
    extravars = {
        "user": username,
        "password": password,
        "host_group": host_group,
        "cmd": cmd,
        "cmd_is_xml": cmd_is_xml,
        "serial_number": serial,
    }

    playbook = f"{nm_path}/playbooks/palo_alto_run_adhoc_command.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    result = dict()

    for event in runner.events:
        if event["event"] == "runner_on_ok":
            device = event["event_data"]["remote_addr"]
            result[device] = event

    return result


def inventory(
    username: str,
    password: str,
    host_group: str,
    nm_path: str,
    private_data_dir: str,
    serials: list = [],
) -> pd.DataFrame:
    """
    Gets partial hardware inventory on Palo Alto firewalls.

    Parameters
    ----------
    username : str
        The user's username.
    password : str
        The user's password.
    host_group : str
        The name of the Ansible inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the hardware inventory.
    """
    cmd = "show system info"
    cmd_is_xml = False

    response = run_adhoc_command(
        username,
        password,
        host_group,
        nm_path,
        private_data_dir,
        cmd,
        cmd_is_xml,
        serials,
    )

    # Parse results into df
    return parser.parse_inventory(response)


def bgp_neighbors(
    username: str,
    password: str,
    host_group: str,
    nm_path: str,
    private_data_dir: str,
    serials: list = [],
) -> pd.DataFrame:
    """Gets BGP neighbors for Palo Alto firewalls.

    Parameters
    ----------
    username : str
        The user's username.
    password : str
        The user's password.
    host_group : str
        The name of the Ansible inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    private_data_dir : str
        The path to the Ansible private data directory.

    Returns
    -------
    df : Pandas Dataframe
        A dataframe containing the BGP neighbors.

    Examples
    --------
    >>> df = ospf_neighbors(username,
                            password,
                            host_group,
                            nm_path,
                            private_data_dir)
    >>> df.columns.to_list()
    ['device',
    'virtual-router',
    'neighbor-address',
    'local-address-binding',
    'type',
    'status',
    'neighbor-router-id',
    'area-id',
    'neighbor-priority',
    'lifetime-remain',
    'messages-pending',
    'lsa-request-pending',
    'options',
    'hello-suppressed',
    'restart-helper-status',
    'restart-helper-time-remaining',
    'restart-helper-exit-reason',
    'timestamp']
    """

    cmd = "show routing protocol bgp peer"
    cmd_is_xml = False

    response = run_adhoc_command(
        username, password, host_group, nm_path, private_data_dir, cmd, cmd_is_xml
    )

    # Parse results into df
    return parser.parse_bgp_neighbors(response)


def get_all_interfaces(
    username: str,
    password: str,
    host_group: str,
    nm_path: str,
    private_data_dir: str,
    db_path: str,
    serials: list = [],
) -> pd.DataFrame:
    """
    Gets all interfaces on Palo Altos. If a list of serial numbers is provided, then it
    will treat the devices in the hostgroup as Panoramas and try to context switch to
    each serial number and run the 'show interface all' command. (The interfaces for the
    Panoramas will still be returned, even if serial numbers are provided.)

    Parameters
    ----------
    username : str
        The user's username.
    password : str
        The user's password.
    host_group : str
        The name of the Ansible inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    private_data_dir : str
        The path to the Ansible private data directory
    db_path : str
        The full path to the database.
    serials : list, optional
        The serial numbers of the devices to run the command on. They are
        ignored if the devices in the host_group are not Panoramas.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the logical interfaces.

    Examples
    --------
    >>> df = get_all_interfaces(username,
                                password,
                                host_group,
                                nm_path,
                                play_path,
                                db_path,
                                private_data_dir)
    >>> df.columns.to_list()
    ['device',
    'name',
    'zone',
    'fwd',
    'vsys',
    'dyn-addr',
    'addr6',
    'tag',
    'ip',
    'id',
    'addr']
    """
    cmd = "show interface all"
    cmd_is_xml = False

    df = pd.DataFrame()

    # If serial numbers were provided, then get the interfaces for them.
    if serials:
        for serial in serials:
            response = run_adhoc_command(
                username,
                password,
                host_group,
                nm_path,
                private_data_dir,
                cmd,
                cmd_is_xml,
                serial,
            )
            df_response = parser.parse_all_interfaces(response)
            df_response.insert(0, "serial", serial)
            df = pd.concat([df, df_response])

    # If serial numbers were provided, then get the device names for those serials.
    if serials:
        df = pah.get_device_name_from_serial(df, db_path)

    # Get the interfaces for the devices in the hostgroup. (This method ensures
    # that the Panoramas and other devices in the hostgroup will have their
    # interfaces collected, even if the 'serials' arg is populated.)
    response = run_adhoc_command(
        username, password, host_group, nm_path, private_data_dir, cmd, cmd_is_xml
    )
    df_response = parser.parse_all_interfaces(response)
    df = pd.concat([df, df_response])

    df = df.reset_index(drop=True)

    # Reorder the columns in the DataFrame
    new_column_order = ["device"] + [col for col in df.columns if col != "device"]
    df = df[new_column_order]

    return df


def get_arp_table(
    username: str,
    password: str,
    host_group: str,
    nm_path: str,
    private_data_dir: str,
    serials,
    interface: str = "",
) -> pd.DataFrame:
    """
    Parses the Palo Alto ARP table and adds vendor OUIs.

    Parameters
    ----------
    username : str
        The user's username.
    password : str
        The user's password.
    host_group : str
        The name of the Ansible inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the ARP table and vendor OUIs.

    Other Parameters
    ----------------
    interface : str, optional
        The interface for which to return the ARP table. The default is to
        return the ARP table for all interfaces.

    Examples
    --------
    >>> df = get_arp_table(username,
                           password,
                           host_group,
                           nm_path,
                           play_path,
                           private_data_dir)
    >>> print(df.columns.to_list())
    ['device', 'status', 'ip', 'mac', 'ttl', 'interface', 'port', 'vendor']

    >>> df = get_arp_table(username,
                           password,
                           host_group,
                           nm_path,
                           play_path,
                           private_data_dir,
                           interface=interface)
    >>> print(df.columns.to_list())
    ['device', 'status', 'ip', 'mac', 'ttl', 'interface', 'port', 'vendor']
    """
    if interface:
        cmd = f"<show><arp><entry name='{interface}'/></arp></show>"
    else:
        cmd = "<show><arp><entry name='all'/></arp></show>"

    response = run_adhoc_command(
        username, password, host_group, nm_path, private_data_dir, cmd, True
    )

    # Parse results into df
    return parser.parse_arp_table(response, nm_path)


def get_interface_ips(
    username: str,
    password: str,
    host_group: str,
    nm_path: str,
    private_data_dir: str,
    db_path: str,
    serials: list = [],
) -> pd.DataFrame:
    """
    Gets interface IPs on Palo Altos. If a list of serial numbers is provided, then it
    will treat the devices in the hostgroup as Panoramas and try to context switch to
    each serial number and get their IPs. (The IP addresses for the Panoramas will
    still be returned, even if serial numbers are provided.)

    Parameters
    ----------
    username : str
        The user's username.
    password : str
        The user's password.
    host_group : str
        The name of the Ansible inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    private_data_dir : str
        The path to the Ansible private data directory.
    db_path : str
        The full path to the database.
    serials : list, optional
        The serial numbers of the devices to run the command on. They are
        ignored if the devices in the host_group are not Panoramas.

    Returns
    -------
    df : Pandas Dataframe
        A dataframe containing the IP addresses.

    Examples
    --------
    >>> df = get_ip_addresses(username,
                              password,
                              db_path,
                              host_group,
                              nm_path,
                              play_path,
                              private_data_dir,
                              timestamp)
    >>> df.columns.to_list()
    ['device',
    'name',
    'zone',
    'fwd',
    'vsys',
    'dyn-addr',
    'addr6',
    'tag',
    'ip',
    'id',
    'addr']
    """
    # TODO: Optimize this function by setting 'get_all_interfaces' as a
    #       dependency. That way the same command does not need to be
    #       run twice (potentially) for two different collectors.
    df = get_all_interfaces(
        username,
        password,
        host_group,
        nm_path,
        private_data_dir,
        db_path,
        serials=serials,
    )

    # Parse results into df
    return parser.parse_interface_ips(df)


def get_logical_interfaces(
    username: str,
    password: str,
    host_group: str,
    nm_path: str,
    private_data_dir: str,
    serials: list = [],
) -> pd.DataFrame:
    """
    Gets the logical interfaces on Palo Altos.

    Parameters
    ----------
    username : str
        The user's username.
    password : str
        The user's password.
    host_group : str
        The name of the Ansible inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the logical interfaces.

    Examples
    --------
    >>> df = get_logical_interfaces(username,
                                    password,
                                    host_group,
                                    nm_path,
                                    play_path,
                                    private_data_dir)
    >>> df.columns.to_list()
    ['device',
    'name',
    'zone',
    'fwd',
    'vsys',
    'dyn-addr',
    'addr6',
    'tag',
    'ip',
    'id',
    'addr']
    """
    cmd = "show interface logical"
    cmd_is_xml = False

    response = run_adhoc_command(
        username, password, host_group, nm_path, private_data_dir, cmd, cmd_is_xml
    )

    # Parse results into df
    return parser.parse_logical_interfaces(response)


def get_physical_interfaces(
    username: str,
    password: str,
    host_group: str,
    nm_path: str,
    private_data_dir: str,
    serials: list = [],
) -> pd.DataFrame:
    """
    Gets the physical interfaces on Palo Altos.

    Parameters
    ----------
    username : str
        The user's username.
    password : str
        The user's password.
    host_group : str
        The name of the Ansible inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the physical interfaces.

    Examples
    --------
    >>> df = get_physical_interfaces(username,
                                     password,
                                     host_group,
                                     nm_path,
                                     play_path,
                                     private_data_dir)
    >>> df.columns.to_list()
    ['device',
    'name',
    'duplex',
    'type',
    'state',
    'st',
    'mac',
    'mode',
    'speed',
    'id']
    """
    cmd = "show interface hardware"
    cmd_is_xml = False
    response = run_adhoc_command(
        username, password, host_group, nm_path, private_data_dir, cmd, cmd_is_xml
    )

    # Parse results into df
    return parser.parse_physical_interfaces(response)


def get_security_rules(
    username: str,
    password: str,
    host_group: str,
    play_path: str,
    private_data_dir: str,
    serials,
    device_group: str = "shared",
) -> pd.DataFrame:
    """
    Get a list of all security rules from a Palo Alto firewall.

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
    device_group : str, optional
        The device group to query. Defaults to 'shared'.

    Returns
    -------
    df_rules : pd.DataFrame
        A DataFrame containing the security rules.
    """
    extravars = {
        "user": username,
        "password": password,
        "device_group": device_group,
        "host_group": host_group,
    }

    playbook = f"{play_path}/palo_alto_get_security_rules.yml"
    runner = ansible_runner.run(
        private_data_dir=private_data_dir,
        playbook=playbook,
        extravars=extravars,
        suppress_env_files=True,
    )

    # Parse results into df
    return parser.parse_security_rules(runner)


def ospf_neighbors(
    username: str,
    password: str,
    host_group: str,
    nm_path: str,
    private_data_dir: str,
    serials: list = [],
) -> pd.DataFrame:
    """Gets OSPF neighbors for Palo Alto firewalls.

    Parameters
    ----------
    username : str
        The user's username.
    password : str
        The user's password.
    host_group : str
        The name of the Ansible inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    private_data_dir : str
        The path to the Ansible private data directory.

    Returns
    -------
    df : Pandas Dataframe
        A dataframe containing the OSPF neighbors.

    Examples
    --------
    >>> df = ospf_neighbors(username,
                            password,
                            host_group,
                            nm_path,
                            private_data_dir)
    >>> df.columns.to_list()
    ['device',
    'virtual-router',
    'neighbor-address',
    'local-address-binding',
    'type',
    'status',
    'neighbor-router-id',
    'area-id',
    'neighbor-priority',
    'lifetime-remain',
    'messages-pending',
    'lsa-request-pending',
    'options',
    'hello-suppressed',
    'restart-helper-status',
    'restart-helper-time-remaining',
    'restart-helper-exit-reason',
    'timestamp']
    """

    cmd = "show routing protocol ospf neighbor"
    cmd_is_xml = False

    response = run_adhoc_command(
        username, password, host_group, nm_path, private_data_dir, cmd, cmd_is_xml
    )

    # Parse results into df
    return parser.parse_ospf_neighbors(response)


def panorama_get_managed_devices(
    username, password, host_group, nm_path, private_data_dir
):
    cmd = "show devices connected"
    cmd_is_xml = False

    response = run_adhoc_command(
        username, password, host_group, nm_path, private_data_dir, cmd, cmd_is_xml
    )

    return parser.panorama_get_managed_devices(response).astype(str)
