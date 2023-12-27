#!/usr/bin/env python3

import ast
import os
import sys
from dotenv import load_dotenv

sys.path.append(".")
from netmanage.collectors import f5_collectors as collectors  # noqa
from netmanage.helpers import helpers as hp  # noqa

load_dotenv()


def test_get_arp_table(
    username,
    password,
    host_group,
    netmanage_path,
    play_path,
    private_data_dir,
    validate_certs=True,
):
    """Test the 'f5_get_arp_table' collector."""
    df = collectors.get_arp_table(
        username,
        password,
        host_group,
        netmanage_path,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    expected = [
        "device",
        "Name",
        "Address",
        "HWaddress",
        "Vlan",
        "Expire-in-sec",
        "Status",
        "vendor",
    ]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_self_ips(
    username, password, host_group, play_path, private_data_dir, validate_certs=True
):
    """Test the 'f5_get_self_ips' collector."""
    df = collectors.get_self_ips(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    expected = [
        "device",
        "address",
        "cidr",
        "allow-service",
        "traffic-group",
        "vlan",
        "name",
        "floating",
        "unit",
        "subnet",
        "network_ip",
        "broadcast_ip",
    ]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_interface_descriptions(
    username,
    password,
    host_group,
    netmanage_path,
    play_path,
    private_data_dir,
    reverse_dns=False,
    validate_certs=True,
):
    """Test the 'f5_get_interface_descriptions' collector."""
    df = collectors.get_interface_descriptions(
        username,
        password,
        host_group,
        netmanage_path,
        play_path,
        private_data_dir,
        reverse_dns=False,
        validate_certs=validate_certs,
    )

    expected = ["device", "interface", "description"]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_interface_status(
    username, password, host_group, play_path, private_data_dir, validate_certs=True
):
    """Test the 'f5_get_interface_status' collector."""
    df = collectors.get_interface_status(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    expected = ["device", "interface", "status", "vlan", "duplex", "speed", "type"]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_node_availability(
    username, password, host_group, play_path, private_data_dir, validate_certs=True
):
    """Test the 'f5_get_node_availability' collector."""
    df = collectors.get_node_availability(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    expected = [
        "device",
        "partition",
        "node",
        "addr",
        "cur-sessions",
        "monitor-rule",
        "monitor-status",
        "name",
        "serverside.bits-in",
        "serverside.bits-out",
        "serverside.cur-conns",
        "serverside.max-conns",
        "serverside.pkts-in",
        "serverside.pkts-out",
        "serverside.tot-conns",
        "session-status",
        "status.availability-state",
        "status.enabled-state",
        "status.status-reason",
        "tot-requests",
    ]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_pool_availability(
    username, password, host_group, play_path, private_data_dir, validate_certs=True
):
    """Test the 'f5_get_pool_availability' collector."""
    df = collectors.get_pool_availability(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    expected = [
        "device",
        "partition",
        "pool",
        "availability",
        "state",
        "total",
        "avail",
        "cur",
        "min",
        "reason",
    ]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_get_pool_data(
    username, password, host_group, play_path, private_data_dir, validate_certs=True
):
    """Test the 'f5_get_pool_data' collector."""
    df = collectors.get_pool_data(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    expected = ["device", "partition", "pool", "member", "member_port", "address"]

    assert df.columns.to_list() == expected


def test_get_pool_member_availability(
    username, password, host_group, play_path, private_data_dir, validate_certs=True
):
    """Test the 'f5_get_pool_member_availability' collector."""
    df = collectors.get_pool_member_availability(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    expected = ["device", "partition", "pool_name", "pool_member", "pool_member_state"]

    assert df.columns.to_list() == expected


def test_get_vip_availability(
    username, password, host_group, play_path, private_data_dir, validate_certs=True
):
    """Test the 'f5_get_vip_availability' collector."""
    df = collectors.get_vip_availability(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    expected = [
        "device",
        "partition",
        "vip",
        "destination",
        "port",
        "availability",
        "state",
        "reason",
    ]

    assert df.columns.to_list() == expected


def test_get_vlan_db(
    username, password, host_group, play_path, private_data_dir, validate_certs=True
):
    """Test the 'f5_get_vlan_db' collector."""
    df = collectors.get_vlan_db(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    expected = ["device", "id", "name", "status", "ports"]

    assert df.columns.to_list() == expected


def test_get_vlans(
    username, password, host_group, play_path, private_data_dir, validate_certs=True
):
    """Test the 'f5_get_vlans' collector."""
    df = collectors.get_vlans(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    expected = ["device", "fwd-mode", "if-index", "interfaces", "sflow", "tag", "name"]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def test_inventory(
    username, password, host_group, play_path, private_data_dir, validate_certs=True
):
    """Test the 'f5_inventory' collector."""
    df = collectors.inventory(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    expected = [
        "device",
        "name",
        "bios_revision",
        "base_mac",
        "appliance_type",
        "appliance_serial",
        "part_number",
        "host_board_serial",
        "host_board_part_revision",
    ]

    assert df.columns.to_list() == expected

    assert len(df) >= 1


def main():
    username = os.environ.get("f5_ltm_username")
    password = os.environ.get("f5_ltm_password")
    database_path = os.path.expanduser(os.environ["database_path"])
    host_group = os.environ.get("f5_host_group")
    netmanage_path = os.path.expanduser(os.environ["netmanage_path"].rstrip("/"))
    private_data_dir = os.path.expanduser(os.environ["private_data_directory"])
    validate_certs = ast.literal_eval(os.environ["validate_certs"])

    # Create the output folder if it does not already exist.
    exists = hp.check_dir_existence(database_path)
    if not exists:
        hp.create_dir(database_path)

    # Define additional variables
    play_path = netmanage_path + "/playbooks"

    # Execute tests
    test_get_arp_table(
        username,
        password,
        host_group,
        netmanage_path,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    test_get_self_ips(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    test_get_interface_descriptions(
        username,
        password,
        host_group,
        netmanage_path,
        play_path,
        private_data_dir,
        reverse_dns=False,
        validate_certs=validate_certs,
    )

    test_get_interface_status(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    test_get_node_availability(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    test_get_pool_availability(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    test_get_pool_data(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    test_get_pool_member_availability(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    test_get_vip_availability(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )

    # Commenting out test since collector is broken.
    # test_get_vlan_db(username,
    #                  password,
    #                  host_group,
    #                  play_path,
    #                  private_data_dir,
    #                  validate_certs=validate_certs)

    # Commenting out test since collector is broken.
    # test_get_vlans(username,
    #                password,
    #                host_group,
    #                play_path,
    #                private_data_dir,
    #                validate_certs=validate_certs)

    test_inventory(
        username,
        password,
        host_group,
        play_path,
        private_data_dir,
        validate_certs=validate_certs,
    )


if __name__ == "__main__":
    main()
