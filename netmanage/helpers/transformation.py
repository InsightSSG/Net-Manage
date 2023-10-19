import pandas as pd
import re
from typing import Callable, Dict, List, Tuple, Union, Any

"""
Provides utilities for transforming data based on a predefined schema.

Functions:
- get_function_mapping: Returns a mapping between function names and functions.
- get_mapping_schema: Provides the schema used for data transformation.
- seconds_to_ios_format: Converts seconds into an IOS-like BGP timer format.
- set_column_order: Sets the desired column order for DataFrames.
- split_domain: Splits a device name into device and domain parts.
- split_ip_port: Splits an IP address and its port.
- standardize_timestamp: Standardizes the timestamp format.
- transform_dataframe: Transforms a DataFrame using the provided schema.
- transform_dataframe_row: Transforms a DataFrame row based on the schema.
- transform_row: Transforms a row of data based on the given schema.
"""


def get_function_mapping() -> Dict[str, Callable]:
    """
    Return a dictionary mapping function names in the schema to actual
    functions.

    Returns
    -------
    dict
        A dictionary where keys are function names as used in the schema,
        and values are the actual callable functions.

    Notes
    -----
    This mapping provides a way to call the appropriate transformation
    function based on its name in the schema.
    """
    return {
        'standardize_timestamp': standardize_timestamp,
        'bgp_state_timer': seconds_to_ios_format
    }


