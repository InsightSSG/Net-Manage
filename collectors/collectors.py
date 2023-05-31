#!/usr/bin/env python3

'''
A library of functions for collecting data from network devices.
'''

import ansible_runner
import ipaddress
import json
import pandas as pd
import re
import sqlite3 as sl

from helpers import helpers as hp


def asa_get_interface_ips(username,
                          password,
                          host_group,
                          play_path,
                          private_data_dir):
    '''
    Gets the IP addresses assigned to interfaces on Cisco ASA devices.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory

    Returns:
        df_ip (df):             A DataFrame containing the interfaces and IPs
    '''
    # cmd = ['show ip interface',
    #        '|',
    #        'include line protocol|Internet address is|VPN Routing']
    # cmd = ' '.join(cmd)
    cmd = 'show interface summary | include Interface|IP address'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the command
    playbook = f'{play_path}/cisco_asa_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse the results
    df_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

            output = [_.strip('\t') for _ in output]

            output = [_ for _ in output if _.split()[0] == 'Interface' or
                      ' '.join(_.split()[:2]) == 'IP address']

            counter = 0
            for line in output:
                counter += 1
                line = line.split(',')
                if line[0].split()[0] == 'Interface' and \
                        '"' in line[0].split()[-1]:
                    inf = line[0].split()[1]
                    nameif = line[0].split()[2].strip('"')

                    _line = output[counter]
                    if 'unassigned' in _line:
                        ip = 'unassigned'
                        netmask = 'unassigned'
                    else:
                        ip = _line.split(',')[0].split()[-1]
                        netmask = _line.split(',')[-1].split()[-1]
                        cidr = hp.convert_mask_to_cidr(netmask)
                        ip = f'{ip}/{cidr}'

                    row = [device, inf, ip, nameif]
                    df_data.append(row)
    # Create a dataframe from df_data and return it
    cols = ['device', 'interface', 'ip', 'nameif']
    df_ip = pd.DataFrame(data=df_data, columns=cols)
    return df_ip


def ios_find_uplink_by_ip(username,
                          password,
                          host_group,
                          play_path,
                          private_data_dir,
                          subnets=list()):
    '''
    Searches the hostgroup for a list of subnets (use /32 to esarch for a
    single IP). Once it finds them, it uses CDP and LLDP (if applicable) to try
    to find the uplink.

    If a list of IP addresses is not provided, it will attempt to find the
    uplinks for all IP addresses on the devices.

    This is a simple function that was writting for a single use case. It has
    some limitations:

    1. There is not an option to specify the VRF (although it will still return
       the uplinks for every IP that meets the parameters)
    2. If CDP and LLDP are disabled or the table is not populated, it does not
       try alternative methods like interface descriptions and CAM tables. I
       can add those if there is enough interest in this function.

    TODOs:
    - Add alternative methods if CDP and LLDP do not work:
      - Interface descriptions
      - Reverse DNS (in the case of P2P IPs)
      - CAM table
    - Add option to specify the VRF (low priority)

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        addresses (list):       (Optional) A list of one or more subnets to
                                search for. Use CIDR notation. Use /32 to
                                search for individual IPs. If no list is
                                provided then the function will try to find the
                                uplinks for all IP addresses on the devices.

    Returns:
        df_combined (DF):       A DataFrame containing IP > remote port mapping
    '''

    # Get the IP addresses on the devices in the host group
    df_ip = ios_get_interface_ips(username,
                                  password,
                                  host_group,
                                  play_path,
                                  private_data_dir)

    # Get the CDP neighbors for the device
    df_cdp = ios_get_cdp_neighbors(username,
                                   password,
                                   host_group,
                                   play_path,
                                   private_data_dir)

    # Remove the sub-interfaces from df_ip
    local_infs = df_ip['Interface'].to_list()
    local_infs = [inf.split('.')[0] for inf in local_infs]
    df_ip['Interface'] = local_infs

    # Attempt to find the neighbors for the interfaces that have IPs
    df_data = list()

    for idx, row in df_ip.iterrows():
        device = row['Device']
        inf = row['Interface']
        neighbor_row = df_cdp.loc[(df_cdp['Device'] == device) &
                                  (df_cdp['Local Inf'] == inf)]
        remote_device = list(neighbor_row['Neighbor'].values)
        if remote_device:
            remote_device = remote_device[0]
            remote_inf = list(neighbor_row['Remote Inf'].values)[0]
        else:
            remote_device = 'unknown'
            remote_inf = 'unknown'
        mgmt_ip = row['IP']
        df_data.append([device, mgmt_ip, inf, remote_device, remote_inf])
    # Create a DataFrame and return it
    cols = ['Device',
            'IP',
            'Local Interface',
            'Remote Device',
            'Remote Interface']
    df_combined = pd.DataFrame(data=df_data, columns=cols)

    return df_combined


