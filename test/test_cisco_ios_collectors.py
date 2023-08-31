#!/usr/bin/env python3

import ast
import os
import sys
from dotenv import load_dotenv
sys.path.append('.')
from netmanage.collectors import cisco_ios_collectors as collectors  # noqa
from netmanage.helpers import helpers as hp  # noqa

load_dotenv()


def test_get_arp_table(ios_devices_username,
                       ios_devices_password,
                       host_group,
                       netmanage_path,
                       play_path,
                       private_data_dir):
    """Test the 'ios_get_arp_table' collector.
    """
    df_arp = collectors.ios_get_arp_table(ios_devices_username,
                                          ios_devices_password,
                                          host_group,
                                          netmanage_path,
                                          play_path,
                                          private_data_dir)

    expected = ['device',
                'protocol',
                'address',
                'age',
                'mac',
                'inf_type',
                'interface',
                'vendor']
    assert df_arp.columns.to_list() == expected

    assert len(df_arp) >= 1


def test_get_cam_table(ios_devices_username,
                       ios_devices_password,
                       host_group,
                       netmanage_path,
                       play_path,
                       private_data_dir,
                       interface=None):
    """Test the 'ios_get_cam_table' collector.
    """
    df_cam = collectors.ios_get_cam_table(ios_devices_username,
                                          ios_devices_password,
                                          host_group,
                                          netmanage_path,
                                          play_path,
                                          private_data_dir,
                                          interface=None)

    expected = ['device', 'vlan', 'mac', 'inf_type', 'ports', 'vendor']
    assert df_cam.columns.to_list() == expected

    assert len(df_cam) >= 1


def test_get_interface_descriptions(ios_devices_username,
                                    ios_devices_password,
                                    host_group,
                                    play_path,
                                    private_data_dir,
                                    interface=None):
    """Test the 'ios_get_interface_descriptions' collector.
    """
    df_desc = collectors.ios_get_interface_descriptions(ios_devices_username,
                                                        ios_devices_password,
                                                        host_group,
                                                        play_path,
                                                        private_data_dir,
                                                        interface=None)

    expected = ['device', 'interface', 'description']
    assert df_desc.columns.to_list() == expected

    assert len(df_desc) >= 1


def test_get_vrfs(ios_devices_username: str,
                  ios_devices_password: str,
                  host_group: str,
                  play_path: str,
                  private_data_dir: str):
    """Test the 'get_vrfs' collector.
    """
    df = collectors.get_vrfs(ios_devices_username,
                             ios_devices_password,
                             host_group,
                             play_path,
                             private_data_dir)

    expected = ['device', 'Name', 'Default RD', 'Protocols', 'Interfaces']

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def main():
    # Read environment variables.
    database_name = os.environ['database_name']
    database_path = os.path.expanduser(os.environ['database_path'])
    netmanage_path = os.path.expanduser(
        os.environ['netmanage_path'].strip('/'))
    private_data_dir = os.path.expanduser(
        os.environ['private_data_directory'])
    # validate_certs = ast.literal_eval(os.environ['validate_certs'])
    # database_method = os.environ['database_method']

    ios_devices_username = os.environ['ios_devices_username']
    ios_devices_password = os.environ['ios_devices_password']

    # Create the output folder if it does not already exist.
    exists = hp.check_dir_existence(database_path)
    if not exists:
        hp.create_dir(database_path)

    # Define additional variables
    play_path = netmanage_path + '/playbooks'

    # Define the host group to test against.
    host_group = 'mgmt'

    # Execute tests
    test_get_arp_table(ios_devices_username,
                       ios_devices_password,
                       host_group,
                       netmanage_path,
                       play_path,
                       private_data_dir)

    test_get_cam_table(ios_devices_username,
                       ios_devices_password,
                       host_group,
                       netmanage_path,
                       play_path,
                       private_data_dir,
                       interface=None)

    test_get_interface_descriptions(ios_devices_username,
                                    ios_devices_password,
                                    host_group,
                                    play_path,
                                    private_data_dir,
                                    interface=None)

    test_get_vrfs(ios_devices_username,
                  ios_devices_password,
                  host_group,
                  play_path,
                  private_data_dir)


if __name__ == '__main__':
    main()
