#!/usr/bin/env python3

"""A collection of helper functions for Netbox operations.

"""

import pandas as pd
import re
import json
from netmanage.collectors import netbox_collectors as nbc
import sqlite3


def get_prefix_custom_field_states(nb_path: str,
                                   token: str,
                                   f_name: str) -> pd.DataFrame:
    '''
    Gets the values of a single custom field for all prefixes.

    Queries the API to get the value of a custom field for all prefixes.
    The original purpose of this function was to get the Infoblox Object
    Reference number for networks that had been synchronized from Infoblox
    to Netbox. However, it has many other potential uses.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    f_name : str
        The name of the custom field to query.

    Returns
    -------
    df : pd.DataFrame
        A Pandas DataFrame containing the object reference number for each
        prefix ID.

    See Also
    --------
    netbox_collectors.netbox_get_ipam_prefixes : A function to get all
                                                 prefixes from a Netbox
                                                 instance.

    Examples
    --------
    >>> df = get_prefix_custom_field_states(nb_path, token, f_name)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    '''
    # Get the IPAM prefixes from Netbox
    result = nbc.netbox_get_ipam_prefixes(nb_path, token)

    # Create a dataframe containing the prefix IDs and 'f_name' values
    df = result[['id', f'custom_fields_{f_name}']].copy()

    return df


def make_nb_url_compliant(string: str):
    """
    Replaces all characters except letters, numbers, underscores,
    and hyphens with hyphens.

    Parameters
    ----------
    string : str
        string to make URL compliant for NB
    """
    return re.sub(r"[^\w\-]", "-", string)


def get_table_prefix_to_device_mfg():
    return {
        'ASA': 'CISCO',
        'BIGIP': 'F5 Networks',
        'IOS': 'CISCO',
        'MERAKI': 'MERAKI',
        'NXOS': 'CISCO',
        'PANOS': 'PALO ALTO',
    }