def ios_get_arp_table(username,
                      password,
                      host_group,
                      nm_path,
                      play_path,
                      private_data_dir):
    '''
    Gets the IOS ARP table and adds the vendor OUI.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        nm_path (str):          The path to the Net-Manage repository
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        interface (str):        The interface (defaults to all interfaces)

    Returns:
        df_arp (DataFrame):     The ARP table and vendor OUI
    '''
    cmd = 'show ip arp'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_ios_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Create the column headers. I do not like to hard code these, but they
    # should be modified from Cisco's format before being stored in a
    # database. I suppose it is not strictly necessary to do so, but
    # "Age (min)" and "Hardware Addr" do not make for good column headers.
    columns = ['device',
               'protocol',
               'address',
               'age',
               'mac',
               'inf_type',
               'interface']

    # Parse the output and add it to 'data'
    df_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

            for line in output[1:]:
                row = [device] + line.split()
                df_data.append(row)

    # Create the DataFrame
    df_arp = pd.DataFrame(data=df_data, columns=columns)

    # Get the vendor OUIs
    df_vendors = hp.find_mac_vendors(df_arp['mac'], nm_path)

    # Add the vendor OUIs to df_cam as a column, and return the dataframe.
    df_arp['vendor'] = df_vendors['vendor']

    return df_arp


def ios_get_cam_table(username,
                      password,
                      host_group,
                      nm_path,
                      play_path,
                      private_data_dir,
                      interface=None):
    '''
    Gets the IOS CAM table and adds the vendor OUI.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        nm_path (str):          The path to the Net-Manage repository
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        interface (str):        The interface (defaults to all interfaces)

    Returns:
        df_cam (DataFrame):     The CAM table and vendor OUI
    '''
    if interface:
        cmd = f'show mac address-table interface {interface}'
    else:
        cmd = 'show mac address-table | begin Vlan'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_ios_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Create the column headers. I do not like to hard code these, but they
    # should be modified from Cisco's format before being stored in a
    # database. I suppose it is not strictly necessary to do so, but
    # "Mac Address" and "Type" do not make good column headers.
    columns = ['device',
               'vlan',
               'mac',
               'inf_type',
               'ports']

    # Parse the output and add it to 'data'
    df_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')
            # columns = list(filter(None, output[0].split('  ')))
            # columns.insert(0, 'device')
            # columns = [_.strip() for _ in columns]

            for line in output[2:-1]:
                row = [device] + line.split()
                df_data.append(row)

    # Create the DataFrame
    df_cam = pd.DataFrame(data=df_data, columns=columns)

    # Get the vendor OUIs
    df_vendors = hp.find_mac_vendors(df_cam['mac'], nm_path)

    # Add the vendor OUIs to df_cam as a column, and return the dataframe.
    df_cam['vendor'] = df_vendors['vendor']

    return df_cam


def ios_get_cdp_neighbors(username,
                          password,
                          host_group,
                          play_path,
                          private_data_dir,
                          interface=str()):
    '''
    Gets the CDP neighbors for a Cisco IOS device.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        interface (str):        The interface to get the neighbor entry for. If
                                not specified, it will get all neighbors.

    Returns:
        df_cdp (DataFrame):     A DataFrame containing the CDP neighbors
    '''
    cmd = 'show cdp neighbor detail | include Device ID|Interface'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the command
    playbook = f'{play_path}/cisco_ios_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse the results
    cdp_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')
            pos = 1  # Used to account for multiple connections to same device
            for line in output:
                if 'Device ID' in line:
                    remote_device = line.split('(')[0].split()[2].split('.')[0]
                    local_inf = output[pos].split()[1].strip(',')
                    remote_inf = output[pos].split()[-1]
                    row = [device, local_inf, remote_device, remote_inf]
                    cdp_data.append(row)
                pos += 1
    # Create a dataframe from cdp_data and return the results
    cols = ['Device', 'Local Inf', 'Neighbor', 'Remote Inf']
    df_cdp = pd.DataFrame(data=cdp_data, columns=cols)
    return df_cdp


