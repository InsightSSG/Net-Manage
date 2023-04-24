#!/usr/bin/env python3

import os
import sys

# Change to the Net-Manage repository so imports will work
nm_path = os.environ.get('NM_PATH')
os.chdir(f'{nm_path}/test')
sys.path.append('..')
from collectors import collectors  # noqa


def test_get_cam_table(username,
                       password,
                       host_group,
                       nm_path,
                       play_path,
                       private_data_dir,
                       interface=None):
    """
    Test the 'ios_get_cam_table' collector.
    """
    df_cam = collectors.ios_get_cam_table(username,
                                          password,
                                          host_group,
                                          nm_path,
                                          play_path,
                                          private_data_dir,
                                          interface=None)
    expected = ['device', 'interface', 'mac', 'vlan', 'vendor']

    assert df_cam.columns.to_list() == expected


# def test_get_all_interfaces(username,
#                             password,
#                             host_group,
#                             nm_path,
#                             private_data_dir):
#     # Test getting all logical interfaces.
#     df_all = palo_alto_collectors.get_all_interfaces(username,
#                                                      password,
#                                                      host_group,
#                                                      nm_path,
#                                                      private_data_dir)
#     expected = ['device',
#                 'name',
#                 'zone',
#                 'fwd',
#                 'vsys',
#                 'dyn-addr',
#                 'addr6',
#                 'tag',
#                 'ip',
#                 'id',
#                 'addr']
#     assert df_all.columns.to_list() == expected


# def test_get_arp_table(username,
#                        password,
#                        host_group,
#                        nm_path,
#                        private_data_dir,
#                        interface=str()):

#     # Test getting the ARP table for all interfaces.
#     df_arp = palo_alto_collectors.get_arp_table(username,
#                                                 password,
#                                                 host_group,
#                                                 nm_path,
#                                                 private_data_dir)
#     expected = ['device',
#                 'status',
#                 'ip',
#                 'mac',
#                 'ttl',
#                 'interface',
#                 'port',
#                 'vendor']
#     assert df_arp.columns.to_list() == expected

#     # Test getting the ARP table for a single interface.
#     df_arp = palo_alto_collectors.get_arp_table(username,
#                                                 password,
#                                                 host_group,
#                                                 nm_path,
#                                                 private_data_dir,
#                                                 interface='management')
#     expected = ['device', 'interface', 'ip', 'mac', 'status', 'vendor']
#     assert df_arp.columns.to_list() == expected


# def test_get_logical_interfaces(username,
#                                 password,
#                                 host_group,
#                                 nm_path,
#                                 private_data_dir):
#     # Test getting all logical interfaces.
#     df_logical = palo_alto_collectors.get_logical_interfaces(username,
#                                                              password,
#                                                              host_group,
#                                                              nm_path,
#                                                              private_data_dir)
#     expected = ['device',
#                 'name',
#                 'zone',
#                 'fwd',
#                 'vsys',
#                 'dyn-addr',
#                 'addr6',
#                 'tag',
#                 'ip',
#                 'id',
#                 'addr']
#     assert df_logical.columns.to_list() == expected


# def test_get_physical_interfaces(username,
#                                  password,
#                                  host_group,
#                                  nm_path,
#                                  private_data_dir):
#     # Test getting all physical interfaces.
#     df_phys = palo_alto_collectors.get_physical_interfaces(username,
#                                                            password,
#                                                            host_group,
#                                                            nm_path,
#                                                            private_data_dir)
#     expected = ['device',
#                 'name',
#                 'duplex',
#                 'type',
#                 'state',
#                 'st',
#                 'mac',
#                 'mode',
#                 'speed',
#                 'id']
#     assert df_phys.columns.to_list() == expected


def main():
    username = os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    host_group = os.environ.get('IOS_HOST_GROUP')
    nm_path = os.environ.get('NM_PATH')
    play_path = os.environ.get('PLAY_PATH')
    private_data_dir = os.environ.get('PRIVATE_DATA_DIR')

    # Execute tests
    test_get_cam_table(username,
                       password,
                       host_group,
                       nm_path,
                       play_path,
                       private_data_dir,
                       interface=None)

    # test_get_all_interfaces(username,
    #                         password,
    #                         host_group,
    #                         nm_path,
    #                         private_data_dir)

    # test_get_arp_table(username,
    #                    password,
    #                    host_group,
    #                    nm_path,
    #                    private_data_dir)

    # test_get_logical_interfaces(username,
    #                             password,
    #                             host_group,
    #                             nm_path,
    #                             private_data_dir)

    # test_get_physical_interfaces(username,
    #                              password,
    #                              host_group,
    #                              nm_path,
    #                              private_data_dir)


if __name__ == '__main__':
    main()