def get_mapping_schema() -> Dict[str, Dict[str, Union[str, Dict[str, Any]]]]:
    """
    Return the mapping schema for data transformation.

    Returns
    -------
    dict
        A dictionary defining the transformation schema for each table.

    Notes
    -----
    The schema is used to determine how each data entry should be transformed
    or mapped to its new format or column.
    """
    return {
        # ARP TABLES
        'BIGIP_ARP_TABLE': {
            'timestamp': {
                'function': {
                    'name': 'standardize_timestamp',
                    'args': []
                }
            },
            'device': 'device',
            'Name': 'entry_name',
            'Address': 'ip_address',
            'HWaddress': 'mac_address',
            'Vlan': 'vlan',
            'Expire-in-sec': 'expiry_time_seconds',
            'Status': 'arp_status',
            'vendor': 'vendor'
        },
        'IOS_ARP_TABLE': {
            'timestamp': {
                'function': {
                    'name': 'standardize_timestamp',
                    'args': []
                }
            },
            'device': 'device',
            'protocol': 'protocol',
            'address': 'ip_address',
            'age': 'age',
            'mac': 'mac_address',
            'inf_type': 'interface_type',
            'interface': 'interface_name',
            'vendor': 'vendor'
        },
        'NXOS_ARP_TABLE': {
            'timestamp': {
                'function': {
                    'name': 'standardize_timestamp',
                    'args': []
                }
            },
            'device': 'device',
            'ip_address': 'ip_address',
            'age': 'age',
            'mac_address': 'mac_address',
            'interface': 'interface_name',
            'vendor': 'vendor'
        },
        'PANOS_ARP_TABLE': {
            'timestamp': {
                'function': {
                    'name': 'standardize_timestamp',
                    'args': []
                }
            },
            'device': 'device',
            'status': 'arp_status',
            'ip': 'ip_address',
            'mac': 'mac_address',
            'ttl': 'ttl_seconds',
            'interface': 'interface_name',
            'port': 'interface_port',
            'vendor': 'vendor'
        },
        # BGP NEIGHBORS
        'IOS_BGP_NEIGHBORS': {
            'bgp_neighbor': 'bgp_neighbor',
            'local_host': 'local_address',
            'timestamp': {
                'function': {
                    'name': 'standardize_timestamp',
                    'args': []
                }
            },
            'device': {
                'split': ['device', 'domain']
            },
            'vrf': 'vrf',
            'local_as': 'local_as',
            'remote_as': 'remote_as',
            'peer_group': 'peer_group',
            'bgp_version': 'bgp_version',
            'neighbor_id': 'neighbor_id',
            'bgp_state': 'bgp_state',
            'bgp_state_timer': 'bgp_state_timer'
        },
        'PANOS_BGP_NEIGHBORS': {
            'timestamp': {
                'function': {
                    'name': 'standardize_timestamp',
                    'args': []
                }
            },
            'device': 'device',
            '@peer': 'neighbor',
            '@vr': 'vrf',
            'peer-group': 'peer_group',
            'peer-router-id': 'neighbor_id',
            'remote-as': 'remote_as',
            'status': 'status',
            'status-duration': {
                'function': {
                    'name': 'bgp_state_timer',
                    'args': []
                }
            },
            'password-set': 'password_set',
            'passive': 'passive',
            'multi-hop-ttl': 'multi_hop_ttl',
            'peer-address': 'remote_address',
            'local-address': 'local_address',
            'reflector-client': 'reflector_client',
            'same-confederation': 'same_confederation',
            'aggregate-confed-as': 'aggregate_confed_as',
            'peering-type': 'peering_type',
            'connect-retry-interval': 'connect_retry_interval',
            'open-delay': 'open_delay',
            'idle-hold': 'idle_hold',
            'prefix-limit': 'prefix_limit',
            'holdtime': 'holdtime',
            'holdtime-config': 'holdtime_config',
            'keepalive': 'keepalive',
            'keepalive-config': 'keepalive_config',
            'msg-update-in': 'msg_update_in',
            'msg-update-out': 'msg_update_out',
            'msg-total-in': 'msg_total_in',
            'msg-total-out': 'msg_total_out',
            'last-update-age': 'last_update_age',
            'last-error': 'last_error',
            'status-flap-counts': 'status_flap_counts',
            'established-counts': 'established_counts',
            'ORF-entry-received': 'orf_entry_received',
            'nexthop-self': 'nexthop_self',
            'nexthop-thirdparty': 'nexthop_thirdparty',
            'nexthop-peer': 'nexthop_peer',
            'config': 'config',
            'peer-capability': 'peer_capability',
            'prefix-counter': 'prefix_counter'
        },
        # HARDWARE INVENTORY
        'ASA_HARDWARE_INVENTORY': {
            'timestamp': {
                'function': {
                    'name': 'standardize_timestamp',
                    'args': []
                }
            },
            'device': 'device',
            'name': 'name',
            'description': 'description',
            'pid': 'product_id',
            'vid': 'vendor_id',
            'serial': 'serial'
        },
        'BIGIP_HARDWARE_INVENTORY': {
            'timestamp': {
                'function': {
                    'name': 'standardize_timestamp',
                    'args': []
                }
            },
            'device': 'device',
            'name': 'name',
            'bios_revision': 'bios_revision',
            'base_mac': 'mac_address',
            'appliance_type': 'appliance_type',
            'appliance_serial': 'serial'
        },
        'IOS_HARDWARE_INVENTORY': {
            'timestamp': {
                'function': {
                    'name': 'standardize_timestamp',
                    'args': []
                }
            },
            'device': 'device',
            'name': 'name',
            'description': 'description',
            'pid': 'product_id',
            'vid': 'vendor_id',
            'serial': 'serial'
        },
        'NXOS_HARDWARE_INVENTORY': {
            'timestamp': {
                'function': {
                    'name': 'standardize_timestamp',
                    'args': []
                }
            },
            'device': 'device',
            'name': 'name',
            'desc': 'description',
            'productid': 'product_id',
            'vendorid': 'vendor_id',
            'serialnum': 'serial'
        },
        'PANOS_HARDWARE_INVENTORY': {
            'timestamp': {
                'function': {
                    'name': 'standardize_timestamp',
                    'args': []
                }
            },
            'device': 'device',
            'hostname': 'hostname',
            'ip-address': 'ip_address',
            'public-ip-address': 'public_ip_address',
            'netmask': 'netmask',
            'default-gateway': 'default_gateway',
            'is-dhcp': 'is_dhcp',
            'ipv6-address': 'ipv6_address',
            'ipv6-link-local-address': 'ipv6_link_local_address',
            'mac-address': 'mac_address',
            'time': 'time',
            'uptime': 'uptime',
            'devicename': 'device_name',
            'family': 'family',
            'model': 'model',
            'serial': 'serial',
            'cloud-mode': 'cloud_mode',
            'sw-version': 'software_version',
            'global-protect-client-package-version':
                'global_protect_client_package_version',
            'device-dictionary-version': 'device_dictionary_version',
            'device-dictionary-release-date': 'device_dictionary_release_date',
            'app-version': 'app_version',
            'app-release-date': 'app_release_date',
            'av-version': 'av_version',
            'av-release-date': 'av_release_date',
            'threat-version': 'threat_version',
            'threat-release-date': 'threat_release_date',
            'wf-private-version': 'wf_private_version',
            'wf-private-release-date': 'wf_private_release_date',
            'url-db': 'url_db',
            'wildfire-version': 'wildfire_version',
            'wildfire-release-date': 'wildfire_release_date',
            'wildfire-rt': 'wildfire_rt',
            'url-filtering-version': 'url_filtering_version',
            'global-protect-datafile-version':
                'global_protect_datafile_version',
            'global-protect-datafile-release-date':
                'global_protect_datafile_release_date',
            'global-protect-clientless-vpn-version':
                'global_protect_clientless_vpn_version',
            'logdb-version': 'logdb_version',
            'plugin_versions': 'plugin_versions',
            'platform-family': 'platform_family',
            'high-speed-log-forwarding-mode': 'high_speed_log_forwarding_mode',
            'vpn-disable-mode': 'vpn_disable_mode',
            'multi-vsys': 'multi_vsys',
            'operational-mode': 'operational_mode',
            'device-certificate-status': 'device_certificate_status',
            'vm-uuid': 'vm_uuid',
            'vm-cpuid': 'vm_cpuid',
            'vm-license': 'vm_license',
            'vm-cap-tier': 'vm_cap_tier',
            'vm-cores': 'vm_cores',
            'vm-mem': 'vm_mem',
            'relicense': 'relicense',
            'vm-mode': 'vm_mode',
            'global-protect-clientless-vpn-release-date':
                'global_protect_clientless_vpn_release_date'
        }
    }


