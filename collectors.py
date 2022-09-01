#!/usr/bin/env python3

'''
A library of functions for collecting data from network devices.
'''

import ansible_runner
import json
import pandas as pd
import re
import socket


def collect(ansible_os,
            collector,
            username,
            password,
            hostgroup,
            play_path,
            private_data_dir,
            nm_path,
            ansible_timeout='300',
            validate_certs=True):
    '''
    This function calls the test that the user requested.

    Args:
        os (str):               The ansible_network_os variable
        collector (str):        The name of the test that the user requested
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        nm_path (str):          The path to the Net-Manage repository
        interface (str):        The interface (defaults to all interfaces)
        validate_certs (bool):  Whether to validate SSL certs (used for F5s)
    '''
    if collector == 'cam_table':
        if ansible_os == 'cisco.ios.ios':
            result = ios_get_cam_table(username,
                                       password,
                                       hostgroup,
                                       play_path,
                                       private_data_dir,
                                       nm_path)

        if ansible_os == 'cisco.nxos.nxos':
            result = nxos_get_cam_table(username,
                                        password,
                                        hostgroup,
                                        play_path,
                                        private_data_dir,
                                        nm_path)

    if collector == 'arp_table':
        if ansible_os == 'cisco.nxos.nxos':
            result = nxos_get_arp_table(username,
                                        password,
                                        hostgroup,
                                        nm_path,
                                        play_path,
                                        private_data_dir)

        if ansible_os == 'bigip':
            result = f5_get_arp_table(username,
                                      password,
                                      hostgroup,
                                      nm_path,
                                      play_path,
                                      private_data_dir,
                                      validate_certs=False)

        if ansible_os == 'paloaltonetworks.panos':
            result = panos_get_arp_table(username,
                                         password,
                                         hostgroup,
                                         play_path,
                                         private_data_dir)

    if collector == 'f5_pool_availability':
        if ansible_os == 'bigip':
            result = f5_get_pool_availability(username,
                                              password,
                                              hostgroup,
                                              play_path,
                                              private_data_dir,
                                              validate_certs=False)

    if collector == 'f5_pool_member_availability':
        if ansible_os == 'bigip':
            result = f5_get_pool_member_availability(username,
                                                     password,
                                                     hostgroup,
                                                     play_path,
                                                     private_data_dir,
                                                     validate_certs=False)

    if collector == 'f5_vip_availability':
        if ansible_os == 'bigip':
            result = f5_get_vip_availability(username,
                                             password,
                                             hostgroup,
                                             play_path,
                                             private_data_dir,
                                             validate_certs=False)

    if collector == 'interface_description':
        if ansible_os == 'cisco.ios.ios':
            result = ios_get_interface_descriptions(username,
                                                    password,
                                                    hostgroup,
                                                    play_path,
                                                    private_data_dir)

        if ansible_os == 'cisco.nxos.nxos':
            result = nxos_get_interface_descriptions(username,
                                                     password,
                                                     hostgroup,
                                                     play_path,
                                                     private_data_dir)

        if ansible_os == 'bigip':
            result = f5_get_interface_descriptions(username,
                                                   password,
                                                   hostgroup,
                                                   nm_path,
                                                   play_path,
                                                   private_data_dir,
                                                   reverse_dns=False,
                                                   validate_certs=False)

    if collector == 'interface_status':
        if ansible_os == 'cisco.nxos.nxos':
            result = nxos_get_interface_status(username,
                                               password,
                                               hostgroup,
                                               play_path,
                                               private_data_dir)

        if ansible_os == 'bigip':
            result = f5_get_interface_status(username,
                                             password,
                                             hostgroup,
                                             play_path,
                                             private_data_dir,
                                             validate_certs=False)

    if collector == 'find_uplink_by_ip':
        if ansible_os == 'cisco.ios.ios':
            result = ios_find_uplink_by_ip(username,
                                           password,
                                           hostgroup,
                                           play_path,
                                           private_data_dir)

    if collector == 'port_channel_data':
        if ansible_os == 'cisco.nxos.nxos':
            result = nxos_get_port_channel_data(username,
                                                password,
                                                hostgroup,
                                                play_path,
                                                private_data_dir)

    if collector == 'vpc_state':
        if ansible_os == 'cisco.nxos.nxos':
            result = nxos_get_vpc_state(username,
                                        password,
                                        hostgroup,
                                        play_path,
                                        private_data_dir)

    if collector == 'vlan_database':
        if ansible_os == 'cisco.nxos.nxos':
            result = nxos_get_vlan_db(username,
                                      password,
                                      hostgroup,
                                      play_path,
                                      private_data_dir)

        if ansible_os == 'bigip':
            result = f5_get_vlan_db(username,
                                    password,
                                    hostgroup,
                                    play_path,
                                    private_data_dir,
                                    validate_certs=False)

    return result


