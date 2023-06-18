#!/usr/bin/env python3

import os
import sys

# Change to the Net-Manage repository so imports will work
nm_path = os.environ.get('NM_PATH')
os.chdir(f'{nm_path}/test')
sys.path.append('..')
from collectors import cisco_nxos_collectors as collectors  # noqa


def test_get_arp_table(username,
                       password,
                       host_group,
                       nm_path,
                       play_path,
                       private_data_dir,
                       reverse_dns=False):
    """Test the 'nxos_get_arp_table' collector.
    """
    df_arp = collectors.nxos_get_arp_table(username,
                                           password,
                                           host_group,
                                           nm_path,
                                           play_path,
                                           private_data_dir,
                                           reverse_dns=False)

    expected = ['device',
                'ip_address',
                'age',
                'mac_address',
                'interface',
                'vendor']
    assert df_arp.columns.to_list() == expected

    assert len(df_arp) >= 1


def test_get_cam_table(username,
                       password,
                       host_group,
                       nm_path,
                       play_path,
                       private_data_dir,
                       interface=None):
    """Test the 'nxos_get_cam_table' collector.
    """
    df_cam = collectors.nxos_get_cam_table(username,
                                           password,
                                           host_group,
                                           nm_path,
                                           play_path,
                                           private_data_dir,
                                           interface=None)

    expected = ['device', 'interface', 'mac', 'vlan', 'vendor']
    assert df_cam.columns.to_list() == expected

    assert len(df_cam) >= 1


def test_get_interface_descriptions(username,
                                    password,
                                    host_group,
                                    play_path,
                                    private_data_dir,
                                    interface=None):
    """Test the 'nxos_get_interface_descriptions' collector.
    """
    df_desc = collectors.nxos_get_interface_descriptions(username,
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
    host_group_all = os.environ.get('NXOS_HOST_GROUP_ALL')
    nm_path = os.environ.get('NM_PATH')
    play_path = os.environ.get('PLAY_PATH')
    private_data_dir = os.environ.get('PRIVATE_DATA_DIR')

    # Execute tests
    test_get_arp_table(username,
                       password,
                       host_group_all,
                       nm_path,
                       play_path,
                       private_data_dir,
                       reverse_dns=False)

    test_get_cam_table(username,
                       password,
                       host_group_all,
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
