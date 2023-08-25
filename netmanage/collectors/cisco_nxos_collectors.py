#!/usr/bin/env python3

import ansible_runner
import pandas as pd
import sqlite3 as sl

from netmanage.parsers import cisco_nxos_parsers as parser


def nxos_diff_running_config(username: str,
                             password: str,
                             host_group: str,
                             play_path: str,
                             private_data_dir: str,
                             nm_path: str,
                             interface: str = None) -> pd.DataFrame:
    '''
    Gets the running-config diff for NXOS devices.

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
    nm_path : str
        The path to the Net-Manage repository.

    Returns
    -------
    df_diff : pd.DataFrame
        The diff.
    '''
    cmd = 'show running-config diff'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the command and parse the output
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_diff_running_config(runner)


def nxos_get_arp_table(username: str,
                       password: str,
                       host_group: str,
                       nm_path: str,
                       play_path: str,
                       private_data_dir: str,
                       reverse_dns: bool = False) -> pd.DataFrame:
    '''
    Get the ARP table for Cisco NXOS devices and retrieve the OUI (vendor) for
    each MAC address. Optionally, perform a reverse DNS query for hostnames,
    but note that it may take several minutes for large datasets.

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
    reverse_dns : bool, optional
        Whether to perform a reverse DNS lookup. Defaults to False because the
        operation can be time-consuming for large ARP tables.

    Returns
    -------
    df_arp : pd.DataFrame
        The ARP table as a pandas DataFrame.
    '''
    cmd = 'show ip arp vrf all | begin "Address         Age"'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_arp_table(runner, nm_path)


def nxos_get_fexes_table(username: str,
                         password: str,
                         host_group: str,
                         nm_path: str,
                         play_path: str,
                         private_data_dir: str) -> pd.DataFrame:
    '''
    Get the FEXes for Cisco 5Ks. This function is required for gathering
    interface data on devices with a large number of FEXes, as it helps
    prevent timeouts.

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
    df_fexes : pd.DataFrame
        The FEXes of the device. If there are no FEXes, an empty DataFrame
        will be returned.
    '''
    # Get selected FEX details
    cmd = 'show fex detail'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the command and parse the output
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_fexes_table(runner)


def nxos_get_bgp_neighbors(username: str,
                           password: str,
                           host_group: str,
                           nm_path: str,
                           play_path: str,
                           private_data_dir: str) -> pd.DataFrame:
    '''
    Get the BGP neighbors for all VRFs on NXOS devices.

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
    df_bgp : pd.DataFrame
        The BGP neighbors as a pandas DataFrame.
    '''
    cmd = 'show ip bgp summary vrf all'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the command and parse the output
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_bgp_neighbors(runner)


def nxos_get_cam_table(username: str,
                       password: str,
                       host_group: str,
                       nm_path: str,
                       play_path: str,
                       private_data_dir: str,
                       interface: str = None) -> pd.DataFrame:
    '''
    Get the CAM table for NXOS devices and add the vendor OUI.

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
    '''
    if interface:
        cmd = f'show mac address-table interface {interface}'
    else:
        cmd = 'show mac address-table'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_cam_table(runner, nm_path)


def nxos_get_hostname(username: str,
                      password: str,
                      host_group: str,
                      play_path: str,
                      private_data_dir: str,
                      nm_path: str,
                      interface: str = None) -> pd.DataFrame:
    '''
    Get the hostname for NXOS devices.

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
    nm_path : str
        The path to the Net-Manage repository.

    Returns
    -------
    df_name : pd.DataFrame
        The hostname as a pandas DataFrame.
    '''
    cmd = 'show hostname'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the command and parse the output
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_hostname(runner)


def nxos_get_interface_descriptions(username: str,
                                    password: str,
                                    host_group: str,
                                    play_path: str,
                                    private_data_dir: str,
                                    interface: str = None) -> pd.DataFrame:
    '''
    Get NXOS interface descriptions.

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
        The interface descriptions as a pandas DataFrame.
    '''
    # Get the interface descriptions and add them to df_cam
    cmd = 'show interface description | grep -v "\\-\\-\\-\\-"'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute 'show interface description' and parse the results
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)
    # Parse results into df
    return parser.nxos_parse_interface_descriptions(runner)


