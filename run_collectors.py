#!/usr/bin/env python3

'''
Define collectors and map them to the correct function in colletors.py.
'''

import collectors as cl


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
            result = cl.ios_get_cam_table(username,
                                          password,
                                          hostgroup,
                                          play_path,
                                          private_data_dir,
                                          nm_path)

        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_cam_table(username,
                                           password,
                                           hostgroup,
                                           play_path,
                                           private_data_dir,
                                           nm_path)

    if collector == 'arp_table':
        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_arp_table(username,
                                           password,
                                           hostgroup,
                                           nm_path,
                                           play_path,
                                           private_data_dir)

        if ansible_os == 'bigip':
            result = cl.f5_get_arp_table(username,
                                         password,
                                         hostgroup,
                                         nm_path,
                                         play_path,
                                         private_data_dir,
                                         validate_certs=False)

        if ansible_os == 'paloaltonetworks.panos':
            result = cl.panos_get_arp_table(username,
                                            password,
                                            hostgroup,
                                            play_path,
                                            private_data_dir)

    if collector == 'f5_pool_availability':
        if ansible_os == 'bigip':
            result = cl.f5_get_pool_availability(username,
                                                 password,
                                                 hostgroup,
                                                 play_path,
                                                 private_data_dir,
                                                 validate_certs=False)

    if collector == 'f5_pool_member_availability':
        if ansible_os == 'bigip':
            result = cl.f5_get_pool_member_availability(username,
                                                        password,
                                                        hostgroup,
                                                        play_path,
                                                        private_data_dir,
                                                        validate_certs=False)

    if collector == 'f5_vip_availability':
        if ansible_os == 'bigip':
            result = cl.f5_get_vip_availability(username,
                                                password,
                                                hostgroup,
                                                play_path,
                                                private_data_dir,
                                                validate_certs=False)

    if collector == 'interface_description':
        if ansible_os == 'cisco.ios.ios':
            result = cl.ios_get_interface_descriptions(username,
                                                       password,
                                                       hostgroup,
                                                       play_path,
                                                       private_data_dir)

        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_interface_descriptions(username,
                                                        password,
                                                        hostgroup,
                                                        play_path,
                                                        private_data_dir)

        if ansible_os == 'bigip':
            result = cl.f5_get_interface_descriptions(username,
                                                      password,
                                                      hostgroup,
                                                      nm_path,
                                                      play_path,
                                                      private_data_dir,
                                                      reverse_dns=False,
                                                      validate_certs=False)

    if collector == 'interface_status':
        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_interface_status(username,
                                                  password,
                                                  hostgroup,
                                                  play_path,
                                                  private_data_dir)

        if ansible_os == 'bigip':
            result = cl.f5_get_interface_status(username,
                                                password,
                                                hostgroup,
                                                play_path,
                                                private_data_dir,
                                                validate_certs=False)

    if collector == 'find_uplink_by_ip':
        if ansible_os == 'cisco.ios.ios':
            result = cl.ios_find_uplink_by_ip(username,
                                              password,
                                              hostgroup,
                                              play_path,
                                              private_data_dir)

    if collector == 'port_channel_data':
        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_port_channel_data(username,
                                                   password,
                                                   hostgroup,
                                                   play_path,
                                                   private_data_dir)

    if collector == 'vpc_state':
        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_vpc_state(username,
                                           password,
                                           hostgroup,
                                           play_path,
                                           private_data_dir)

    if collector == 'vlan_database':
        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_vlan_db(username,
                                         password,
                                         hostgroup,
                                         play_path,
                                         private_data_dir)

        if ansible_os == 'bigip':
            result = cl.f5_get_vlan_db(username,
                                       password,
                                       hostgroup,
                                       play_path,
                                       private_data_dir,
                                       validate_certs=False)

    return result


def define_collectors():
    '''
    Creates a list of collectors.

    Args:
        None

    Returns:
        collectors (list):  A list of collectors.
    '''
    collectors = [
                  'arp_table',
                  'cam_table',
                  'f5_pool_availability',
                  'f5_pool_member_availability',
                  'f5_vip_availability',
                  'interface_description',
                  'interface_status',
                  'port_channel_data',
                  'vlan_database',
                  'vpc_state',
                  ]
    return collectors
