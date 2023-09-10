#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv
sys.path.append('.')
from netmanage.collectors import cisco_nxos_collectors as collectors  # noqa
from netmanage.helpers import helpers as hp  # noqa

load_dotenv()


def test_get_arp_table(
    username,
    password,
    host_group,
    netmanage_path,
    play_path,
    private_data_dir,
    reverse_dns=False,
):
    """Test the 'nxos_get_arp_table' collector."""
    df_arp = collectors.nxos_get_arp_table(
        username,
        password,
        host_group,
        netmanage_path,
        play_path,
        private_data_dir,
        reverse_dns=False,
    )

    expected = [
        "device",
        "ip_address",
        "age",
        "mac_address",
        "interface",
        "vendor",
    ]

    assert df_arp.columns.to_list() == expected

    assert len(df_arp) >= 1


def test_get_cam_table(
    username,
    password,
    host_group,
    netmanage_path,
    play_path,
    private_data_dir,
    interface=None,
):
    """Test the 'nxos_get_cam_table' collector."""
    df_cam = collectors.nxos_get_cam_table(
        username,
        password,
        host_group,
        netmanage_path,
        play_path,
        private_data_dir,
        interface=None,
    )

    expected = ["device", "interface", "mac", "vlan", "vendor"]
    assert df_cam.columns.to_list() == expected

    assert len(df_cam) >= 1


def test_get_interface_descriptions(
    username, password, host_group, play_path, private_data_dir, interface=None
):
    """Test the 'nxos_get_interface_descriptions' collector."""
    df_desc = collectors.nxos_get_interface_descriptions(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        interface=None,
    )

    expected = ["device", "interface", "description"]
    assert df_desc.columns.to_list() == expected

    assert len(df_desc) >= 1


def test_nxos_get_interface_ips(
    username, password, host_group, play_path, private_data_dir
):
    """Test the 'nxos_get_interface_ips' collector."""
    df = collectors.nxos_get_interface_ips(
        username, password, host_group, play_path, private_data_dir
    )

    expected = [
        "device",
        "interface",
        "ip",
        "cidr",
        "vrf",
        "subnet",
        "network_ip",
        "broadcast_ip",
    ]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_nxos_get_interface_status(
    username, password, host_group, play_path, private_data_dir
):
    """Test the 'nxos_get_interface_status' collector."""
    df = collectors.nxos_get_interface_status(
        username, password, host_group, play_path, private_data_dir
    )

    expected = [
        "device",
        "interface",
        "status",
        "vlan",
        "duplex",
        "speed",
        "type",
    ]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_nxos_get_inventory(
    username, password, host_group, play_path, private_data_dir
):
    """Test the 'nxos_get_inventory' collector."""
    df = collectors.nxos_get_inventory(
        username, password, host_group, play_path, private_data_dir
    )

    expected = ["name", "desc", "productid", "vendorid", "serialnum", "device"]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_nxos_get_port_channel_data(
    username, password, host_group, play_path, private_data_dir
):
    """Test the 'nxos_get_port_channel_data' collector."""
    df = collectors.nxos_get_port_channel_data(
        username, password, host_group, play_path, private_data_dir
    )

    expected = [
        "device",
        "interface",
        "total_ports",
        "up_ports",
        "age",
        "port_1",
        "port_2",
        "port_3",
        "port_4",
        "port_5",
        "port_6",
        "port_7",
        "port_8",
        "first_operational_port",
        "last_bundled_member",
        "last_unbundled_member",
    ]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_nxos_get_vlan_db(
    username, password, host_group, play_path, private_data_dir
):
    """Test the 'nxos_get_vlan_db' collector."""
    df = collectors.nxos_get_vlan_db(
        username, password, host_group, play_path, private_data_dir
    )

    expected = ["device", "id", "name", "status", "ports"]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_nxos_get_vpc_state(
    username, password, host_group, play_path, private_data_dir
):
    """Test the 'nxos_get_vpc_state' collector."""
    df = collectors.nxos_get_vpc_state(
        username, password, host_group, play_path, private_data_dir
    )

    expected = [
        "device",
        "vPC domain id",
        "Peer status",
        "vPC keep-alive status",
        "Configuration consistency status",
        "Per-vlan consistency status",
        "Type-2 consistency status",
        "vPC role",
        "Number of vPCs configured",
        "Peer Gateway",
        "Dual-active excluded VLANs",
        "Graceful Consistency Check",
        "Auto-recovery status",
        "Delay-restore status",
        "Delay-restore SVI status",
        "Delay-restore Orphan-port status",
        "Operational Layer3 Peer-router",
        "Virtual-peerlink mode",
    ]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_nxos_get_vrfs(
    username, password, host_group, play_path, private_data_dir
):
    """Test the 'nxos_get_vrfs' collector."""
    df = collectors.nxos_get_vrfs(
        username, password, host_group, play_path, private_data_dir
    )

    expected = [
        "device",
        "name",
        "vrf_id",
        "state",
        "description",
        "vpn_id",
        "route_domain",
        "max_routes",
        "min_threshold",
    ]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_nxos_get_bgp_neighbors(
    username, password, host_group, netmanage_path, play_path, private_data_dir
):
    """Test the 'nxos_get_bgp_neighbors' collector."""
    df = collectors.nxos_get_bgp_neighbors(
        username, password, host_group, netmanage_path, play_path,
        private_data_dir
    )

    expected = [
        "device",
        "vrf",
        "neighbor_id",
        "version",
        "as",
        "msg_received",
        "message_sent",
        "table_version",
        "in_q",
        "out_q",
        "up_down",
        "state_pfx_rfx",
    ]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_fexes_table(
    username, password, host_group, netmanage_path, play_path, private_data_dir
):
    """Test the 'nxos_get_fexes_table' collector."""
    df_fexes = collectors.nxos_get_fexes_table(
        username, password, host_group, netmanage_path, play_path,
        private_data_dir
    )

    expected = [
        "device",
        "ip_address",
        "age",
        "mac_address",
        "interface",
        "vendor",
    ]

    assert df_fexes.columns.to_list() == expected

    assert len(df_fexes) >= 1