def get_device_types():
    return {
        'MERAKI': {
            'MS120-48FP': {
                'u_height': 1,
                'is_full_depth': False,
                'airflow': 'front-to-rear',
                'weight': '12.7',
                'weight_unit': 'lb',
                'slug': 'ms120-48fp'
            },
            'MS120-48LP': {
                'u_height': 1,
                'is_full_depth': False,
                'airflow': 'front-to-rear',
                'weight': '12.7',
                'weight_unit': 'lb',
                'slug': 'ms120-48lp'
            },
            'MX450': {
                'u_height': 1,
                'is_full_depth': False,
                'airflow': 'front-to-rear',
                'weight': '18.7',
                'weight_unit': 'lb',
                'slug': 'mx450'
            },
            'MX65': {
                'u_height': 1,
                'is_full_depth': False,
                'airflow': 'front-to-rear',
                'weight': '1.6',
                'weight_unit': 'lb',
                'slug': 'mx65'
            },
            'MX84': {
                'u_height': 1,
                'is_full_depth': False,
                'airflow': 'front-to-rear',
                'weight': '9',
                'weight_unit': 'lb',
                'slug': 'mx84'
            },
            'MX64': {
                'u_height': 1,
                'is_full_depth': False,
                'airflow': 'front-to-rear',
                'weight': '1.6',
                'weight_unit': 'lb',
                'slug': 'mx64'
            },
            'MR44': {
                'u_height': 1,
                'is_full_depth': False,
                'weight': '1.6',
                'weight_unit': 'lb',
                'slug': 'mr44'
            },
            'MR33': {
                'u_height': 1,
                'is_full_depth': False,
                'weight': '0.8',
                'weight_unit': 'lb',
                'slug': 'mr33'
            },
            'MR42': {
                'u_height': 1,
                'is_full_depth': False,
                'weight': '1.5',
                'weight_unit': 'lb',
                'slug': 'mr42'
            },
        },
        'CISCO': {
            'FPR-1120': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 8,
                'weight_unit': 'lb'
            },
            'ASR1002-X': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 17.36,
                'weight_unit': 'lb'
            },
            'ASR1002-HX': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 39.05,
                'weight_unit': 'lb'
            },
            'N2K-C2248TP-E-1GE': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 12.7,
                'weight_unit': 'lb'
            },
            'N9K-C93180YC-FX': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 47.5,
                'weight_unit': 'lb'
            },
            'WS-C2960X-24TS-LL': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 10.8,
                'weight_unit': 'lb'
            },
            'CISCO1921/K9': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 2.9,
                'weight_unit': 'lb'
            },
            'WS-C2960L-24PS-LL': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 11.2,
                'weight_unit': 'lb'
            },
            'C9410R': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 33.1,
                'weight_unit': 'lb'
            },
            'C8500-12X': {
                'u_height': 12,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 152,
                'weight_unit': 'lb'
            },
            'WS-C2960-24TT-L': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 10.8,
                'weight_unit': 'lb'
            },
            'ASR1001-X': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 6.6,
                'weight_unit': 'lb'
            },
            'WS-C2960L-48TS-LL': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 12.7,
                'weight_unit': 'lb'
            },
            'C9500-48Y4C': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 37.8,
                'weight_unit': 'lb'
            },
            'N5K-C5696Q': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '47.5',
                'weight_unit': 'lb',
                'slug': 'n5k-c5696q'
            },
            'N77-C7706': {
                'u_height': 9,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '300',
                'weight_unit': 'lb',
                'slug': 'n77-c7706'
            },
            'N2K-C2348UPQ-10GE': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '10.8',
                'weight_unit': 'lb',
                'slug': 'n2k-c2348upq-10ge'
            },
            'N5K-C5596UP': {
                'u_height': 2,
                'is_full_depth': False,
                'airflow': 'front-to-rear',
                'weight': '47.5',
                'weight_unit': 'lb',
                'slug': 'n5k-c5596up'
            },
            'CISCO2901/K9': {
                'u_height': 1,
                'airflow': 'front-to-rear',
                'is_full_depth': False,
                'weight': 9.5,
                'weight_unit': 'lb',
            },
            'ASA5555': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 25,
                'weight_unit': 'lb',
                'slug': 'asa5555'
            },
            'WS-C2960L-24TS': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 6.04,
                'weight_unit': 'lb',
                'slug': 'ws-c2960l-24ts'
            },
            'WS-C2960L-24TS-LL': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '11.2',
                'weight_unit': 'lb'
            },
            'N2K-C2348TQ-10G-E': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '12.7',
                'weight_unit': 'lb',
                'slug': 'n2k-c2348tq-10g-e'
            },
            'C9300L-48T-4X': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '16.2',
                'weight_unit': 'lb',
                'slug': 'c9300l-48t-4x'
            },
            'WS-C3850-24T': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '15.9',
                'weight_unit': 'lb',
                'slug': 'ws-c3850-24t'
            },
            'WS-C2950-24': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '10',
                'weight_unit': 'lb',
                'slug': 'ws-c2950-24'
            },
            'C9300-24T': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '16.3',
                'weight_unit': 'lb',
                'slug': 'c9300-24t'
            },
            'C9200L-24T-4X': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '10',
                'weight_unit': 'lb',
                'slug': 'c9200l-24t-4x'
            },
        },
        'F5 NETWORKS': {
            'BIG-IP i4600': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 82,
                'weight_unit': 'lb',
                'slug': 'i4600'
            }
        },
        'PALO ALTO': {
            'PA-5250': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '28.6',
                'weight_unit': 'lb'
            },
            'PA-VM': {
                'u_height': 0,
                'is_full_depth': False,
                'airflow': 'front-to-rear',
                'weight': '0',
                'weight_unit': 'lb'
            },
            'PA-5220': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '28.6',
                'weight_unit': 'lb'
            },
        },
        'DEFAULT': {
            'DEFAULT': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 0,
                'weight_unit': 'lb',
                'slug': 'default'
            }
        },
    }


def create_netbox_device_roles_json():
    """
    Creates JSON data for device roles in Netbox.
    :return: JSON string representing device roles for Netbox.
    """
    device_roles = [
        {"name": "Router", "slug": "router", "color": "0000ff",
         "description": "Routers", "vm_role": False},
        {"name": "Switch", "slug": "switch", "color": "00ff00",
         "description": "Switches", "vm_role": False},
        {"name": "Firewall", "slug": "firewall", "color": "ff0000",
         "description": "Firewalls", "vm_role": False},
        {"name": "Load Balancer", "slug": "load-balancer", "color": "ff00ff",
         "description": "Load Balancers", "vm_role": False},
        {"name": "Access Point", "slug": "access-point", "color": "ffff00",
         "description": "Access Points", "vm_role": False},
        {"name": "Wireless Lan Controller", "slug": "wireless-lan-controller",
         "color": "00ffff", "description": "Wireless Lan Controllers",
         "vm_role": False},
        {"name": "Default", "slug": "default",
         "color": "ffffff", "description": "Default",
         "vm_role": False},
    ]

    return json.dumps(device_roles, indent=4)