def ios_get_interface_descriptions(username,
                                   password,
                                   host_group,
                                   play_path,
                                   private_data_dir,
                                   interface=None):
    '''
    Gets IOS interface descriptions.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        interface (str):        The interface (defaults to all interfaces)

    Returns:
        df_desc (DataFrame):    The interface descriptions
    '''
    # Get the interface descriptions and add them to df_cam
    cmd = 'show interface description'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute 'show interface description' and parse the results
    playbook = f'{play_path}/cisco_ios_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)
    # Create a list to store the rows for the dataframe
    df_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')
            # Get the position of the 'Description' column (we cannot split by
            # spaces because some interface descriptions have spaces in them).
            pos = output[0].index('Description')
            for line in output[1:]:
                inf = line.split()[0]
                desc = line[pos:]
                df_data.append([device, inf, desc])

    # Create the dataframe and return it
    cols = ['device', 'interface', 'description']
    df_desc = pd.DataFrame(data=df_data, columns=cols)
    return df_desc


def ios_get_interface_ips(username,
                          password,
                          host_group,
                          play_path,
                          private_data_dir):
    '''
    Gets the IP addresses assigned to interfaces.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory

    Returns:
        df_ip (df):             A DataFrame containing the interfaces and IPs
    '''
    cmd = ['show ip interface',
           '|',
           'include line protocol|Internet address is|VPN Routing']
    cmd = ' '.join(cmd)
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the command
    playbook = f'{play_path}/cisco_ios_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse the results
    df_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')
            output.reverse()  # Reverse the output to make it easier to iterate
            counter = 0
            for line in output:
                if 'Internet address' in line:
                    pos = counter
                    if 'VPN Routing/Forwarding' in output[pos-1]:
                        vrf = output[pos-1].split()[-1].strip('"')
                    else:
                        vrf = 'None'
                    ip = line.split()[-1]
                    inf = output[pos+1].split()[0]
                    row = [device, inf, ip, vrf]
                    df_data.append(row)
                counter += 1

    # Create a dataframe from df_data and return it
    df_data.reverse()
    cols = ['device', 'interface', 'ip', 'vrf']
    df_ip = pd.DataFrame(data=df_data, columns=cols)
    return df_ip


def nxos_diff_running_config(username,
                             password,
                             host_group,
                             play_path,
                             private_data_dir,
                             nm_path,
                             interface=None):
    '''
    Gets the running-config diff for NXOS devices.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        interface (str):        The interface (defaults to all interfaces)
        nm_path (str):          The path to the Net-Manage repository

    Returns:
        df_diff (DataFrame):    The diff
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

    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')[3:]

            for line in output:
                df_data.append([device, line])

    # Create the dataframe and return it
    cols = ['device', 'diff']
    df_diff = pd.DataFrame(data=df_data, columns=cols)

    return df_diff


def nxos_get_arp_table(username,
                       password,
                       host_group,
                       nm_path,
                       play_path,
                       private_data_dir,
                       reverse_dns=False):
    '''
    Gets the ARP table for Cisco NXOS devices. Also returns the OUI (vendor)
    for the MAC address. Will also return a reverse DNS query, but only if the
    user requests it (it can take several minutes for large datasets).

    TODO: Create a standalone function for reverse DNS queries

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        nm_path (str):          The path to the Net-Manage repository
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        reverse_dns (bool):     Whether to run a reverse DNS lookup. Defaults
                                to False because the test can take several
                                minutes on large ARP tables.

    Returns:
        df_arp (DataFrame):     The ARP table
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

    # Parse the output and add it to 'data'
    df_data = list()

    # Create a list of mac addresses (used for querying the vendor)
    macs = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

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

    cols = ['device',
            'ip_address',
            'age',
            'mac_address',
            'interface']

    # TODO: Convert this to a standalone function
    # if reverse_dns:
    #     cols.append('reverse_dns')

    df_arp = pd.DataFrame(data=df_data, columns=cols)

    # Find the vendrs and add them to the dataframe
    df_vendors = hp.find_mac_vendors(macs, nm_path)
    df_arp['vendor'] = df_vendors['vendor']

    return df_arp