def update_ouis(nm_path):
    '''
    Creates a dataframe of vendor OUIs. List is taken from
    https://standards-oui.ieee.org/. It is downloaded ahead of time to save
    time.

    There is a Python library for it, but it is prohibitively slow.

    To update the OUIs, save the data in https://standards-oui.ieee.org/ to
    Net-Manage/ouis.txt.

    Note: It might seem inefficient to parse the OUIs and create the
    dataframe as needed. However, it only takes 250ms~ to do, and the DataFrame
    size is only 500KB~. Therefore, I find the overhead acceptable.

    Args:
        nm_path (str): Path to the Net-Manage repository.

    Returns:
        df_ouis (DataFrame): A DataFrame containing the vendor OUIs
    '''
    with open(f'{nm_path}/ouis.txt', 'r') as f:
        data = f.read()
    pattern = '.*base 16.*'
    data = re.findall(pattern, data)
    data = [[_.split()[0], _.split('\t')[-1]] for _ in data]
    df_ouis = pd.DataFrame(data=data, columns=['base', 'vendor'])
    return df_ouis


def find_mac_vendor(addresses, nm_path):
    '''
    Finds the vendor OUI for a list of MAC addresses.

    Note: This function could be improved by multi-threading. However, in
    testing I found the performance in its current state to be acceptable. It
    took about 30 seconds to get the vendors for 16,697 MAC addresses. That
    DOES include the time it took for Ansible to connect to the devices and get
    the CAM tables.

    Args:
        addresses (list):   A list of MAC adddresses.
        nm_path (str):      The path to the Net-Manage repository

    Returns:
        vendors (list):     A list of vendors, ordered the same as 'addresses'
    '''
    # Convert MAC addresses to base 16
    addresses = [m.replace(':', str()) for m in addresses]
    addresses = [m.replace('-', str()) for m in addresses]
    addresses = [m.replace('.', str()) for m in addresses]
    addresses = [m[:6].upper() for m in addresses]
    # Create a list to store vendors
    vendors = list()

    # Create a list to store unknown vendors. This is used to keep from
    # repeatedly searching for vendor OUIs that are unknown
    unknown = list()

    # Create a dict to store known vendors. This is used to keep from
    # repeatedly searching df_ouis for vendors that are already discovered
    known = dict()

    # Get the OUIs
    # TODO: Optimize so df_ouis isn't recreated every time function is called
    # TODO: This could be added to the database once at first run-time. A
    #       query could be run after that just to make sure the table exists
    #       and is populated.
    #
    df_ouis = update_ouis(nm_path)

    # Search df_ouis for the vendor, add it to 'vendors', and return it
    for mac in addresses:
        vendor = known.get(mac)
        if not vendor:
            if mac in unknown:
                vendor = 'unknown'
            else:
                vendor_row = df_ouis.loc[df_ouis['base'] == mac]
                if len(vendor_row) > 0:
                    vendor = vendor_row['vendor'].values[0]
                else:
                    vendor = 'unknown'
                    unknown.append(mac)
        vendors.append(vendor)
    return vendors