def create_netbox_sites_json(sites_list):
    """
    Creates JSON for site creation in Netbox from a list of site names.

    :param sites_list: List of dictionaries with 'name' key for each site.
    :return: JSON string for creating sites.
    """
    sites_json = []
    for site_entry in sites_list:
        site_name = site_entry.get('name', '')
        site_data = {
            "name": site_name,
            "slug": site_name.lower(),
        }
        sites_json.append(site_data)

    return json.dumps(sites_json, indent=4)


def create_valid_slug(name):
    # Replace invalid characters (like slashes) with an underscore
    slug = name.replace('/', '_').replace(' ', '_')
    # Ensure the slug is valid for Netbox
    return re.sub(r'[^a-zA-Z0-9_-]', '', slug).lower()


def create_netbox_device_types_json():
    """
    Creates JSON data for device types in Netbox using the device types mapping
    function.

    :return: JSON string representing device types for Netbox.
    """
    device_types_mapping = get_device_types()
    netbox_device_types = []

    for manufacturer, models in device_types_mapping.items():
        for model, attributes in models.items():
            netbox_device_type = {
                "manufacturer": manufacturer,
                "model": model,
                "slug": create_valid_slug(model),
                **attributes
            }
            netbox_device_types.append(netbox_device_type)

    return json.dumps(netbox_device_types, indent=4)


def generate_rack_dicts(rack_data):
    """
    Generates a list of dictionaries for racks based on inputted data tuples.

    :param rack_data: List of tuples, each containing rack range, site ID,
                        tenant ID, and rack height (in U).
    :return: List of rack dictionaries.
    """
    rack_dicts = []

    for data in rack_data:
        rack_range, site_id, tenant_id, u_height = data
        start, end = rack_range.split(' ~ ')
        start_group, start_number = start.split('-')
        end_group, end_number = end.split('-')

        for group in range(int(start_group), int(end_group) + 1):
            start_num = int(start_number) if group == int(start_group) else 1
            end_num = int(end_number) if group == int(end_group) else 16

            for num in range(start_num, end_num + 1):
                rack_dict = {
                    "name": f"{group}-{num}",
                    "site": site_id,
                    "tenant": tenant_id,
                    "u_height": u_height,
                }
                rack_dicts.append(rack_dict)

    return rack_dicts


def determine_device_role_by_model(model, roles_dict):
    """
    Determines the device role ID based on the device model.

    :param model: The model of the device.
    :param roles_dict: A dictionary mapping device role IDs
    :return: The ID of the determined role of the device.
    """

    # Mapping of model patterns to role display names
    model_to_role_display = {
        'ASR': 'Router',
        'CISCO29': 'Router',
        'CISCO19': 'Router',
        'Catalyst': 'Switch',
        'WS-C': 'Switch',
        'C-9500': 'Switch',
        'C9410': 'Switch',
        'C8500': 'Switch',
        'C9': 'Switch',
        'Nexus': 'Switch',
        'N9K': 'Switch',
        'N7K': 'Switch',
        'N5K': 'Switch',
        'N2K': 'Switch',
        'N77': 'Switch',
        'MS': 'Switch',
        'MX': 'Firewall',
        'ASA': 'Firewall',
        'FPR-': 'Firewall',
        'PA-': 'Firewall',
        'F5': 'Load Balancer',
        'BIG-IP': 'Load Balancer',
    }

    for model_pattern, role_display in model_to_role_display.items():
        if model_pattern in model:
            return roles_dict.get(role_display, None)
        else:
            return roles_dict.get('Default', None)


def get_site_name(hostname):
    """
    Extracts the site code from the hostname.

    :param hostname: The hostname of the device.
    :return: The extracted site code.
    """
    if hostname[:4].isdigit():
        # If the hostname starts with 4 digits, return the first 4 digits
        return hostname[:4]
    else:
        # Check for specific prefixes and return the prefix if matched
        for prefix in ["CTS", "DR", "CALL", "MMI"]:
            if hostname.startswith(prefix):
                return prefix
        # If no conditions are met
        print(f"Error: Unknown site for hostname {hostname}")
        return None


