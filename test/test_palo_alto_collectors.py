#!/usr/bin/env python3

import os
import sys
sys.path.append('..')
from collectors import palo_alto_collectors  # noqa


def test_run_adhoc_command(username,
                           password,
                           host_group,
                           nm_path,
                           private_data_dir):
    # Test running an XML command.
    cmd = '<show><system><info></info></system></show>'
    cmd_is_xml = True
    response = palo_alto_collectors.run_adhoc_command(username,
                                                      password,
                                                      host_group,
                                                      nm_path,
                                                      private_data_dir,
                                                      cmd,
                                                      cmd_is_xml)
    for key in response:
        assert isinstance(response[key]['event'], str)

    # Test running a non-XML command.
    cmd = 'show system software status'
    cmd_is_xml = False
    response = palo_alto_collectors.run_adhoc_command(username,
                                                      password,
                                                      host_group,
                                                      nm_path,
                                                      private_data_dir,
                                                      cmd,
                                                      cmd_is_xml)
    for key in response:
        assert isinstance(response[key]['event'], str)


def test_get_arp_table(username,
                       password,
                       host_group,
                       nm_path,
                       private_data_dir,
                       interface=str()):

    # Test getting the ARP table for all interfaces.
    df_arp = palo_alto_collectors.get_arp_table(username,
                                                password,
                                                host_group,
                                                nm_path,
                                                private_data_dir)
    expected = ['device',
                'status',
                'ip',
                'mac',
                'ttl',
                'interface',
                'port',
                'vendor']
    assert df_arp.columns.to_list() == expected

    # Test getting the ARP table for a single interface.
    df_arp = palo_alto_collectors.get_arp_table(username,
                                                password,
                                                host_group,
                                                nm_path,
                                                private_data_dir,
                                                interface='management')
    expected = ['device', 'interface', 'ip', 'mac', 'status', 'vendor']
    assert df_arp.columns.to_list() == expected


def test_get_logical_interfaces(username,
                                password,
                                host_group,
                                nm_path,
                                private_data_dir):
    # Test getting all logical interfaces.
    df_logical = palo_alto_collectors.get_logical_interfaces(username,
                                                             password,
                                                             host_group,
                                                             nm_path,
                                                             private_data_dir)
    expected = ['device',
                'name',
                'zone',
                'fwd',
                'vsys',
                'dyn-addr',
                'addr6',
                'tag',
                'ip',
                'id',
                'addr']
    assert df_logical.columns.to_list() == expected


def test_get_physical_interfaces(username,
                                 password,
                                 host_group,
                                 nm_path,
                                 private_data_dir):
    # Test getting all physical interfaces.
    df_phys = palo_alto_collectors.get_physical_interfaces(username,
                                                           password,
                                                           host_group,
                                                           nm_path,
                                                           private_data_dir)
    expected = ['device',
                'name',
                'duplex',
                'type',
                'state',
                'st',
                'mac',
                'mode',
                'speed',
                'id']
    assert df_phys.columns.to_list() == expected


def main():
    username = os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    host_group = os.environ.get('HOST_GROUP')
    nm_path = os.environ.get('NM_PATH')
    private_data_dir = os.environ.get('PRIVATE_DATA_DIR')

    test_run_adhoc_command(username,
                           password,
                           host_group,
                           nm_path,
                           private_data_dir)

    test_get_arp_table(username,
                       password,
                       host_group,
                       nm_path,
                       private_data_dir)

    test_get_logical_interfaces(username,
                                password,
                                host_group,
                                nm_path,
                                private_data_dir)

    test_get_physical_interfaces(username,
                                 password,
                                 host_group,
                                 nm_path,
                                 private_data_dir)


if __name__ == '__main__':
    main()