def f5_get_arp_table(username,
                     password,
                     host_group,
                     nm_path,
                     play_path,
                     private_data_dir,
                     reverse_dns=False,
                     validate_certs=True):
    '''
    Gets the ARP table for F5 LTM devices. Also returns the OUI (vendor) for
    the MAC address. Will also return a reverse DNS query, but only if the user
    requests it (it can take several minutes for large datasets).

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
        validate_certs (bool):  Whether to validate SSL certificates

    Returns:
        df_arp (DataFrame):     The ARP table
    '''
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the command
    playbook = f'{play_path}/f5_get_arp_table.yml'
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

            output = event_data['res']['stdout_lines'][0]

            # Parse the output and add it to 'df_data'
            for line in output:
                line = line.split()
                address = line[1]
                age = line[-2]
                mac = line[2]
                vlan = line[3]  # Column name is 'interface' to match Ciscos
                macs.append(mac)
                row = [device, address, age, mac, vlan]

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
    vendors = find_mac_vendor(macs, nm_path)
    df_arp['vendor'] = vendors

    return df_arp


def f5_get_interface_descriptions(username,
                                  password,
                                  host_group,
                                  nm_path,
                                  play_path,
                                  private_data_dir,
                                  reverse_dns=False,
                                  validate_certs=True):
    '''
    Gets IOS interface descriptions.

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
        validate_certs (bool):  Whether to validate SSL certificates

    Returns:
        df_desc (DataFrame):    The interface descriptions
    '''
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the command and parse the results
    playbook = f'{play_path}/f5_get_interface_description.yml'
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

            output = event_data['res']['stdout_lines'][0]
            pos = 1
            for line in output:
                if 'net interface' in line or 'net trunk' in line:
                    inf = line.split()[-2]
                    desc = output[pos].split()[1:]
                    desc = ' '.join(desc)  # To account for spaces in desc
                    df_data.append([device, inf, desc])
                pos += 1

    # Create the dataframe and return it
    cols = ['device', 'interface', 'description']
    df_desc = pd.DataFrame(data=df_data, columns=cols)
    return df_desc


def f5_get_interface_status(username,
                            password,
                            host_group,
                            play_path,
                            private_data_dir,
                            validate_certs=True):
    '''
    Gets the interface and trunk statuses for F5 devices.

    Args:
        username (str):             The username to login to devices
        password (str):             The password to login to devices
        host_group (str):           The inventory host group
        play_path (str):            The path to the playbooks directory
        private_data_dir (str):     Path to the Ansible private data directory
        nm_path (str):              The path to the Net-Manage repository
        validate_certs (bool):      Whether to validate SSL certificates

    Returns:
        df_inf_status (DataFrame):  The interface statuses
    '''
    # Get the interface statuses
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the pre-checks
    playbook = f'{play_path}/f5_get_interface_status.yml'
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

            # The playbook runs two commands--show net interface and show net
            # trunk. The output of both commands is in the same event.
            output = event_data['res']['stdout_lines']
            net_inf = output[0]
            net_trunk = output[1]

            # Parse the interface statuses and add it to 'df_data'.
            for line in net_inf:
                line = line.split()
                inf = line[0]
                status = line[1]
                vlan = str()
                duplex = str()
                speed = str()
                media = line[8]
                row = [device,
                       inf,
                       status,
                       vlan,
                       duplex,
                       speed,
                       media]
                df_data.append(row)

            for line in net_trunk:
                line = line.split()
                inf = line[0]
                status = line[1]
                vlan = str()
                duplex = str()
                speed = line[2]
                media = str()
                row = [device,
                       inf,
                       status,
                       vlan,
                       duplex,
                       speed,
                       media]
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