def nxos_get_fexes_table(username,
                         password,
                         host_group,
                         nm_path,
                         play_path,
                         private_data_dir):
    '''
    Gets the FEXes for Cisco 5Ks. This function is required for gathering
    interface data on devices with lots of FEXes. Otherwise there will be
    timeouts.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        nm_path (str):          The path to the Net-Manage repository
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory

    Returns:
        df_fexes (DataFrame):   The device FEXes (if there are not any then an
                                empty dataframe will be returned).
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

    # Parse the output and add it to 'data'
    df_data = list()

    # Create a list of mac addresses (used for querying the vendor)
    macs = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

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

    cols = ['device',
            'ip_address',
            'age',
            'mac_address',
            'interface']

    # TODO: Convert this to a standalone function
    # if reverse_dns:
    #     cols.append('reverse_dns')

    df_arp = pd.DataFrame(data=df_data, columns=cols)

    # Find the vendrs and add them to the dataframe
    vendors = hp.find_mac_vendors(macs, nm_path)
    df_arp['vendor'] = vendors

    return df_arp


def nxos_get_bgp_neighbors(username,
                           password,
                           host_group,
                           nm_path,
                           play_path,
                           private_data_dir):
    '''
    Gets the BGP neighbors for all VRFs on NXOS devices.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        nm_path (str):          The path to the Net-Manage repository
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory

    Returns:
        df_bgp (DataFrame):     The BGP neighbors
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

    # Necessary to keep from exceeding 80-character line length
    address = ipaddress.ip_address

    # Phrase to search for to find the start of VRF neighbors
    phrase = 'BGP summary information for VRF'

    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']
            output = event_data['res']['stdout'][0].split('\n')
            for line in output:
                if phrase in line:
                    vrf = line.split(',')[0].split()[-1]
                    pos = output.index(line)+1
                    if pos < len(output):
                        while phrase not in output[pos]:
                            try:
                                if address(output[pos].split()[0]):
                                    row = output[pos].split()
                                    df_data.append([device,
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
                                                    row[9]])
                            except Exception:
                                pass
                            pos += 1
                            if pos == len(output):
                                break

    # Create dataframe and return it
    cols = ['device',
            'vrf',
            'neighbor_id',
            'version',
            'as',
            'msg_received',
            'message_sent',
            'table_version',
            'in_q',
            'out_q',
            'up_down',
            'state_pfx_rfx']
    df_bgp = pd.DataFrame(data=df_data, columns=cols)
    return df_bgp


def nxos_get_cam_table(username,
                       password,
                       host_group,
                       nm_path,
                       play_path,
                       private_data_dir,
                       interface=None):
    '''
    Gets the CAM table for NXOS devices and adds the vendor OUI.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        nm_path (str):          The path to the Net-Manage repository
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        interface (str):        The interface (defaults to all interfaces)

    Returns:
        df_cam (DataFrame):     The CAM table and vendor OUI
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

    # Define the RegEx pattern for a valid MAC address
    # pattern = '([0-9a-f]{4}\.[0-9a-f]{4}\.[0-9a-f]{4})'
    pattern = '.*[a-zA-Z0-9]{4}\\.[a-zA-Z0-9]{4}\\.[a-zA-Z0-9]{4}.*'

    # Create a list to store MAC addresses
    addresses = list()

    # Parse the output and add it to 'data'
    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0]

            output = re.findall(pattern, output)
            for line in output:
                mac = line.split()[2]
                interface = line.split()[-1]
                vlan = line.split()[1]
                df_data.append([device, interface, mac, vlan])

    # Create the dataframe and return it
    cols = ['device',
            'interface',
            'mac',
            'vlan']
    df_cam = pd.DataFrame(data=df_data, columns=cols)

    # Get the OUIs and add them to df_cam
    addresses = df_cam['mac'].to_list()
    df_vendors = hp.find_mac_vendors(addresses, nm_path)
    df_cam['vendor'] = df_vendors['vendor']

    # Return df_cam
    return df_cam


def nxos_get_hostname(username,
                      password,
                      host_group,
                      play_path,
                      private_data_dir,
                      nm_path,
                      interface=None):
    '''
    Gets the hostname for NXOS devices.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        interface (str):        The interface (defaults to all interfaces)
        nm_path (str):          The path to the Net-Manage repository

    Returns:
        df_name (DataFrame):    The hostname
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

    df_data = dict()
    df_data['device'] = list()
    df_data['hostname'] = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0]

            df_data['device'].append(device)
            df_data['hostname'].append(output)

    # Create the dataframe and return it
    df_name = pd.DataFrame.from_dict(df_data)

    return df_name