def seconds_to_ios_format(seconds: int) -> Union[str, None]:
    """
    Convert a duration in seconds to an IOS-like BGP timer format.

    Parameters
    ----------
    seconds : int
        Duration in seconds.

    Returns
    -------
    Union[str, None]
        Formatted duration in the format 'up for XwXdXh' or None if the input
        is 0.
    """
    seconds = int(seconds)

    if seconds == 0:
        return None

    weeks, remainder = divmod(int(seconds),
                              7 * 24 * 60 * 60)
    days, remainder = divmod(remainder, 24 * 60 * 60)
    hours, _ = divmod(remainder, 60 * 60)

    if weeks and days and not hours:
        return f"up for {weeks}w{days}d"
    elif weeks and not days and not hours:
        return f"up for {weeks}w"
    elif not weeks and days and hours:
        return f"up for {days}d{hours}h"
    elif not weeks and days and not hours:
        return f"up for {days}d"
    else:
        return f"up for {weeks}w{days}d{hours}h"


def set_column_order(table_name: str) -> List:
    """
    Defines the desired column order for DataFrames.

    Parameters
    ----------
    table_name : str
        The table name that was used to create the DataFrame.

    Returns
    -------
    col_order : list
        A list containing the column order. If the columns do not need to be
        changed, then an empty list will be returned.
    """
    col_order = list()
    if table_name == 'PANOS_BGP_NEIGHBORS':
        col_order = ['device',
                     'neighbor',
                     'vrf',
                     'peer_group',
                     'neighbor_id',
                     'remote_as',
                     'status',
                     'status-duration',
                     'password_set',
                     'passive',
                     'multi_hop_ttl',
                     'remote_address',
                     'remote_address_port',
                     'local_address',
                     'local_address_port',
                     'reflector_client',
                     'same_confederation',
                     'aggregate_confed_as',
                     'peering_type',
                     'connect_retry_interval',
                     'open_delay',
                     'idle_hold',
                     'prefix_limit',
                     'holdtime',
                     'holdtime_config',
                     'keepalive',
                     'keepalive_config',
                     'msg_update_in',
                     'msg_update_out',
                     'msg_total_in',
                     'msg_total_out',
                     'last_update_age',
                     'last_error',
                     'status_flap_counts',
                     'established_counts',
                     'orf_entry_received',
                     'nexthop_self',
                     'nexthop_thirdparty',
                     'nexthop_peer',
                     'config',
                     'peer_capability',
                     'prefix_counter']
    return col_order


def split_domain(device_name: str) -> Tuple[str, str]:
    """
    Split the device name into device and domain.

    Parameters
    ----------
    device_name : str
        The input device name.

    Returns
    -------
    Tuple[str, str]
        A tuple containing the main device name and the domain.
    """
    parts = device_name.split('.')
    return parts[0], '.'.join(parts[1:])


def split_ip_port(address: str) -> Tuple[str, Union[str, None]]:
    """
    Split the given address into IP and port.

    Parameters
    ----------
    address : str
        The input address, which can be either an IP address or an IP:port
        combination.

    Returns
    -------
    Tuple[str, Union[str, None]]
        A tuple containing the IP address and the port (if present).
    """
    match = re.search(r'(?P<ip>.*):(?P<port>\d+)$', address)
    if match:
        return match.group("ip"), match.group("port")
    return address, None


def standardize_timestamp(timestamp: str) -> str:
    """
    Convert timestamp format from 'YYYY-MM-DD_HHMM' to 'YYYY-MM-DD HH:MM:SS'.

    Parameters
    ----------
    timestamp : str
        The input timestamp in the format 'YYYY-MM-DD_HHMM'.

    Returns
    -------
    str
        The standardized timestamp in the format 'YYYY-MM-DD HH:MM:SS'.
    """
    date_part, time_part = timestamp.split('_')
    formatted_time = f"{time_part[:2]}:{time_part[2:]}:00"
    return f"{date_part} {formatted_time}"


