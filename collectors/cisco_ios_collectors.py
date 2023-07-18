#!/usr/bin/env python3

import ansible_runner
import pandas as pd

from helpers import helpers as hp


def gather_facts(username: str,
                 password: str,
                 host_group: str,
                 play_path: str,
                 private_data_dir: str,
                 gather_info: dict) -> dict:
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
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'gather_info': gather_info}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_ios_gather_facts.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse the output, store it in 'facts', and return it
    facts = dict()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']
            output = event_data['res']['ansible_facts']

            facts[device] = output

    return facts


def get_config(username: str,
               password: str,
               host_group: str,
               play_path: str,
               private_data_dir: str) -> pd.DataFrame:
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
    gather_info = {'subset': ['config']}
    facts = gather_facts(username,
                         password,
                         host_group,
                         play_path,
                         private_data_dir,
                         gather_info)

    configs = dict()
    for key, value in facts.items():
        configs[key] = value['ansible_net_config']

    df = pd.DataFrame(list(configs.items()), columns=['device', 'config'])

    return df


def get_vrfs(username: str,
             password: str,
             host_group: str,
             play_path: str,
             private_data_dir: str) -> pd.DataFrame:
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
    cmd = 'show vrf detail | include VRF Id'
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

    # Parse the output, create the DataFrame and return it.
    data = []

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0]
            for line in output.strip().split("\n"):
                # Split each line into its name, vrf_id, default_rd, and
                # default_vpn_id components
                name_start = line.find("VRF ") + len("VRF ")
                name_end = line.find(" (VRF Id =")
                name = line[name_start:name_end].strip()

                vrf_id_start = line.find("VRF Id = ") + len("VRF Id = ")
                vrf_id_end = line.find(");")
                vrf_id = line[vrf_id_start:vrf_id_end].strip()

                default_rd = "not set" if "<not set>" in line else None
                default_vpn_id = "not set" if "<not set>" in line else None

                data.append([device, name, vrf_id, default_rd, default_vpn_id])

    # Convert the data to a DataFrame with the appropriate columns
    df = pd.DataFrame(
        data, columns=["device",
                       "name",
                       "vrf_id",
                       "default_rd",
                       "default_vpn_id"])

    return df


def ios_find_uplink_by_ip(username: str,
                          password: str,
                          host_group: str,
                          play_path: str,
                          private_data_dir: str,
                          subnets: list = []) -> pd.DataFrame:
    '''
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


def ios_get_arp_table(username: str,
                      password: str,
                      host_group: str,
                      nm_path: str,
                      play_path: str,
                      private_data_dir: str) -> pd.DataFrame:
    '''
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


def ios_get_cam_table(username: str,
                      password: str,
                      host_group: str,
                      nm_path: str,
                      play_path: str,
                      private_data_dir: str,
                      interface: str = None) -> pd.DataFrame:
    '''
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


def ios_get_cdp_neighbors(username: str,
                          password: str,
                          host_group: str,
                          play_path: str,
                          private_data_dir: str,
                          interface: str = '') -> pd.DataFrame:
    '''
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


def ios_get_interface_descriptions(username: str,
                                   password: str,
                                   host_group: str,
                                   play_path: str,
                                   private_data_dir: str,
                                   interface: str = None) -> pd.DataFrame:
    '''
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


def ios_get_interface_ips(username: str,
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
        A DataFrame containing the interfaces and IP addresses.
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
    df = pd.DataFrame(data=df_data, columns=cols)

    # Add the subnets, network IPs, and broadcast IPs.
    addresses = df['ip'].to_list()
    result = hp.generate_subnet_details(addresses)
    df['subnet'] = result['subnet']
    df['network_ip'] = result['network_ip']
    df['broadcast_ip'] = result['broadcast_ip']

    return df


def ios_get_vlan_db(username: str,
                    password: str,
                    host_group: str,
                    play_path: str,
                    private_data_dir: str) -> pd.DataFrame:
    '''
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
    '''
    # Get the interface descriptions and add them to df_cam
    cmd = 'show vlan brief | exclude ----'
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
    # Create a dictionary to store the rows for the dataframe
    df_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

            # Create the column headers
            cols = ['device'] + output[0].split()[:3]
            cols = [_.lower() for _ in cols]

            # Removed wrapped interfaces
            output = [_ for _ in output[1:] if _[0] != ' ']

            # Add the VLANs to 'df_data'
            for line in output:
                row = [device] + line.split()[:3]
                df_data.append(row)

    # Create the dataframe and return it
    df = pd.DataFrame(data=df_data, columns=cols)
    return df