def nxos_get_interface_descriptions(username,
                                    password,
                                    host_group,
                                    play_path,
                                    private_data_dir,
                                    interface=None):
    '''
    Gets NXOS interface descriptions.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        interface (str):        The interface (defaults to all interfaces)

    Returns:
        df_desc (DataFrame):    The interface descriptions
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
    # Create a list to store the rows for the dataframe
    df_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')
            output = list(filter(None, output))
            # NXOS does not have consistent column widths. Therefore, we must
            # re-index the position of the 'Description' column every time it
            # occurs.
            for _ in output:
                if ('Port' in _ or 'Interface' in _) and 'Description' in _:
                    pos = _.index('Description')
                else:
                    inf = _.split()[0]
                    desc = _[pos:].strip()
                    df_data.append([device, inf, desc])

    # Create the dataframe and return it
    cols = ['device', 'interface', 'description']
    df_desc = pd.DataFrame(data=df_data, columns=cols)
    return df_desc


def nxos_get_interface_ips(username,
                           password,
                           host_group,
                           play_path,
                           private_data_dir):
    '''
    Gets the IP addresses assigned to interfaces.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory

    Returns:
        df_ip (df):             A DataFrame containing the interfaces and IPs
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

    # Parse the results
    df_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

            counter = 0
            for line in output:
                if 'IP Interface Status for VRF' in line:
                    vrf = line.split()[-1].strip('"')

                if 'IP address:' in line:
                    pos = counter
                    inf = output[pos-1].split(',')[0]
                    ip = line.split(',')[0].split()[-1]
                    subnet = line.split(',')[1].split()[2].split('/')[-1]
                    ip = f'{ip}/{subnet}'
                    row = [device, inf, ip, vrf]
                    df_data.append(row)

                counter += 1

    # Create a dataframe from df_data and return it
    cols = ['device', 'interface', 'ip', 'vrf']
    df_ip = pd.DataFrame(data=df_data, columns=cols)
    return df_ip