def main():
    username = os.environ.get('ios_devices_username')
    password = os.environ.get('ios_devices_password')
    database_path = os.path.expanduser(os.environ['database_path'])
    host_group = os.environ.get('nxos_host_group')
    netmanage_path = os.path.expanduser(
        os.environ['netmanage_path'].rstrip('/'))
    private_data_dir = os.path.expanduser(
        os.environ['private_data_directory'])

    # Create the output folder if it does not already exist.
    exists = hp.check_dir_existence(database_path)
    if not exists:
        hp.create_dir(database_path)

    # Define additional variables
    play_path = netmanage_path + '/playbooks'

    # Execute tests
    test_get_arp_table(
        username,
        password,
        host_group,
        netmanage_path,
        play_path,
        private_data_dir,
        reverse_dns=False
    )

    test_get_cam_table(
        username,
        password,
        host_group,
        netmanage_path,
        play_path,
        private_data_dir,
        interface=None
    )

    test_get_interface_descriptions(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        interface=None
    )

    test_nxos_get_interface_ips(
        username, password, host_group, play_path, private_data_dir
    )

    test_nxos_get_interface_status(
        username, password, host_group, play_path, private_data_dir
    )

    test_nxos_get_inventory(
        username, password, host_group, play_path, private_data_dir
    )

    test_nxos_get_port_channel_data(
        username, password, host_group, play_path, private_data_dir
    )

    test_nxos_get_vlan_db(
        username, password, host_group, play_path, private_data_dir
    )

    test_nxos_get_vpc_state(
        username, password, host_group, play_path, private_data_dir
    )

    test_nxos_get_vrfs(
        username, password, host_group, play_path, private_data_dir
    )

    test_nxos_get_bgp_neighbors(
        username, password, host_group, netmanage_path, play_path,
        private_data_dir
    )

    test_get_fexes_table(
        username,
        password,
        host_group,
        netmanage_path,
        play_path,
        private_data_dir
    )


if __name__ == "__main__":
    main()
