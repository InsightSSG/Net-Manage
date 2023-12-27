#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

# Change to the Net-Manage repository so imports will work
load_dotenv()
sys.path.append("..")
from netmanage.collectors import palo_alto_collectors  # noqa


def test_run_adhoc_command(
    username, password, host_group, netmanage_path, private_data_dir
):
    # Test running an XML command.
    cmd = "<show><system><info></info></system></show>"
    cmd_is_xml = True
    response = palo_alto_collectors.run_adhoc_command(
        username,
        password,
        host_group,
        netmanage_path,
        private_data_dir,
        cmd,
        cmd_is_xml,
    )
    for key in response:
        assert isinstance(response[key]["event"], str)

    # Test running a non-XML command.
    cmd = "show system software status"
    cmd_is_xml = False
    response = palo_alto_collectors.run_adhoc_command(
        username,
        password,
        host_group,
        netmanage_path,
        private_data_dir,
        cmd,
        cmd_is_xml,
    )
    for key in response:
        assert isinstance(response[key]["event"], str)


def test_get_all_interfaces(
    username, password, host_group, netmanage_path, private_data_dir, db_path
):
    # Test getting all logical interfaces.
    df_all = palo_alto_collectors.get_all_interfaces(
        username, password, host_group, netmanage_path, private_data_dir, db_path
    )
    expected = [
        "device",
        "name",
        "zone",
        "fwd",
        "vsys",
        "dyn-addr",
        "addr6",
        "tag",
        "ip",
        "id",
        "addr",
    ]
    assert set(df_all.columns.to_list()) == set(expected)


def test_get_arp_table(
    username, password, host_group, netmanage_path, private_data_dir, serials
):
    # Test getting the ARP table for all interfaces.
    df_arp = palo_alto_collectors.get_arp_table(
        username, password, host_group, netmanage_path, private_data_dir, serials
    )
    expected = ["device", "status", "ip", "mac", "ttl", "interface", "port", "vendor"]
    assert set(df_arp.columns.to_list()) == set(expected)

    # Test getting the ARP table for a single interface.
    df_arp = palo_alto_collectors.get_arp_table(
        username,
        password,
        host_group,
        netmanage_path,
        private_data_dir,
        serials,
        interface="management",
    )
    expected = ["device", "interface", "ip", "mac", "status", "vendor"]
    assert set(df_arp.columns.to_list()) == set(expected)


def test_get_logical_interfaces(
    username, password, host_group, netmanage_path, private_data_dir
):
    # Test getting all logical interfaces.
    df_logical = palo_alto_collectors.get_logical_interfaces(
        username, password, host_group, netmanage_path, private_data_dir
    )
    expected = [
        "device",
        "name",
        "zone",
        "fwd",
        "vsys",
        "dyn-addr",
        "addr6",
        "tag",
        "ip",
        "id",
        "addr",
    ]
    assert set(df_logical.columns.to_list()) == set(expected)


def test_get_physical_interfaces(
    username, password, host_group, netmanage_path, private_data_dir
):
    # Test getting all physical interfaces.
    df_phys = palo_alto_collectors.get_physical_interfaces(
        username, password, host_group, netmanage_path, private_data_dir
    )
    expected = [
        "device",
        "name",
        "duplex",
        "type",
        "state",
        "st",
        "mac",
        "mode",
        "speed",
        "id",
    ]
    assert set(df_phys.columns.to_list()) == set(expected)