def nxos_get_interface_status(username,
                              password,
                              host_group,
                              play_path,
                              private_data_dir):
    '''
    Gets the interface status for NXOS devices.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        nm_path (str):          The path to the Net-Manage repository

    Returns:
        df_inf_status (DataFrame): The interface statuses
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

    # Parse the output and add it to 'data'
    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')
            output = list(filter(None, output))

            # Get the positions of the header columns (except Port and Name)
            header = output[0]
            pos_status = header.index('Status')
            pos_vlan = header.index('Vlan')
            pos_duplex = header.index('Duplex')
            pos_speed = header.index('Speed')
            pos_type = header.index('Type')

            # Remove lines that repeat the header
            output = [_ for _ in output if 'Port' not in _ and 'type' not in _]

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
    cols = ['device',
            'interface',
            'status',
            'vlan',
            'duplex',
            'speed',
            'type']

    df_inf_status = pd.DataFrame(data=df_data, columns=cols)

    return df_inf_status


def nxos_get_interface_summary(db_path):
    '''
    Gets a summary of the interfaces on a NXOS devices. The summary includes
    the interface status, description, associated MACs, and vendor OUIs.

    Args:
        db_path (str):          The path to the database

    Returns:
        df_summary (DataFrame): The summaries of interfaces on the devices
    '''
    # Get the interface statuses, descriptions and cam table
    con = sl.connect(db_path)
    table = 'nxos_interface_status'
    df_ts = pd.read_sql(f'select distinct timestamp from {table}', con)
    ts = df_ts['timestamp'].to_list()[-1]
    df_inf = pd.read_sql(f'select * from {table} where timestamp = "{ts}"',
                         con)

    df_data = dict()
    df_data['device'] = list()
    df_data['interface'] = list()
    df_data['status'] = list()
    df_data['description'] = list()
    df_data['vendors'] = list()
    df_data['macs'] = list()

    for idx, row in df_inf.iterrows():
        device = row['device']
        inf = row['interface']
        status = row['status']

        query = f'''SELECT mac,vendor
                    FROM nxos_cam_table
                    WHERE timestamp = "{ts}"
                       AND device = "{device}"
                       AND interface = "{inf}"'''
        df_macs = pd.read_sql(query, con)
        if len(df_macs) > 0:
            macs = df_macs['mac'].to_list()
            macs = '|'.join(macs)

            vendors = list()
            for idx, row in df_macs.iterrows():
                vendor = row['vendor']
                if vendor:
                    vendor = vendor.replace(',', str())
                    if vendor not in vendors:
                        vendors.append(vendor)

            vendors = '|'.join(vendors)

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
            desc = desc['description'].to_list()[0]
        else:
            desc = str()

        df_data['device'].append(device)
        df_data['interface'].append(inf)
        df_data['status'].append(status)
        df_data['description'].append(desc)
        df_data['vendors'].append(vendors)
        df_data['macs'].append(macs)

    con.close()

    df_summary = pd.DataFrame.from_dict(df_data)
    df_summary = df_summary[['device',
                             'interface',
                             'status',
                             'description',
                             'vendors',
                             'macs']]

    return df_summary


def nxos_get_inventory(username,
                       password,
                       host_group,
                       play_path,
                       private_data_dir):
    '''
    Gets the interface status for NXOS devices.

    Args:
        username (str):             The username to login to devices
        password (str):             The password to login to devices
        host_group (str):           The inventory host group
        play_path (str):            The path to the playbooks directory
        private_data_dir (str):     The path to the Ansible private data
                                    directory
        nm_path (str):              The path to the Net-Manage repository

    Returns:
        df_inventory (DataFrame):   A dataframe containing the output of the
                                    'show inventory | json' command.
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

    # Create a list for holding the inventory items
    data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0]['TABLE_inv']['ROW_inv']

            # Add the inventory items to the 'data' list
            for item in output:
                item['device'] = device
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


def nxos_get_logs(username,
                  password,
                  host_group,
                  play_path,
                  private_data_dir):
    '''
    Gets the latest log messages for NXOS devices.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        nm_path (str):          The path to the Net-Manage repository

    Returns:
        df_logs (DataFrame):    The latest log messages
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

    # Parse the output and add it to 'data'
    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

            for line in output:
                _time = line[:21].strip()
                _msg = line[21:].strip()
                df_data.append([device,
                                _time,
                                _msg])

    # Create the dataframe and return it
    cols = ['device',
            'time',
            'message']

    df_logs = pd.DataFrame(data=df_data, columns=cols)

    return df_logs


def nxos_get_port_channel_data(username,
                               password,
                               host_group,
                               play_path,
                               private_data_dir):
    '''
    Gets port-channel data (output from 'show port-channel database') for Cisco
    NXOS devices.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        nm_path (str):          The path to the Net-Manage repository

    Returns:
        df_po_data (DataFrame): The port-channel data
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

    # Define the dataframe columns
    cols = ['device',
            'interface',
            'total_ports',
            'up_ports',
            'age',
            'port_1',
            'port_2',
            'port_3',
            'port_4',
            'port_5',
            'port_6',
            'port_7',
            'port_8',
            'first_operational_port',
            'last_bundled_member',
            'last_unbundled_member']

    # Create a dictionary to store the data for creating the dataframe
    df_data = dict()
    for c in cols:
        df_data[c] = list()

    # Parse the output and add it to 'data'
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

            # output.append(str())  # For finding the end of database entries
            output = [_ for _ in output if _ != 'Legend:']
            output = [_ for _ in output if '"*":' not in _]

            # TODO: Re-write this using regex to 1) make it more concise, and
            # 2) avoid iterating over 'output' twice

            # Create a list to store database entries
            entries = list()

            pos = 0
            for line in output:
                if line[:12] == 'port-channel':
                    interface = line
                    entry = [interface, device]
                    counter = pos+1
                    while output[counter][:4] == '    ':
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
                    if 'ports in total' in line:
                        total_ports = line.split()[0]
                        up_ports = line.split(',')[-1].split()[0]
                    if 'First operational' in line:
                        first_op_port = line.split()[-1]
                    if 'Last bundled' in line:
                        last_bundled = line.split()[-1]
                    if 'Last unbundled' in line:
                        last_unbundled = line.split()[-1]
                    if 'Age of the' in line:
                        age = line.split()[-1]
                    if ']' in line:
                        port = line.split('Ports:')[-1].strip()
                        ports[counter] = port
                        counter += 1

                # Fill in ports list with ports that exist
                port_num = 1
                for p in ports:
                    key = f'port_{str(port_num)}'
                    df_data[key].append(p)
                    port_num += 1
                # Add remaining variables to df_data
                df_data['interface'].append(interface)
                df_data['device'].append(device)
                df_data['total_ports'].append(total_ports)
                df_data['up_ports'].append(up_ports)
                df_data['age'].append(age)
                df_data['first_operational_port'].append(first_op_port)
                df_data['last_bundled_member'].append(last_bundled)
                df_data['last_unbundled_member'].append(last_unbundled)

    df_po_data = pd.DataFrame.from_dict(df_data)
    # Set dataframe columns to desired order (from 'cols' list)
    df_po_data = df_po_data[cols]

    return df_po_data