def f5_get_pool_availability(username,
                             password,
                             host_group,
                             play_path,
                             private_data_dir,
                             validate_certs=True):
    '''
    Gets pool availability from F5 LTMs.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): Path to the Ansible private data directory
        nm_path (str):          The path to the Net-Manage repository
        validate_certs (bool):  Whether to validate SSL certificates

    Returns:
        df_pools (DataFrame):   The pool availability and associated data
    '''
    # Get the interface statuses
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the pre-checks
    playbook = f'{play_path}/f5_get_pool_availability.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse the pool data and add it to two dictionaries--'pools' and
    # 'pool_members'. The data from those dictionaries will be used to
    # create the two dataframes
    pools = dict()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']
            pools[device] = dict()

            # The playbook runs two commands--show net interface and show net
            # trunk. The output of both commands is in the same event.
            output = event_data['res']['stdout_lines'][0]

            pos = 0
            for line in output:
                if 'Ltm::Pool:' in line:
                    if '/' in line:
                        pool = line.split('/')[-1]
                        partition = line.split('/')[1].split('/')[-1]
                    else:
                        pool = line.split()[-1]
                        partition = 'Common'
                    pools[device][pool] = dict()
                    pools[device][pool]['device'] = device
                    pools[device][pool]['partition'] = partition
                    counter = pos+1
                    while 'Ltm::Pool:' not in output[counter]:
                        _ = output[counter]
                        if _.split()[0] != '|':
                            if 'Availability' in _:
                                pools[device][pool]['availability'] = \
                                    _.split()[-1]
                            if 'State' in _:
                                pools[device][pool]['state'] = _.split()[-1]
                            if 'Reason' in _:
                                pools[device][pool]['reason'] = \
                                    _.split(':')[-1].strip()
                            if 'Minimum Active Members' in _:
                                pools[device][pool]['minimum_active'] = \
                                    _.split()[-1]
                            if 'Current Active Members' in _:
                                pools[device][pool]['current_active'] = \
                                    _.split()[-1]
                            if 'Available Members' in _:
                                pools[device][pool]['available'] = \
                                    _.split()[-1]
                            if 'Total Members' in _:
                                pools[device][pool]['total'] = _.split()[-1]
                        counter += 1
                        if counter == len(output):
                            break
                pos += 1

    df_pools_data = list()
    for key, value in pools.items():
        for k, v in value.items():
            pool = k
            device = v['device']
            available = v['available']
            availability = v['availability']
            current_active = v['current_active']
            minimum_active = v['minimum_active']
            partition = v['partition']
            reason = v['reason']
            state = v['state']
            total = v['total']
            df_pools_data.append([device,
                                  partition,
                                  pool,
                                  availability,
                                  state,
                                  total,
                                  available,
                                  current_active,
                                  minimum_active,
                                  reason])

    cols = ['device',
            'partition',
            'pool',
            'availability',
            'state',
            'total',
            'avail',
            'cur',
            'min',
            'reason']

    df_pools = pd.DataFrame(data=df_pools_data, columns=cols)

    return df_pools


def f5_get_pool_member_availability(username,
                                    password,
                                    host_group,
                                    play_path,
                                    private_data_dir,
                                    validate_certs=True):
    '''
    Gets F5 pool member availability from F5 LTMs.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): Path to the Ansible private data directory
        nm_path (str):          The path to the Net-Manage repository
        validate_certs (bool):  Whether to validate SSL certificates

    Returns:
        df_members (DataFrame): The pool availability and associated data
    '''
    # Get the interface statuses
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the pre-checks
    playbook = f'{play_path}/f5_get_pool_member_availability.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    df_data = list()
    # df_dict = dict()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']
            # df_dict[device] = dict()

            output = event_data['res']['stdout_lines'][0]
            pos = 0
            for line in output:
                if 'Ltm::Pool:' in line:
                    # TODO: Separate partition from pool name.
                    if '/' in line:
                        pool = line.split()[-1]
                    else:
                        pool = line.split()[-1]
                    # df_dict[device][pool] = dict()
                    counter = pos+1
                    while 'Ltm::Pool:' not in output[counter]:
                        _ = output[counter]
                        if _.split()[0] == '|':
                            if 'Ltm::Pool Member:' in _:
                                member = _.split()[-1]
                            if 'Availability' in _:
                                availability = _.split()[-1]
                                df_data.append([device,
                                                pool,
                                                member,
                                                availability])
                        counter += 1
                        if counter == len(output):
                            break

                pos += 1

    cols = ['device',
            'pool_name',
            'pool_member',
            'pool_member_state']

    df_members = pd.DataFrame(data=df_data, columns=cols)

    return df_members