def nxos_get_interface_ips(username: str,
                           password: str,
                           host_group: str,
                           play_path: str,
                           private_data_dir: str) -> pd.DataFrame:
    '''
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
        A DataFrame containing the interfaces and their corresponding IP
        addresses.
    '''
    grep = 'Interface status:\\|IP address:\\|IP Interface Status for VRF'
    cmd = f'show ip interface vrf all | grep "{grep}"'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the command
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_interface_ips(runner)


def nxos_get_interface_status(username: str,
                              password: str,
                              host_group: str,
                              play_path: str,
                              private_data_dir: str) -> pd.DataFrame:
    '''
    Get the interface status for NXOS devices.

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
    df_inf_status : pd.DataFrame
        The interface statuses as a pandas DataFrame.
    '''
    cmd = 'show interface status | grep -v "\\-\\-\\-"'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_interface_status(runner)


def nxos_get_interface_summary(db_path: str) -> pd.DataFrame:
    '''
    Get a summary of the interfaces on a NXOS devices. The summary includes
    the interface status, description, associated MACs, and vendor OUIs.

    Parameters
    ----------
    db_path : str
        The path to the database.

    Returns
    -------
    df_summary : pd.DataFrame
        The summaries of interfaces on the devices as a pandas DataFrame.
    '''
    # Get the interface statuses, descriptions and cam table
    con = sl.connect(db_path)
    table = 'nxos_interface_status'
    df_ts = pd.read_sql(f'select distinct timestamp from {table}', con)
    ts = df_ts['timestamp'].to_list()[-1]
    df_inf = pd.read_sql(f'select * from {table} where timestamp = "{ts}"',
                         con)

    # Parse results into df
    return parser.nxos_parse_interface_summary(df_inf, con, ts)


def nxos_get_inventory(username: str,
                       password: str,
                       host_group: str,
                       play_path: str,
                       private_data_dir: str) -> pd.DataFrame:
    '''
    Get the inventory for NXOS devices.

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
    df_inventory : pd.DataFrame
        A DataFrame containing the output of the 'show inventory | json'
        command.
    '''
    # Create the playbook variables
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}
    playbook = f'{play_path}/cisco_nxos_get_inventory.yml'

    # Execute the playbook
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_inventory(runner)


def nxos_get_logs(username: str,
                  password: str,
                  host_group: str,
                  play_path: str,
                  private_data_dir: str) -> pd.DataFrame:
    '''
    Get the latest log messages for NXOS devices.

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
    df_logs : pd.DataFrame
        The latest log messages as a pandas DataFrame.
    '''
    cmd = 'show logging last 999'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_logs(runner)


def nxos_get_port_channel_data(username: str,
                               password: str,
                               host_group: str,
                               play_path: str,
                               private_data_dir: str) -> pd.DataFrame:
    '''
    Get port-channel data (output from 'show port-channel database') for Cisco
    NXOS devices.

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
    df_po_data : pd.DataFrame
        The port-channel data as a pandas DataFrame.
    '''
    cmd = 'show port-channel database'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_port_channel_data(runner)


def nxos_get_vlan_db(username: str,
                     password: str,
                     host_group: str,
                     play_path: str,
                     private_data_dir: str) -> pd.DataFrame:
    '''
    Get the VLAN database for NXOS devices.

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
    df_vlans : pd.DataFrame
        The VLAN database as a pandas DataFrame.
    '''
    cmd = 'show vlan brief | grep "Status    Ports\\|active\\|suspend\\|shut"'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'ansible_command_timeout': '240',
                 'commands': cmd}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_vlan_db(runner)


def nxos_get_vpc_state(username: str,
                       password: str,
                       host_group: str,
                       play_path: str,
                       private_data_dir: str) -> pd.DataFrame:
    '''
    Get the VPC state for NXOS devices.

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
    df_vpc_state : pd.DataFrame
        The VPC state information as a pandas DataFrame.
    '''
    cmd = 'show vpc brief | begin "vPC domain id" | end "vPC Peer-link status"'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_vpc_state(runner)


def nxos_get_vrfs(username: str,
                  password: str,
                  host_group: str,
                  play_path: str,
                  private_data_dir: str) -> pd.DataFrame:
    '''
    Get the VRFs on Nexus devices.

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
    df_vrfs : pd.DataFrame
        A DataFrame containing the VRFs.
    '''
    cmd = 'show vrf detail'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_nxos_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse results into df
    return parser.nxos_parse_vrfs(runner)