def nxos_get_vlan_db(username,
                     password,
                     host_group,
                     play_path,
                     private_data_dir):
    '''
    Gets the VLAN database for NXOS devices.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        nm_path (str):          The path to the Net-Manage repository

    Returns:
        df_vlans (DataFrame):   The VLAN database
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

    # Parse the output and add it to 'data'
    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

            # Get the position of "Ports" column
            pos = output[0].index('Ports')

            for line in output[1:]:
                v_id = line.split()[0]
                name = line.split()[1]
                status = line.split()[2]
                ports = line[pos:].strip()
                df_data.append([device,
                                v_id,
                                name,
                                status,
                                ports])

    # Create the dataframe and return it
    cols = ['device',
            'id',
            'name',
            'status',
            'ports']

    df_vlans = pd.DataFrame(data=df_data, columns=cols)

    return df_vlans


def nxos_get_vpc_state(username,
                       password,
                       host_group,
                       play_path,
                       private_data_dir):
    '''
    Gets the VPC state for NXOS devices.

    Args:
        username (str):           The username to login to devices
        password (str):           The password to login to devices
        host_group (str):         The inventory host group
        play_path (str):          The path to the playbooks directory
        private_data_dir (str):   Path to the Ansible private data directory

    Returns:
        df_vpc_state (DataFrame): The VPC state information
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

    # Parse the output and add it to 'data'
    data = dict()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']
            output = event_data['res']['stdout'][0].split('\n')

            # Remove empty lines
            output = list(filter(None, output))
            # Remove 'vPC Peer-link status'
            output = [_ for _ in output if _ != 'vPC Peer-link status']

            data[device] = dict()
            data[device]['device'] = device
            for line in output:
                col_name = line.split(':')[0].strip()
                data[device][col_name] = line.split(':')[1].strip()

    df_data = dict()
    df_data['device'] = list()
    for key in data:
        for k in data[key]:
            df_data[k] = list()

    for device in data:
        for key in df_data:
            df_data[key].append(data[device].get(key))

    df_vpc_state = pd.DataFrame.from_dict(df_data)

    return df_vpc_state


