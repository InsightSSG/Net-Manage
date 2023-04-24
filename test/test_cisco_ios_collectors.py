#!/usr/bin/env python3

import os
import sys

# Change to the Net-Manage repository so imports will work
nm_path = os.environ.get('NM_PATH')
os.chdir(f'{nm_path}/test')
sys.path.append('..')
from collectors import collectors  # noqa


def test_get_arp_table(username,
                       password,
                       host_group,
                       nm_path,
                       play_path,
                       private_data_dir):
    """Test the 'ios_get_arp_table' collector.
    """
    df_arp = collectors.ios_get_arp_table(username,
                                          password,
                                          host_group,
                                          nm_path,
                                          play_path,
                                          private_data_dir)

    expected = ['device',
                'Protocol',
                'Address',
                'Age (min)',
                'Hardware Addr',
                'Type',
                'Interface',
                'vendor']
    print(expected)
    print(df_arp.columns.to_list())
    print(df_arp)
    assert df_arp.columns.to_list() == expected

    assert len(df_arp) >= 1


def test_get_cam_table(username,
                       password,
                       host_group,
                       nm_path,
                       play_path,
                       private_data_dir,
                       interface=None):
    """Test the 'ios_get_cam_table' collector.
    """
    df_cam = collectors.ios_get_cam_table(username,
                                          password,
                                          host_group,
                                          nm_path,
                                          play_path,
                                          private_data_dir,
                                          interface=None)

    expected = ['device', 'Vlan', 'Mac Address', 'Type', 'Ports', 'vendor']
    assert df_cam.columns.to_list() == expected

    assert len(df_cam) >= 1


def test_get_interface_descriptions(username,
                                    password,
                                    host_group,
                                    play_path,
                                    private_data_dir,
                                    interface=None):
    """Test the 'ios_get_interface_descriptions' collector.
    """
    df_desc = collectors.ios_get_interface_descriptions(username,
                                                        password,
                                                        host_group,
                                                        play_path,
                                                        private_data_dir,
                                                        interface=None)

    expected = ['device', 'interface', 'description']
    assert df_desc.columns.to_list() == expected

    assert len(df_desc) >= 1


def main():
    username = os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    host_group_all = os.environ.get('IOS_HOST_GROUP_ALL')
    host_group_l2 = os.environ.get('IOS_L2_HOST_GROUP')
    # host_group_l3 = os.environ.get('IOS_L3_HOST_GROUP')
    # nm_path = os.environ.get('NM_PATH')
    play_path = os.environ.get('PLAY_PATH')
    private_data_dir = os.environ.get('PRIVATE_DATA_DIR')

    # Execute tests
    test_get_arp_table(username,
                       password,
                       host_group_all,
                       nm_path,
                       play_path,
                       private_data_dir)

    test_get_cam_table(username,
                       password,
                       host_group_l2,
                       nm_path,
                       play_path,
                       private_data_dir,
                       interface=None)

    test_get_interface_descriptions(username,
                                    password,
                                    host_group_all,
                                    play_path,
                                    private_data_dir,
                                    interface=None)


if __name__ == '__main__':
    main()