def test_inventory(username, password, host_group, netmanage_path, private_data_dir):
    # Test getting the hardware inventory.
    df_inventory = palo_alto_collectors.inventory(
        username, password, host_group, netmanage_path, private_data_dir
    )

    # The expected columns if there is a mix of physical and virtual appliances
    expected_with_vms = [
        "device",
        "hostname",
        "ip-address",
        "public-ip-address",
        "netmask",
        "default-gateway",
        "is-dhcp",
        "ipv6-address",
        "ipv6-link-local-address",
        "mac-address",
        "time",
        "uptime",
        "devicename",
        "family",
        "model",
        "serial",
        "cloud-mode",
        "sw-version",
        "global-protect-client-package-version",
        "device-dictionary-version",
        "device-dictionary-release-date",
        "app-version",
        "app-release-date",
        "av-version",
        "av-release-date",
        "threat-version",
        "threat-release-date",
        "wf-private-version",
        "wf-private-release-date",
        "url-db",
        "wildfire-version",
        "wildfire-release-date",
        "wildfire-rt",
        "url-filtering-version",
        "global-protect-datafile-version",
        "global-protect-datafile-release-date",
        "global-protect-clientless-vpn-version",
        "logdb-version",
        "plugin_versions",
        "platform-family",
        "high-speed-log-forwarding-mode",
        "vpn-disable-mode",
        "multi-vsys",
        "operational-mode",
        "device-certificate-status",
        "vm-uuid",
        "vm-cpuid",
        "vm-license",
        "vm-cap-tier",
        "vm-cores",
        "vm-mem",
        "relicense",
        "vm-mode",
        "global-protect-clientless-vpn-release-date",
    ]

    # The expected columns if there are only physical appliances.
    expected_physical_only = [
        "device",
        "hostname",
        "ip-address",
        "public-ip-address",
        "netmask",
        "default-gateway",
        "is-dhcp",
        "ipv6-address",
        "ipv6-link-local-address",
        "mac-address",
        "time",
        "uptime",
        "devicename",
        "family",
        "model",
        "serial",
        "cloud-mode",
        "sw-version",
        "global-protect-client-package-version",
        "device-dictionary-version",
        "device-dictionary-release-date",
        "app-version",
        "app-release-date",
        "av-version",
        "av-release-date",
        "threat-version",
        "threat-release-date",
        "wf-private-version",
        "wf-private-release-date",
        "url-db",
        "wildfire-version",
        "wildfire-release-date",
        "wildfire-rt",
        "url-filtering-version",
        "global-protect-datafile-version",
        "global-protect-datafile-release-date",
        "global-protect-clientless-vpn-version",
        "logdb-version",
        "plugin_versions",
        "platform-family",
        "high-speed-log-forwarding-mode",
        "vpn-disable-mode",
        "multi-vsys",
        "operational-mode",
        "device-certificate-status",
    ]

    # The expected columns if there are only VM appliances.
    expected_vms_only = [
        "device",
        "hostname",
        "ip-address",
        "public-ip-address",
        "netmask",
        "default-gateway",
        "is-dhcp",
        "ipv6-address",
        "ipv6-link-local-address",
        "mac-address",
        "time",
        "uptime",
        "devicename",
        "family",
        "model",
        "serial",
        "vm-uuid",
        "vm-cpuid",
        "vm-license",
        "vm-cap-tier",
        "vm-cores",
        "vm-mem",
        "relicense",
        "vm-mode",
        "cloud-mode",
        "sw-version",
        "global-protect-client-package-version",
        "device-dictionary-version",
        "device-dictionary-release-date",
        "app-version",
        "app-release-date",
        "av-version",
        "av-release-date",
        "threat-version",
        "threat-release-date",
        "wf-private-version",
        "wf-private-release-date",
        "url-db",
        "wildfire-version",
        "wildfire-release-date",
        "wildfire-rt",
        "url-filtering-version",
        "global-protect-datafile-version",
        "global-protect-datafile-release-date",
        "global-protect-clientless-vpn-version",
        "global-protect-clientless-vpn-release-date",
        "logdb-version",
        "plugin_versions",
        "platform-family",
        "vpn-disable-mode",
        "multi-vsys",
        "operational-mode",
        "device-certificate-status",
    ]

    assert (
        set(df_inventory.columns.to_list()) == set(expected_with_vms)
        or set(df_inventory.columns.to_list()) == set(expected_vms_only)
        or set(df_inventory.columns.to_list()) == set(expected_physical_only)
    )


def main():
    username = os.environ.get("palo_alto_username")
    password = os.environ.get("palo_alto_password")
    host_group = os.environ.get("palo_host_group")
    netmanage_path = os.path.expanduser(os.environ.get("netmanage_path"))
    private_data_dir = os.path.expanduser(os.environ.get("private_data_directory"))
    database_name = os.environ["database_name"]
    database_path = os.path.expanduser(os.environ["database_path"])
    database_full_path = f"{database_path}/{database_name}"
    serials = [_.strip() for _ in os.environ.get("palo_alto_serials").split(",")]

    # Execute tests
    test_run_adhoc_command(
        username, password, host_group, netmanage_path, private_data_dir
    )

    test_get_all_interfaces(
        username,
        password,
        host_group,
        netmanage_path,
        private_data_dir,
        database_full_path,
    )

    test_get_arp_table(
        username, password, host_group, netmanage_path, private_data_dir, serials
    )

    test_get_logical_interfaces(
        username, password, host_group, netmanage_path, private_data_dir
    )

    test_get_physical_interfaces(
        username, password, host_group, netmanage_path, private_data_dir
    )

    test_inventory(username, password, host_group, netmanage_path, private_data_dir)


if __name__ == "__main__":
    main()