def nxos_get_vrfs(username,
                  password,
                  host_group,
                  play_path,
                  private_data_dir):
    '''
    Gets the VRFs on Nexus devices.

    Args:
        username (str):           The username to login to devices
        password (str):           The password to login to devices
        host_group (str):         The inventory host group
        play_path (str):          The path to the playbooks directory
        private_data_dir (str):   Path to the Ansible private data directory

    Returns:
    df_vrfs (DataFrame):          A dataframe containing the VRFs
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

    # Parse the output and add it to 'data'
    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

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
                if 'VRF-Name' in line:
                    pos = output.index(line)+1
                    line = line.split(',')
                    line = [_.split(':')[-1].strip() for _ in line]
                    name = line[0]
                    vrf_id = line[1]
                    state = line[2]
                    while 'Table-ID' not in output[pos]:
                        if 'Description:' in output[pos]:
                            description = output[pos+1].strip()
                        if 'VPNID' in output[pos]:
                            vpn_id = output[pos].split(': ')[-1]
                        if 'RD:' in output[pos]:
                            route_domain = output[pos].split()[-1]
                        if 'Max Routes' in output[pos]:
                            _ = output[pos].split(': ')
                            max_routes = _[1].split()[0].strip()
                            min_threshold = _[-1]
                        pos += 1
                    row = [device,
                           name,
                           vrf_id,
                           state,
                           description,
                           vpn_id,
                           route_domain,
                           max_routes,
                           min_threshold]
                    df_data.append(row)

    # Create the DataFrame columns
    cols = ['device',
            'name',
            'vrf_id',
            'state',
            'description',
            'vpn_id',
            'route_domain',
            'max_routes',
            'min_threshold']

    # Create the dataframe and return it
    df_vrfs = pd.DataFrame(data=df_data, columns=cols)

    return df_vrfs


def panos_get_interface_ips(username,
                            password,
                            host_group,
                            play_path,
                            private_data_dir):
    '''
    Gets the interface IP addresses from a Palo Alto firewall.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory

    Returns:
        df_ip (DataFrame):      The interface IP addresses
    '''
    extravars = {'user': username,
                 'password': password,
                 'host_group': host_group}

    playbook = f'{play_path}/palo_alto_get_interface_ip_addresses.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']
            output = event_data['res']['stdout']

            output = json.loads(output)
            output = output['response']['result']['ifnet']['entry']

            for item in output:
                inf = item.get('name')
                ip = item.get('ip')
                vsys = item.get('vsys')
                zone = item.get('zone')
                row = [device, inf, ip, vsys, zone]
                df_data.append(row)

    cols = ['device',
            'interface',
            'ip',
            'vsys',
            'zone']

    df_ip = pd.DataFrame(data=df_data, columns=cols)
    return df_ip


def panos_get_security_rules(username,
                             password,
                             host_group,
                             play_path,
                             private_data_dir,
                             device_group='shared'):
    '''
    Gets a list of all security rules from a Palo Alto firewall.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        device_group (str):     The device group to query. Defaults to 'shared'

    Returns:
        df_rules (DataFrame):   A dataframe containing the rules
    '''
    extravars = {'user': username,
                 'password': password,
                 'device_group': device_group,
                 'host_group': host_group}

    playbook = f'{play_path}/palo_alto_get_security_rules.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Create the 'df_data' dictionary. It will be used to create the dataframe
    df_data = dict()
    df_data['device'] = list()

    # Create a list to store the unformatted details for each rule
    rules = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']
            output = event_data['res']['gathered']

            for item in output:
                item['device'] = device
                rules.append(item)
                for key in item:
                    if not df_data.get(key):
                        df_data[key] = list()

    # Iterate over the rule details, using the keys in dict_keys to create the
    # 'df_data' dictionary, which will be used to create the dataframe
    for item in rules:
        for key in df_data:
            # If a key in a rule has a value that is a list, then convert it to
            # a string by joining it with '|' as a delimiter. We do not want to
            # use commas a delimiter, since that can cause issues when
            # exporting the data to CSV files.
            if isinstance(item.get(key), list):
                # Some keys have a value that is a list, with commas inside the
                # list items. For example, source_user might look like this:
                # ['cn=name,ou=firewall,ou=groups,dc=dcname,dc=local']. That
                # creates an issue when exporting to a CSV file. Therefore,
                # the commas inside list items will be replaced with a space
                # before joining the list.
                _list = item.get(key)
                _list = [_.replace(',', ' ') for _ in _list]

                # Join the list using '|' as a delimiter
                df_data[key].append('|'.join(_list))
            # If the key's value is not a list, then convert it to a string
            # and append it to the key in 'df_data'
            else:
                df_data[key].append(str(item.get(key)))

    # Create the dataframe and return it
    df_rules = pd.DataFrame.from_dict(df_data)

    # Rename the 'destintaion_zone' column to 'destination_zone'
    df_rules.rename({'destintaion_zone': 'destination_zone'},
                    axis=1,
                    inplace=True)

    return df_rules