def transform_dataframe(df: pd.DataFrame,
                        table_name: str,
                        schema: Dict[str,
                                     Dict[str, Union[str, Dict[str, Any]]]],
                        function_mapping: Dict[str, Callable]) -> pd.DataFrame:
    """
    Transform an entire DataFrame based on the provided mapping schema.

    Parameters
    ----------
    df : pd.DataFrame
        The input DataFrame to be transformed.
    table_name : str
        The table name as defined in the mapping_schema.
    schema : Dict[str, Dict[str, Union[str, Dict[str, Any]]]]
        The mapping schema to be used for transformation.
    function_mapping : Dict[str, Callable]
        Dictionary mapping function names in the schema to actual functions.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the transformed data.
    """
    # Apply the row transformation to every row in the DataFrame
    transformed_data = df.apply(lambda row: transform_row(table_name,
                                                          row,
                                                          schema,
                                                          function_mapping),
                                axis=1)

    # Convert the Series of dictionaries to a DataFrame
    transformed_df = pd.DataFrame(list(transformed_data))

    # Reorder the columns based on the desired order
    desired_order = set_column_order(table_name)
    if desired_order:
        present_columns = [col for col in desired_order if col in
                           transformed_df.columns]
        transformed_df = transformed_df[present_columns]

    return transformed_df


def transform_dataframe_row(row: pd.Series,
                            table_name: str,
                            schema: Dict[str, Dict[str,
                                                   Union[str,
                                                         Dict[str, Any]]]],
                            function_mapping: Dict[str, Callable]) \
        -> pd.Series:
    """
    Transform a row of DataFrame based on the mapping schema provided.

    Parameters
    ----------
    row : pd.Series
        A row from a DataFrame to be transformed.
    table_name : str
        The table name as defined in the mapping_schema.
    schema : dict
        The mapping schema to be used for transformation.
    function_mapping : dict
        Dictionary mapping function names in the schema to actual functions.

    Returns
    -------
    pd.Series
        A series containing the transformed data.

    Example
    -------
    >>> df = pd.DataFrame({
    ...     'device': ['device_name'],
    ...     '@peer': ['1.2.3.4'],
    ...     '@vr': ['INTERNET'],
    ...     'peer-group': ['AS1234-RR'],
    ...     'timestamp': ['2023-09-05_1456']
    ... })
    >>> schema = get_mapping_schema()
    >>> func_mapping = get_function_mapping()
    >>> transformed_row = df.apply(transform_df_row,
                                   args=('PANOS_BGP_NEIGHBORS',
                                          schema,
                                          func_mapping),
                                   axis=1)
    >>> print(transformed_row.iloc[0]['device'])
    'device_name'
    """
    row_data = row.to_dict()
    return pd.Series(transform_row(table_name,
                                   row_data,
                                   schema,
                                   function_mapping))


def transform_row(table_name: str,
                  row_data: Dict[str, Any],
                  schema: Dict[str, Dict[str, Union[str, Dict[str, Any]]]],
                  function_mapping: Dict[str, Callable]) -> Dict[str, Any]:
    """
    Transform a single row of data based on the mapping schema provided.

    Parameters
    ----------
    table_name : str
        The table name as defined in the mapping_schema.
    row_data : Dict[str, Any]
        A dictionary representing a row of data.
    schema : Dict[str, Dict[str, Union[str, Dict[str, Any]]]]
        The mapping schema to be used for transformation.
    function_mapping : Dict[str, Callable]
        Dictionary mapping function names in the schema to actual functions.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing the transformed data for the row.
    """
    transformed_data: Dict[str, Any] = {}

    for key, value in schema[table_name].items():
        if key not in row_data:
            continue

        # Handle IP:port columns
        if value in ["remote_address", "local_address"] \
                and ':' in str(row_data[key]):
            ip, port = split_ip_port(row_data[key])
            transformed_data[value] = ip
            if port:
                transformed_data[value + "_port"] = port
            continue  # Go to next key-value pair

        # Handle direct mapping
        if type(value) is str:
            transformed_data[value] = row_data[key]

        # Handle function transformation
        elif 'function' in value:
            function_name = value['function']['name']
            if function_name in function_mapping:
                transformed_data[key] = \
                    function_mapping[function_name](row_data[key])

        # Handle domain split
        elif 'split' in value:
            main, sub = split_domain(row_data[key])
            transformed_data[value['split'][0]] = main
            transformed_data[value['split'][1]] = sub

    return transformed_data