def f5_get_vip_availability(username,
                            password,
                            host_group,
                            play_path,
                            private_data_dir,
                            validate_certs=True):
    '''
    Gets VIP availability from F5 LTMs.
    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): Path to the Ansible private data directory
        nm_path (str):          The path to the Net-Manage repository
        validate_certs (bool):  Whether to validate SSL certificates
    Returns:
        df_vips (DataFrame):    The pool availability and associated data
    '''
    # Get the interface statuses
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the pre-checks
    playbook = f'{play_path}/f5_get_vip_availability_and_destination.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']
            # pools[device] = dict()

            output = event_data['res']['stdout_lines'][0]
            pos = 0
            for line in output:
                if 'Ltm::Virtual Server:' in line:
                    if '/' in line:
                        vip = line.split('/')[-1]
                        partition = line.split('/')[1].split('/')[-1]
                    else:
                        vip = line.split()[-1]
                        partition = 'Common'
                    counter = pos+1
                    while 'Ltm::Virtual Server:' not in output[counter]:
                        _ = output[counter]
                        if 'Availability' in _:
                            availability = _.split()[-1]
                        if 'State' in _:
                            state = _.split()[-1]
                        if 'Reason' in _:
                            reason = _.split(':')[-1].strip()
                        if 'Destination' in _:
                            destination = _.split()[-1].split(':')[0]
                            port = _.split()[-1].split(':')[-1]
                        counter += 1
                        if counter == len(output):
                            break
                    df_data.append([device,
                                    partition,
                                    vip,
                                    destination,
                                    port,
                                    availability,
                                    state,
                                    reason])
                pos += 1

    cols = ['device',
            'partition',
            'vip',
            'destination',
            'port',
            'availability',
            'state',
            'reason']

    df_vips = pd.DataFrame(data=df_data, columns=cols)

    return df_vips


