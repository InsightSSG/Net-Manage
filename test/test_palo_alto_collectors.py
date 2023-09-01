#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

# Change to the Net-Manage repository so imports will work
load_dotenv()
netmanage_path = os.environ['netmanage_path']
os.chdir(f'{netmanage_path}/test')
sys.path.append('..')
from netmanage.collectors import palo_alto_collectors  # noqa


def test_run_adhoc_command(username,
                           password,
                           host_group,
                           netmanage_path,
                           private_data_dir):
    # Test running an XML command.
    cmd = '<show><system><info></info></system></show>'
    cmd_is_xml = True
    response = palo_alto_collectors.run_adhoc_command(username,
                                                      password,
                                                      host_group,
                                                      netmanage_path,
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
                                                      netmanage_path,
                                                      private_data_dir,
                                                      cmd,
                                                      cmd_is_xml)
    for key in response:
        assert isinstance(response[key]['event'], str)


def test_get_all_interfaces(username,
                            password,
                            host_group,
                            netmanage_path,
                            private_data_dir):
    # Test getting all logical interfaces.
    df_all = palo_alto_collectors.get_all_interfaces(username,
                                                     password,
                                                     host_group,
                                                     netmanage_path,
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
    assert set(df_all.columns.to_list()) == set(expected)


def test_get_arp_table(username,
                       password,
                       host_group,
                       netmanage_path,
                       private_data_dir):

    # Test getting the ARP table for all interfaces.
    df_arp = palo_alto_collectors.get_arp_table(username,
                                                password,
                                                host_group,
                                                netmanage_path,
                                                private_data_dir)
    expected = ['device',
                'status',
                'ip',
                'mac',
                'ttl',
                'interface',
                'port',
                'vendor']
    assert set(df_arp.columns.to_list()) == set(expected)

    # Test getting the ARP table for a single interface.
    df_arp = palo_alto_collectors.get_arp_table(username,
                                                password,
                                                host_group,
                                                netmanage_path,
                                                private_data_dir,
                                                interface='management')
    expected = ['device', 'interface', 'ip', 'mac', 'status', 'vendor']
    assert set(df_arp.columns.to_list()) == set(expected)


def test_get_logical_interfaces(username,
                                password,
                                host_group,
                                netmanage_path,
                                private_data_dir):
    # Test getting all logical interfaces.
    df_logical = palo_alto_collectors.get_logical_interfaces(username,
                                                             password,
                                                             host_group,
                                                             netmanage_path,
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
    assert set(df_logical.columns.to_list()) == set(expected)


def test_get_physical_interfaces(username,
                                 password,
                                 host_group,
                                 netmanage_path,
                                 private_data_dir):
    # Test getting all physical interfaces.
    df_phys = palo_alto_collectors.get_physical_interfaces(username,
                                                           password,
                                                           host_group,
                                                           netmanage_path,
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
    assert set(df_phys.columns.to_list()) == set(expected)


def main():
    username = os.environ.get('palo_alto_username')
    password = os.environ.get('palo_alto_password')
    host_group = os.environ.get('palo_host_group')
    private_data_dir = os.environ.get('private_data_directory')

    # Execute tests
    test_run_adhoc_command(username,
                           password,
                           host_group,
                           netmanage_path,
                           private_data_dir)

    test_get_all_interfaces(username,
                            password,
                            host_group,
                            netmanage_path,
                            private_data_dir)

    test_get_arp_table(username,
                       password,
                       host_group,
                       netmanage_path,
                       private_data_dir)

    test_get_logical_interfaces(username,
                                password,
                                host_group,
                                netmanage_path,
                                private_data_dir)

    test_get_physical_interfaces(username,
                                 password,
                                 host_group,
                                 netmanage_path,
                                 private_data_dir)


if __name__ == '__main__':
    main()
