#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
sys.path.append('.')
from netmanage.collectors import cisco_asa_collectors as collectors  # noqa
from netmanage.helpers import helpers as hp  # noqa

load_dotenv()


def test_inventory(username: str,
                   password: str,
                   host_group: str,
                   play_path: str,
                   private_data_dir: str):
    """
    Tests the hardware inventory collector for Cisco ASAs.
    """
    df = collectors.inventory(username,
                              password,
                              host_group,
                              play_path,
                              private_data_dir)
    expected = ['device', 'name', 'description', 'pid', 'vid', 'serial']

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_interface_ips(username: str,
                           password: str,
                           host_group: str,
                           play_path: str,
                           private_data_dir: str):
    """
    Tests the interface IPs collector for Cisco ASAs.
    """
    df = collectors.get_interface_ips(username,
                                      password,
                                      host_group,
                                      play_path,
                                      private_data_dir)
    expected = ['device',
                'interface',
                'ip',
                'nameif',
                'subnet',
                'network_ip',
                'broadcast_ip']

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def main():
    # Read environment variables.
    database_path = os.path.expanduser(os.environ['database_path'])
    host_group = os.environ.get('asa_host_group')
    netmanage_path = os.path.expanduser(
        os.environ['netmanage_path'].rstrip('/'))
    private_data_dir = os.path.expanduser(
        os.environ['private_data_directory'])

    asa_devices_username = os.environ['asa_devices_username']
    asa_devices_password = os.environ['asa_devices_password']

    # Create the output folder if it does not already exist.
    exists = hp.check_dir_existence(database_path)
    if not exists:
        hp.create_dir(database_path)

    # Define additional variables
    play_path = netmanage_path + '/playbooks'

    # Execute tests
    test_inventory(asa_devices_username,
                   asa_devices_password,
                   host_group,
                   play_path,
                   private_data_dir)

    test_get_interface_ips(asa_devices_username,
                           asa_devices_password,
                           host_group,
                           play_path,
                           private_data_dir)


if __name__ == '__main__':
    main()