def f5_get_vlan_db(username,
                   password,
                   host_group,
                   play_path,
                   private_data_dir,
                   validate_certs=True):
    '''
    Gets the VLAN database on F5 LTMs.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): Path to the Ansible private data directory
        nm_path (str):          The path to the Net-Manage repository
        validate_certs (bool):  Whether to validate SSL certificates

    Returns:
        df_vips (DataFrame):    The pool availability and associated data
    '''
    # Get the interface statuses
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    playbook = f'{play_path}/f5_get_vlan_database.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout_lines'][0]

            pos = 0
            for line in output:
                if 'Net::Vlan:' in line:
                    if 'Interface Name' in output[pos+1]:
                        name = output[pos+1].split()[-1]
                    else:
                        name = str()
                    if output[pos+2].split()[0] == 'Tag':
                        tag = output[pos+2].split()[-1]
                    else:
                        tag = str()
                    # TODO: Add support for status and interfaces
                    df_data.append([device,
                                    tag,
                                    name,
                                    str(),
                                    str()])
                pos += 1

    cols = ['device',
            'id',
            'name',
            'status',
            'ports']
    df_vlans = pd.DataFrame(data=df_data, columns=cols)

    return df_vlans


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
    df_ip = cisco_ios_get_interface_ips(username,
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
        cmd = 'show mac address-table'
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

    # Parse the output and add it to 'data'
    df_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')
            output = list(filter(None, output))
            pattern = '[a-zA-Z0-9]{4}\\.[a-zA-Z0-9]{4}\\.[a-zA-Z0-9]{4}'
            for line in output:
                for item in line.split():
                    valid = re.match(pattern, item)
                    if valid and line.split()[-1] != 'CPU':
                        mac = line.split()[1]
                        interface = line.split()[-1]
                        vlan = line.split()[0]
                        try:
                            vendor = find_mac_vendor(mac, nm_path)
                        except Exception:
                            vendor = 'unknown'
                        df_data.append([device, interface, mac, vlan, vendor])

    # Define the dataframe columns
    cols = ['device',
            'interface',
            'mac',
            'vlan',
            'vendor']

    df_cam = pd.DataFrame(data=df_data, columns=cols)

    # Get the ARP table, map the IPs to the CAM table, and add them to 'df_cam'
    # TODO: Iterate through VRFs on devices that do not support 'vrf all'
    cmd = 'show ip arp'
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

    # Create a dict to store the ARP table
    ip_dict = dict()

    # Create a list to store the IP address for each MAC address. If there is
    # not an entry in the ARP table then an empty string will be added
    addresses = list()

    # Parse the output
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')
            output = list(filter(None, output))
            for line in output[1:]:
                mac = line.split()[3]
                ip = line.split()[1]
                ip_dict[mac] = ip

            for idx, row in df_cam.iterrows():
                mac = row['mac']
                if ip_dict.get(mac):
                    addresses.append(ip_dict.get(mac))
                else:
                    addresses.append(str())

    # Add the addresses list to 'df_cam' as a column
    df_cam['ip'] = addresses

    # Set the desired order of columns
    cols = ['device',
            'interface',
            # 'description',
            'mac',
            # 'ip',
            'vlan',
            'vendor']
    df_cam = df_cam[cols]

    # Sort by interface
    df_cam = df_cam.sort_values('interface')

    # Reset (re-order) the index
    df_cam.reset_index(drop=True, inplace=True)

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


def cisco_ios_get_interface_ips(username,
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
    cmd = 'show ip interface | include line protocol|Internet address'
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
    ip_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')
            output.reverse()  # Reverse the output to make it easier to iterate
            for line in output:
                if 'Internet address' in line:
                    ip = line.split()[-1]
                    pos = output.index(line)+1
                    inf = output[pos].split()[0]
                    status = output[pos].split()[-1]
                    row = [device, inf, ip, status]
                    ip_data.append(row)
    # Create a dataframe from ip_data and return it
    cols = ['Device', 'Interface', 'IP', 'Status']
    df_ip = pd.DataFrame(data=ip_data, columns=cols)
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
    vendors = find_mac_vendor(macs, nm_path)
    df_arp['vendor'] = vendors

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
    vendors = find_mac_vendor(macs, nm_path)
    df_arp['vendor'] = vendors

    return df_arp


def nxos_get_cam_table(username,
                       password,
                       host_group,
                       play_path,
                       private_data_dir,
                       nm_path,
                       interface=None):
    '''
    Gets the CAM table for NXOS devices and adds the vendor OUI.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        interface (str):        The interface (defaults to all interfaces)
        nm_path (str):          The path to the Net-Manage repository

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
    vendors = find_mac_vendor(addresses, nm_path)
    df_cam['vendor'] = vendors

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
    cmd = 'show interface status'
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

            # Get the positions of the header columns (except Port and Name)
            header = output[1]
            pos_status = header.index('Status')
            pos_vlan = header.index('Vlan')
            pos_duplex = header.index('Duplex')
            pos_speed = header.index('Speed')
            pos_type = header.index('Type')

            # Parse the output and add it to 'df_data'
            for line in output[3:]:
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
    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

            row = [device]
            for line in output[:-2]:
                line = line.split(':')[-1].strip()
                row.append(line)
            df_data.append(row)

            # Create the DataFrame columns
            cols = ['device',
                    'vPC domain id',
                    'Peer status',
                    'vPC keep-alive status',
                    'Configuration consistency status',
                    'Per-vlan consistency status',
                    'Type-2 consistency status',
                    'vPC role',
                    'Number of vPCs configured',
                    'Peer Gateway',
                    'Peer gateway excluded VLANs',
                    'Dual-active excluded VLANs',
                    'Graceful Consistency Check',
                    'Operational Layer3 Peer-router',
                    'Auto-recovery status']

    # Create the dataframe and return it
    df_vpc_state = pd.DataFrame(data=df_data, columns=cols)

    return df_vpc_state


def panos_get_arp_table(username,
                        password,
                        host_group,
                        nm_path,
                        play_path,
                        private_data_dir,
                        interface=None,
                        reverse_dns=False):
    '''
    Gets the ARP table from a Palo Alto firewall.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        nm_path (str):          The path to the Net-Manage repository
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        interface (str):        The interface (defaults to all interfaces)
        reverse_dns (bool):     Whether to run a reverse DNS lookup. Defaults
                                to False because the test can take several
                                minutes on large ARP tables.

    Returns:
        df_arp (DataFrame):     The ARP table
    '''
    if interface:
        cmd = f'show arp {interface}'
    else:
        cmd = 'show arp all'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'command': cmd}

    playbook = f'{play_path}/palo_alto_get_arp_table.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']
            output = event_data['res']['stdout']

            output = json.loads(output)
            output = output['response']['result']['entries']['entry']

            arp_table = list()
            for item in output:
                address = item['ip']
                age = item['ttl']
                mac = item['mac']
                inf = item['interface']
                # Lookup the OUI vendor
                try:
                    vendor = find_mac_vendor(mac, nm_path)
                except Exception as e:
                    print(str(e))
                    vendor = 'unknown'
                row = [device, address, age, mac, inf, vendor]
                # Perform a reverse DNS lookup if requested
                if reverse_dns:
                    try:
                        rdns = socket.getnameinfo((address, 0), 0)[0]
                    except Exception:
                        rdns = 'unknown'
                    row.append(rdns)
                arp_table.append(row)

    cols = ['Device',
            'Address',
            'Age',
            'MAC Address',
            'Interface',
            'Vendor']
    if reverse_dns:
        cols.append('Reverse DNS')

    df_arp = pd.DataFrame(data=arp_table, columns=cols)
    return df_arp


def main():
    import argparse
    import helpers as hp
    import os
    from tabulate import tabulate

    # Create the parser for command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username',
                        help='''The username for connecting to the devices. If
                                missing, script will prompt for it.''',
                        action='store'
                        )
    parser.add_argument('-P', '--password',
                        help='''The password for connecting to the devices.
                                For testing only. DO NOT USE ON SHARED OR
                                INSECURE DEVICES. Always follow your
                                organization's policies.''',
                        action='store'
                        )
    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument('-H', '--hostgroup',
                               help='The hostgroup to test.',
                               required=True,
                               action='store'
                               )
    requiredNamed.add_argument('-n', '--nm_path',
                               help='The path to the Net-Manage repository',
                               required=True,
                               action='store'
                               )
    requiredNamed.add_argument('-p', '--private_data_dir',
                               help='''The path to the Ansible private data
                                       directory (I.e., the directory containing
                                       the 'inventory' and 'env' folders).''',
                               required=True,
                               action='store'
                               )
    args = parser.parse_args()
    if not args.password:
        password = hp.get_password()
    else:
        password = args.password
    if not args.username:
        username = hp.get_username()
    else:
        username = args.username

    host_group = args.hostgroup
    nm_path = os.path.expanduser(args.nm_path)
    play_path = f'{nm_path}/playbooks'
    private_data_dir = os.path.expanduser(args.private_data_dir)

    result = nxos_get_logs(username,
                               password,
                               host_group,
                               play_path,
                               private_data_dir)    

    print(tabulate(result,
                   headers='keys',
                   tablefmt='psql',
                   showindex=False))


if __name__ == '__main__':
    main()
