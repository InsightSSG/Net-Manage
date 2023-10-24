#!/usr/bin/env python3

from netmanage.helpers import netmiko_helpers as nmh
import pandas as pd

from netmanage.parsers import cisco_asa_parsers as parser


def get_device_info(devices: dict) -> pd.DataFrame:
    """
    Gets device info for Cisco ASA devices.

    Parameters
    ----------
    devices : dict
        A dictionary containing one or more devices for which to gather info.

    Returns
    -------
    df_interface_ips : pd.DataFrame
        A DataFrame containing the interface IP addresses.
    df_inventory : pd.DataFrame
        A DataFrame containing the devices inventories.
    """
    jobs = {
        'Interface IP Addresses': {
            'get_interface_ip_addresses':
                'show interface summary | include Interface|IP address'
        },
        'Inventory': {
            'get_inventory': 'show inventory'
        }
    }

    for device in devices:
        devices[device]['jobs'] = jobs

    results = nmh.execute_commands_on_devices(devices)

    df_interface_ips = parser.asa_parse_interface_ips(results)

    df_inventory = parser.asa_parse_inventory(results)

    return df_interface_ips, df_inventory
