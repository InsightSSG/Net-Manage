#!/usr/bin/env python3

import os
import sys

# Change to the Net-Manage repository so imports will work
nm_path = os.environ.get('NM_PATH')
os.chdir(f'{nm_path}/test')
sys.path.append('..')
from collectors import f5_collectors as collectors  # noqa


def test_get_arp_table(username,
                       password,
                       host_group,
                       nm_path,
                       play_path,
                       private_data_dir,
                       validate_certs=False):
    """Test the 'f5_get_arp_table' collector.
    """
    df = collectors.get_arp_table(username,
                                  password,
                                  host_group,
                                  nm_path,
                                  play_path,
                                  private_data_dir,
                                  validate_certs=False)

    expected = ['device',
                'Name',
                'Address',
                'HWaddress',
                'Vlan',
                'Expire-in-sec',
                'Status',
                'vendor']

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_self_ips(username,
                      password,
                      host_group,
                      play_path,
                      private_data_dir,
                      validate_certs=True):
    """Test the 'f5_get_self_ips' collector.
    """
    df = collectors.get_self_ips(username,
                                 password,
                                 host_group,
                                 play_path,
                                 private_data_dir,
                                 validate_certs=False)

    expected = ['device', 'address', 'allow-service',
                'traffic-group', 'vlan', 'name']

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_interface_descriptions(username,
                                    password,
                                    host_group,
                                    nm_path,
                                    play_path,
                                    private_data_dir,
                                    reverse_dns=False,
                                    validate_certs=False):
    """Test the 'f5_get_interface_descriptions' collector.
    """
    df = collectors.get_interface_descriptions(username,
                                               password,
                                               host_group,
                                               nm_path,
                                               play_path,
                                               private_data_dir,
                                               reverse_dns=False,
                                               validate_certs=False)

    expected = ['device', 'interface', 'description']

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_interface_status(username,
                              password,
                              host_group,
                              play_path,
                              private_data_dir,
                              validate_certs=False):
    """Test the 'f5_get_interface_status' collector.
    """
    df = collectors.get_interface_status(username,
                                         password,
                                         host_group,
                                         play_path,
                                         private_data_dir,
                                         validate_certs=False)

    expected = ['device', 'interface', 'status',
                'vlan', 'duplex', 'speed', 'type']

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_node_availability(username,
                               password,
                               host_group,
                               play_path,
                               private_data_dir,
                               validate_certs=False):
    """Test the 'f5_get_node_availability' collector.
    """
    df = collectors.get_node_availability(username,
                                          password,
                                          host_group,
                                          play_path,
                                          private_data_dir,
                                          validate_certs=False)

    expected = ['device', 'partition', 'node', 'addr',
                'cur-sessions', 'monitor-rule', 'monitor-status',
                'name', 'serverside.bits-in', 'serverside.bits-out',
                'serverside.cur-conns', 'serverside.max-conns',
                'serverside.pkts-in', 'serverside.pkts-out',
                'serverside.tot-conns', 'session-status',
                'status.availability-state', 'status.enabled-state',
                'status.status-reason', 'tot-requests']

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_pool_availability(username,
                               password,
                               host_group,
                               play_path,
                               private_data_dir,
                               validate_certs=False):
    """Test the 'f5_get_pool_availability' collector.
    """
    df = collectors.get_pool_availability(username,
                                          password,
                                          host_group,
                                          play_path,
                                          private_data_dir,
                                          validate_certs=False)

    expected = ['device', 'partition', 'pool', 'availability',
                'state', 'total', 'avail', 'cur', 'min', 'reason']

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_pool_data(username,
                       password,
                       host_group,
                       play_path,
                       private_data_dir,
                       validate_certs=False):
    """Test the 'f5_get_pool_data' collector.
    """
    df = collectors.get_pool_data(username,
                                  password,
                                  host_group,
                                  play_path,
                                  private_data_dir,
                                  validate_certs=False)

    expected = ['device', 'partition', 'pool',
                'member', 'member_port', 'address']

    assert df.columns.to_list() == expected


def test_get_pool_member_availability(username,
                                      password,
                                      host_group,
                                      play_path,
                                      private_data_dir,
                                      validate_certs=False):
    """Test the 'f5_get_pool_member_availability' collector.
    """
    df = collectors.get_pool_member_availability(username,
                                                 password,
                                                 host_group,
                                                 play_path,
                                                 private_data_dir,
                                                 validate_certs=False)

    expected = ['device', 'partition', 'pool_name',
                'pool_member', 'pool_member_state']

    assert df.columns.to_list() == expected