def build_devices_json(db_path, url, token):
    """
    Builds a JSON structure for devices from various tables in the database.

    :param db_path: Path to the SQLite database file.
    :param url: URL of the Netbox instance.
    :param token: API token for authentication.
    :return: JSON string representing devices for Netbox.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    devices = []
    roles_dict = nbc.fetch_device_roles_dict(url, token)
    site_mapping = nbc.fetch_site_name_id_mapping(url, token)
    types_dict = nbc.fetch_device_types_dict(url, token)
    default_type = 124
    default_site = 1106

    # Process ASA_HARDWARE_INVENTORY
    cursor.execute("SELECT device, pid, serial FROM ASA_HARDWARE_INVENTORY WHERE name = 'Chassis'")
    for device, pid, serial in cursor.fetchall():
        site_name = get_site_name(device.split('.')[0])
        site = site_mapping.get(site_name, default_site)
        role = determine_device_role_by_model(pid, roles_dict)
        device_type = types_dict.get(pid, default_type)
        if site:
            devices.append({"device": device, "device_type": device_type,
                            "serial": serial, "site": site, "role": role})

    # Process BIGIP_HARDWARE_INVENTORY
    cursor.execute(
        "SELECT device, name, appliance_serial FROM BIGIP_HARDWARE_INVENTORY")
    for device, name, serial in cursor.fetchall():
        site_name = get_site_name(name.split('.')[0])
        site = site_mapping.get(site_name, default_site)
        role = determine_device_role_by_model(name, roles_dict)
        device_type = types_dict.get(device, default_type)
        if site:
            devices.append({"device": device, "device_type": device_type,
                            "serial": serial, "site": site, "role": role})

    # Process IOS_BASIC_FACTS
    cursor.execute(
        "SELECT ansible_net_hostname, ansible_net_model, ansible_net_serialnum FROM IOS_BASIC_FACTS")
    for hostname, model, serial in cursor.fetchall():
        site_name = get_site_name(hostname.split('.')[0])
        site = site_mapping.get(site_name, default_site)
        role = determine_device_role_by_model(model, roles_dict)
        device_type = types_dict.get(model, default_type)
        if site:
            devices.append(
                {"device": hostname, "device_type":
                    device_type, "serial": serial, "site": site, "role": role})

    # Process MERAKI_ORG_DEVICES
    cursor.execute("SELECT name, model, serial FROM MERAKI_ORG_DEVICES")
    for hostname, model, serial in cursor.fetchall():
        site_name = get_site_name(hostname.split('.')[0])
        site = site_mapping.get(site_name, default_site)
        role = determine_device_role_by_model(model, roles_dict)
        device_type = types_dict.get(model, default_type)
        if site:
            devices.append(
                {"device": hostname, "device_type": device_type,
                 "serial": serial, "site": site, "role": role})

    # Process NXOS_BASIC_FACTS
    cursor.execute(
        "SELECT device, ansible_net_platform, ansible_net_serialnum FROM NXOS_BASIC_FACTS")
    for hostname, platform, serial in cursor.fetchall():
        site_name = get_site_name(hostname.split('.')[0])
        site = site_mapping.get(site_name, default_site)
        role = determine_device_role_by_model(platform, roles_dict)
        device_type = types_dict.get(platform, default_type)
        if site:
            devices.append(
                {"device": hostname, "device_type": device_type,
                 "serial": serial, "site": site, "role": role})

    # Process PANOS_BASIC_FACTS
    cursor.execute(
        "SELECT device, ansible_net_model, ansible_net_serial FROM PANOS_BASIC_FACTS")
    for hostname, model, serial in cursor.fetchall():
        site_name = get_site_name(hostname.split('.')[0])
        site = site_mapping.get(site_name, default_site)
        role = determine_device_role_by_model(model, roles_dict)
        device_type = types_dict.get(model, default_type)
        if site:
            devices.append(
                {"device": hostname, "device_type": device_type,
                 "serial": serial, "site": site, "role": role})

    conn.close()
    return json.dumps(devices, indent=4)