def test_get_pools_and_members(username,
                               password,
                               host_group,
                               play_path,
                               private_data_dir,
                               validate_certs=False):
    """Test the 'f5_get_pool_member_availability' collector.
    """
    df = collectors.get_pools_and_members(username,
                                          password,
                                          host_group,
                                          play_path,
                                          private_data_dir,
                                          validate_certs=False)

    expected = ['device', 'partition', 'pool', 'member', 'address']

    assert df.columns.to_list() == expected


def test_get_vip_availability(username,
                              password,
                              host_group,
                              play_path,
                              private_data_dir,
                              validate_certs=False):
    """Test the 'f5_get_vip_availability' collector.
    """
    df = collectors.get_vip_availability(username,
                                         password,
                                         host_group,
                                         play_path,
                                         private_data_dir,
                                         validate_certs=False)

    expected = ['device', 'partition', 'vip', 'destination',
                'port', 'availability', 'state', 'reason']

    assert df.columns.to_list() == expected


def test_get_vip_summary(username,
                         password,
                         host_group,
                         play_path,
                         private_data_dir,
                         validate_certs=False,
                         db_path,
                         timestamp,):
    """Test the 'f5_get_vip_summary' collector.
    """
    df_pools = collectors.build_pool_table(username,
                                           password,
                                           host_group,
                                           play_path,
                                           private_data_dir,
                                           db_path,
                                           timestamp,
                                           validate_certs=False)

    df = collectors.get_vip_summary(username,
                                    password,
                                    host_group,
                                    play_path,
                                    private_data_dir,
                                    df_pools,
                                    validate_certs=False)

    expected = []

    assert df.columns.to_list() == expected


def test_get_vlan_db(username,
                     password,
                     host_group,
                     play_path,
                     private_data_dir,
                     validate_certs=False):
    """Test the 'f5_get_vlan_db' collector.
    """
    df = collectors.get_vlan_db(username,
                                password,
                                host_group,
                                play_path,
                                private_data_dir,
                                validate_certs=False)

    expected = ['device', 'id', 'name', 'status', 'ports']

    assert df.columns.to_list() == expected


def test_get_vlans(username,
                   password,
                   host_group,
                   play_path,
                   private_data_dir,
                   validate_certs=False):
    """Test the 'f5_get_vlans' collector.
    """
    df = collectors.get_vlans(username,
                              password,
                              host_group,
                              play_path,
                              private_data_dir,
                              validate_certs=False)

    expected = ['device', 'fwd-mode', 'if-index',
                'interfaces', 'sflow', 'tag', 'name']

    assert df.columns.to_list() == expected


def main():
    username = os.environ.get('USERNAME')
    password = os.environ.get('PASSWORD')
    host_group = os.environ.get('HOST_GROUP')
    nm_path = os.environ.get('NM_PATH')
    play_path = os.environ.get('PLAY_PATH')
    private_data_dir = os.environ.get('PRIVATE_DATA_DIR')

    # Execute tests
    test_get_arp_table(username,
                       password,
                       host_group,
                       nm_path,
                       play_path,
                       private_data_dir,
                       validate_certs=False)

    test_get_self_ips(username,
                      password,
                      host_group,
                      play_path,
                      private_data_dir,
                      validate_certs=False)

    test_get_interface_descriptions(username,
                                    password,
                                    host_group,
                                    nm_path,
                                    play_path,
                                    private_data_dir,
                                    reverse_dns=False,
                                    validate_certs=False)

    test_get_interface_status(username,
                              password,
                              host_group,
                              play_path,
                              private_data_dir,
                              validate_certs=False)

    test_get_node_availability(username,
                               password,
                               host_group,
                               play_path,
                               private_data_dir,
                               validate_certs=False)

    test_get_pool_availability(username,
                               password,
                               host_group,
                               play_path,
                               private_data_dir,
                               validate_certs=False)

    test_get_pool_data(username,
                       password,
                       host_group,
                       play_path,
                       private_data_dir,
                       validate_certs=False)

    test_get_pool_member_availability(username,
                                      password,
                                      host_group,
                                      play_path,
                                      private_data_dir,
                                      validate_certs=False)

    test_get_pools_and_members(username,
                               password,
                               host_group,
                               play_path,
                               private_data_dir,
                               validate_certs=False)

    test_get_vip_availability(username,
                              password,
                              host_group,
                              play_path,
                              private_data_dir,
                              validate_certs=False)

    # test_get_vip_summary(username,
    #                password,
    #                host_group,
    #                play_path,
    #                private_data_dir,
    #                validate_certs=False)

    test_get_vlan_db(username,
                     password,
                     host_group,
                     play_path,
                     private_data_dir,
                     validate_certs=False)

    test_get_vlans(username,
                   password,
                   host_group,
                   play_path,
                   private_data_dir,
                   validate_certs=False)


if __name__ == '__main__':
    main()
