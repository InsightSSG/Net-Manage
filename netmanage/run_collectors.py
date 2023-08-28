#!/usr/bin/env python3

'''
Define collectors and map them to the correct function in colletors.py.
'''

import argparse
import ast
import asyncio
import datetime as dt
import os
import pandas as pd
import readline
from netmanage.collectors import cisco_asa_collectors as cac
from netmanage.collectors import cisco_ios_collectors as cic
from netmanage.collectors import cisco_nxos_collectors as cnc
from netmanage.collectors import dnac_collectors as dnc
from netmanage.collectors import f5_collectors as f5c
from netmanage.collectors import infoblox_nios_collectors as nc
from netmanage.collectors import meraki_collectors as mc
from netmanage.collectors import netbox_collectors as nbc
from netmanage.collectors import palo_alto_collectors as pac
from netmanage.collectors import solarwinds_collectors as swc
from dotenv import load_dotenv
from netmanage.helpers import helpers as hp
from typing import List

# Load environment variables.
load_dotenv()

# Protect creds by not writing history to .python_history.
readline.write_history_file = lambda *args: None


def collect(ansible_os: str,
            collector: str,
            hostgroup: str,
            timestamp: str) -> pd.DataFrame:
    '''
    This function calls the test that the user requested.

    Parameters
    ----------
    ansible_os : str
        The Ansible OS of the hostgroup.
    collector : str
        The name of the collector that the user requested.
    hostgroup : str
        The name of the Ansible hostgroup.
    timestamp : str
        The timestamp is YYYY-MM-DD_hhmm format.

    Returns
    -------
    result : pd.DataFrame
        A DataFrame containing the data from the collector.
    '''
    # Read global variables
    database_name = os.environ['database_name']
    database_path = os.path.expanduser(os.environ['database_path'])
    netmanage_path = os.path.expanduser(
        os.environ['netmanage_path'].strip('/'))
    private_data_dir = os.path.expanduser(
        os.environ['private_data_directory'])
    validate_certs = ast.literal_eval(os.environ['validate_certs'])
    database_method = os.environ['database_method']

    # Read Cisco ASA variables
    asa_devices_username = os.environ['asa_devices_username']
    asa_devices_password = os.environ['asa_devices_password']

    # Read Cisco DNAC variables
    dnac_url = os.environ['dnac_url']
    dnac_username = os.environ['dnac_username']
    dnac_password = os.environ['dnac_password']
    dnac_platform_ids = list(
        filter(None, os.environ['dnac_platform_ids'].split(',')))

    # Read Cisco IOS variables
    ios_devices_username = os.environ['ios_devices_username']
    ios_devices_password = os.environ['ios_devices_password']

    # Read Cisco NXOS variables
    nxos_devices_username = os.environ['nxos_devices_username']
    nxos_devices_password = os.environ['nxos_devices_password']

    # Read F5 LTM variables
    f5_ltm_username = os.environ['f5_ltm_username']
    f5_ltm_password = os.environ['f5_ltm_password']
    # f5_log_range = os.environ['f5_log_range']
    # f5_log_type = os.environ['f5_log_type']
    # f5_num_lines = os.environ['f5_num_lines']

    # Read Infoblox variables
    infoblox_url = os.environ['infoblox_url']
    infoblox_username = os.environ['infoblox_username']
    infoblox_password = os.environ['infoblox_password']
    infoblox_paging = os.environ['infoblox_paging']

    # Read Meraki variables
    meraki_api_key = os.environ['meraki_api_key']
    meraki_networks = list(filter(
        None, os.environ['meraki_networks'].split(',')))
    meraki_organizations = list(filter(
        None, os.environ['meraki_organizations'].split(',')))
    meraki_macs = os.environ['meraki_macs']
    meraki_lookback = os.environ['meraki_lookback_timespan']
    meraki_per_page = os.environ['meraki_per_page']
    meraki_serials = list(filter(
        None, os.environ['meraki_serials'].split(',')))
    meraki_serials = [_.strip() for _ in meraki_serials]
    try:
        meraki_tp = int(os.environ['meraki_total_pages'])
    except ValueError:
        meraki_tp = -1

    # Read Netbox variables
    netbox_url = os.environ['netbox_url']
    netbox_token = os.environ['netbox_token']

    # Read Palo Alto variables
    palo_alto_username = os.environ['palo_alto_username']
    palo_alto_password = os.environ['palo_alto_password']

    # Read Solarwinds NPM variables
    npm_server = os.environ['solarwinds_npm_server']
    npm_username = os.environ['solarwinds_npm_username']
    npm_password = os.environ['solarwinds_npm_password']
    npm_group_name = os.environ['solarwinds_npm_group_name']

    # Create the output folder if it does not already exist.
    exists = hp.check_dir_existence(database_path)
    if not exists:
        hp.create_dir(database_path)

    # Define additional variables
    database_full_path = f'{database_path}/{database_name}'
    idx_cols = list()
    play_path = netmanage_path + '/playbooks'

    # Create an empty DataFrame for when collectors return no results.
    result = pd.DataFrame()

    # Call collector and return results.
    if ansible_os == 'bigip':
        if collector == 'arp_table':
            result = f5c.get_arp_table(f5_ltm_username,
                                       f5_ltm_password,
                                       hostgroup,
                                       netmanage_path,
                                       play_path,
                                       private_data_dir,
                                       validate_certs=validate_certs)

        if collector == 'interface_description':
            result = f5c.\
                get_interface_descriptions(f5_ltm_username,
                                           f5_ltm_password,
                                           hostgroup,
                                           netmanage_path,
                                           play_path,
                                           private_data_dir,
                                           reverse_dns=False,
                                           validate_certs=validate_certs)

        if collector == 'interface_summary':
            result = f5c.get_interface_status(f5_ltm_username,
                                              f5_ltm_password,
                                              hostgroup,
                                              play_path,
                                              private_data_dir,
                                              validate_certs=validate_certs)

        # Do not uncomment the 'logs' collector until it is updated to use
        # bash. This is because of a suspected F5 bug that causes the active
        # unit to sometimes hang when retrieving the logs with a tmsh command
        # (Ansible) or a REST API call.

        # if collector == 'logs':
        #     result = f5c.get_log_files(f5_ltm_username,
        #                                f5_ltm_password,
        #                                hostgroup,
        #                                play_path,
        #                                private_data_dir,
        #                                log_type=f5_log_type,
        #                                log_range=f5_log_range,
        #                                num_lines=f5_num_lines,
        #                                validate_certs=validate_certs)

        if collector == 'node_availability':
            result = f5c.get_node_availability(f5_ltm_username,
                                               f5_ltm_password,
                                               hostgroup,
                                               play_path,
                                               private_data_dir,
                                               validate_certs=validate_certs)

        if collector == 'pool_availability':
            result = f5c.get_pool_availability(f5_ltm_username,
                                               f5_ltm_password,
                                               hostgroup,
                                               play_path,
                                               private_data_dir,
                                               validate_certs=validate_certs)

        if collector == 'pool_summary':
            result = f5c.get_pool_data(f5_ltm_username,
                                       f5_ltm_password,
                                       hostgroup,
                                       play_path,
                                       private_data_dir,
                                       validate_certs=validate_certs)

        if collector == 'pool_member_availability':
            result = f5c.\
                get_pool_member_availability(f5_ltm_username,
                                             f5_ltm_password,
                                             hostgroup,
                                             play_path,
                                             private_data_dir,
                                             validate_certs=validate_certs)

        if collector == 'self_ips':
            result = f5c.get_self_ips(f5_ltm_username,
                                      f5_ltm_password,
                                      hostgroup,
                                      play_path,
                                      private_data_dir,
                                      validate_certs=validate_certs)

        if collector == 'vip_availability':
            result = f5c.get_vip_availability(f5_ltm_username,
                                              f5_ltm_password,
                                              hostgroup,
                                              play_path,
                                              private_data_dir,
                                              validate_certs=validate_certs)

        if collector == 'vip_destinations':
            result = f5c.get_vip_destinations(database_full_path)

        if collector == 'vlans':
            result = f5c.get_vlans(f5_ltm_username,
                                   f5_ltm_password,
                                   hostgroup,
                                   play_path,
                                   private_data_dir,
                                   validate_certs=validate_certs)

        if collector == 'vlan_database':
            result = f5c.f5_get_vlan_db(f5_ltm_username,
                                        f5_ltm_password,
                                        hostgroup,
                                        play_path,
                                        private_data_dir,
                                        validate_certs=validate_certs)

    if collector == 'bgp_neighbors_summary':
        if ansible_os == 'cisco.ios.ios':
            result = cic.bgp_neighbor_summary(ios_devices_username,
                                              ios_devices_password,
                                              hostgroup,
                                              play_path,
                                              private_data_dir)

    if collector == 'devices_inventory':
        if ansible_os == 'cisco.dnac':
            result = dnc.devices_inventory(dnac_url,
                                           dnac_username,
                                           dnac_password,
                                           platform_ids=dnac_platform_ids,
                                           verify=validate_certs)

    if collector == 'device_cdp_lldp_neighbors':
        if ansible_os == 'meraki':
            result = asyncio.run(
                mc.meraki_get_device_cdp_lldp_neighbors(meraki_api_key,
                                                        database_full_path,
                                                        meraki_serials))

    if collector == 'devices_modules':
        if ansible_os == 'cisco.dnac':
            result = dnc.devices_modules(dnac_url,
                                         dnac_username,
                                         dnac_password,
                                         platform_ids=dnac_platform_ids,
                                         verify=validate_certs)

    if collector == 'cam_table':
        if ansible_os == 'cisco.ios.ios':
            result = cic.ios_get_cam_table(ios_devices_username,
                                           ios_devices_password,
                                           hostgroup,
                                           netmanage_path,
                                           play_path,
                                           private_data_dir)

        if ansible_os == 'cisco.nxos.nxos':
            result = cnc.nxos_get_cam_table(nxos_devices_username,
                                            nxos_devices_password,
                                            hostgroup,
                                            netmanage_path,
                                            play_path,
                                            private_data_dir)

    if collector == 'config':
        if ansible_os == 'cisco.ios.ios':
            result = cic.get_config(ios_devices_username,
                                    ios_devices_password,
                                    hostgroup,
                                    play_path,
                                    private_data_dir)

    if collector == 'arp_table':
        if ansible_os == 'cisco.ios.ios':
            result = cic.ios_get_arp_table(ios_devices_username,
                                           ios_devices_password,
                                           hostgroup,
                                           netmanage_path,
                                           play_path,
                                           private_data_dir)

        if ansible_os == 'cisco.nxos.nxos':
            result = cnc.nxos_get_arp_table(nxos_devices_username,
                                            nxos_devices_password,
                                            hostgroup,
                                            netmanage_path,
                                            play_path,
                                            private_data_dir)

        if ansible_os == 'paloaltonetworks.panos':
            result = pac.get_arp_table(palo_alto_username,
                                       palo_alto_password,
                                       hostgroup,
                                       netmanage_path,
                                       private_data_dir)

    if collector == 'bgp_neighbors':
        if ansible_os == 'cisco.nxos.nxos':
            result = cnc.nxos_get_bgp_neighbors(nxos_devices_username,
                                                nxos_devices_password,
                                                hostgroup,
                                                netmanage_path,
                                                play_path,
                                                private_data_dir)

    if collector == 'interface_description':
        if ansible_os == 'cisco.ios.ios':
            result = cic.ios_get_interface_descriptions(ios_devices_username,
                                                        ios_devices_password,
                                                        hostgroup,
                                                        play_path,
                                                        private_data_dir)

        if ansible_os == 'cisco.nxos.nxos':
            result = cnc.nxos_get_interface_descriptions(nxos_devices_username,
                                                         nxos_devices_password,
                                                         hostgroup,
                                                         play_path,
                                                         private_data_dir)

    if collector == 'infoblox_get_network_containers':
        result = nc.get_network_containers(infoblox_url,
                                           infoblox_username,
                                           infoblox_password,
                                           infoblox_paging,
                                           validate_certs=validate_certs)

    if collector == 'infoblox_get_networks':
        result = nc.get_networks(infoblox_url,
                                 infoblox_username,
                                 infoblox_password,
                                 infoblox_paging,
                                 validate_certs=validate_certs)

    if collector == 'infoblox_get_network_containers':
        result = nc.get_network_containers(infoblox_url,
                                           infoblox_username,
                                           infoblox_password,
                                           infoblox_paging,
                                           validate_certs=validate_certs)

    if collector == 'infoblox_get_networks_parent_containers':
        result = nc.get_networks_parent_containers(database_full_path)

    if collector == 'infoblox_get_vlan_ranges':
        result = nc.get_vlan_ranges(infoblox_url,
                                    infoblox_username,
                                    infoblox_password,
                                    infoblox_paging,
                                    validate_certs=validate_certs)

    if collector == 'infoblox_get_vlans':
        result = nc.get_vlans(infoblox_url,
                              infoblox_username,
                              infoblox_password,
                              infoblox_paging,
                              validate_certs=validate_certs)

    if collector == 'interface_ip_addresses':
        if ansible_os == 'cisco.asa.asa':
            result = cac.get_interface_ips(asa_devices_username,
                                           asa_devices_password,
                                           hostgroup,
                                           play_path,
                                           private_data_dir)

        if ansible_os == 'cisco.ios.ios':
            result = cic.ios_get_interface_ips(ios_devices_username,
                                               ios_devices_password,
                                               hostgroup,
                                               play_path,
                                               private_data_dir)

        if ansible_os == 'cisco.nxos.nxos':
            result = cnc.nxos_get_interface_ips(nxos_devices_username,
                                                nxos_devices_password,
                                                hostgroup,
                                                play_path,
                                                private_data_dir)

        if ansible_os == 'paloaltonetworks.panos':
            result = pac.get_interface_ips(palo_alto_username,
                                           palo_alto_password,
                                           hostgroup,
                                           netmanage_path,
                                           private_data_dir)

    if collector == 'interface_status':
        if ansible_os == 'cisco.nxos.nxos':
            result = cnc.nxos_get_interface_status(nxos_devices_username,
                                                   nxos_devices_password,
                                                   hostgroup,
                                                   play_path,
                                                   private_data_dir)

    if collector == 'interface_summary':
        if ansible_os == 'cisco.nxos.nxos':
            result = cnc.nxos_get_interface_summary(database_full_path)

    if collector == 'find_uplink_by_ip':
        if ansible_os == 'cisco.ios.ios':
            result = cic.ios_find_uplink_by_ip(ios_devices_username,
                                               ios_devices_password,
                                               hostgroup,
                                               play_path,
                                               private_data_dir)

    if collector == 'inventory_nxos':
        result = cnc.nxos_get_inventory(nxos_devices_username,
                                        nxos_devices_password,
                                        hostgroup,
                                        play_path,
                                        private_data_dir)

    if collector == 'network_appliance_vlans':
        if ansible_os == 'meraki':
            mc.get_network_appliance_vlans(ansible_os,
                                           meraki_api_key,
                                           collector,
                                           database_full_path,
                                           timestamp,
                                           networks=meraki_networks,
                                           orgs=meraki_organizations)

    if collector == 'network_clients':
        if ansible_os == 'meraki':
            result = asyncio.run(
                mc.meraki_get_network_clients(meraki_api_key,
                                              networks=meraki_networks,
                                              macs=meraki_macs,
                                              orgs=meraki_organizations,
                                              per_page=meraki_per_page,
                                              timespan=meraki_lookback,
                                              total_pages=meraki_tp))

    if collector == 'network_devices':
        if ansible_os == 'meraki':
            result = mc.meraki_get_network_devices(meraki_api_key,
                                                   database_full_path,
                                                   networks=meraki_networks,
                                                   orgs=meraki_organizations)

    if collector == 'network_device_statuses':
        if ansible_os == 'meraki':
            result = mc.meraki_get_network_device_statuses(
                database_full_path, meraki_networks)

    if collector == 'organizations':
        if ansible_os == 'meraki':
            result = mc.meraki_get_organizations(meraki_api_key)

    if collector == 'org_devices':
        if ansible_os == 'meraki':
            result = mc.meraki_get_org_devices(meraki_api_key,
                                               database_full_path,
                                               orgs=meraki_organizations)

    if collector == 'org_device_statuses':
        if ansible_os == 'meraki':
            result, idx_cols = mc.meraki_get_org_device_statuses(
                meraki_api_key,
                database_full_path,
                orgs=meraki_organizations,
                total_pages=meraki_tp
            )

    if collector == 'org_networks':
        if ansible_os == 'meraki':
            result = mc.meraki_get_org_networks(meraki_api_key,
                                                database_full_path,
                                                orgs=meraki_organizations,
                                                use_db=True)

    if collector == 'ospf_neighbors':
        if ansible_os == 'cisco.ios.ios':
            result = cic.ospf_neighbors(ios_devices_username,
                                        ios_devices_password,
                                        hostgroup,
                                        play_path,
                                        private_data_dir)

    if collector == 'switch_lldp_neighbors':
        if ansible_os == 'meraki':
            result = mc.meraki_get_switch_lldp_neighbors(database_full_path)

    if collector == 'switch_port_statuses':
        if ansible_os == 'meraki':
            result = mc.meraki_get_switch_port_statuses(meraki_api_key,
                                                        database_full_path,
                                                        meraki_networks)

    if collector == 'switch_port_usages':
        if ansible_os == 'meraki':
            result = mc.meraki_get_switch_port_usages(meraki_api_key,
                                                      database_full_path,
                                                      meraki_networks,
                                                      timestamp)

    if collector == 'security_rules':
        if ansible_os == 'paloaltonetworks.panos':
            result = pac.get_security_rules(palo_alto_username,
                                            palo_alto_password,
                                            hostgroup,
                                            play_path,
                                            private_data_dir)

    if collector == 'netbox_get_ipam_prefixes':
        result = nbc.netbox_get_ipam_prefixes(netbox_url, netbox_token)

    if collector == 'ncm_serial_numbers':
        result = swc.get_ncm_serial_numbers(npm_server,
                                            npm_username,
                                            npm_password)

    if collector == 'npm_containers':
        result = swc.get_npm_containers(npm_server, npm_username, npm_password)

    if collector == 'npm_group_members':
        result = swc.get_npm_group_members(npm_server,
                                           npm_username,
                                           npm_password,
                                           npm_group_name)

    if collector == 'npm_group_names':
        result = swc.get_npm_group_names(npm_server,
                                         npm_username,
                                         npm_password)

    if collector == 'npm_node_ids':
        result = swc.get_npm_node_ids(npm_server, npm_username, npm_password)

    if collector == 'npm_node_ips':
        result = swc.get_npm_node_ips(npm_server, npm_username, npm_password)

    if collector == 'npm_node_machine_types':
        result = swc.get_npm_node_machine_types(npm_server,
                                                npm_username,
                                                npm_password)

    if collector == 'npm_node_os_versions':
        result = swc.get_npm_node_os_versions(npm_server,
                                              npm_username,
                                              npm_password)

    if collector == 'npm_node_vendors':
        result = swc.get_npm_node_vendors(npm_server,
                                          npm_username,
                                          npm_password)

    if collector == 'npm_nodes':
        result = swc.get_npm_nodes(npm_server, npm_username, npm_password)

    if collector == 'all_interfaces':
        if ansible_os == 'paloaltonetworks.panos':
            result = pac.get_all_interfaces(palo_alto_username,
                                            palo_alto_password,
                                            hostgroup,
                                            netmanage_path,
                                            private_data_dir)

    if collector == 'logical_interfaces':
        if ansible_os == 'paloaltonetworks.panos':
            result = pac.get_logical_interfaces(palo_alto_username,
                                                palo_alto_password,
                                                hostgroup,
                                                netmanage_path,
                                                private_data_dir)

    if collector == 'physical_interfaces':
        if ansible_os == 'paloaltonetworks.panos':
            result = pac.get_physical_interfaces(palo_alto_username,
                                                 palo_alto_password,
                                                 hostgroup,
                                                 netmanage_path,
                                                 private_data_dir)

    if collector == 'port_channel_data':
        if ansible_os == 'cisco.nxos.nxos':
            result = cnc.nxos_get_port_channel_data(nxos_devices_username,
                                                    nxos_devices_password,
                                                    hostgroup,
                                                    play_path,
                                                    private_data_dir)

    if collector == 'vpc_state':
        if ansible_os == 'cisco.nxos.nxos':
            result = cnc.nxos_get_vpc_state(nxos_devices_username,
                                            nxos_devices_password,
                                            hostgroup,
                                            play_path,
                                            private_data_dir)

    if collector == 'vlans':
        if ansible_os == 'cisco.ios.ios':
            result = cic.ios_get_vlan_db(ios_devices_username,
                                         ios_devices_password,
                                         hostgroup,
                                         play_path,
                                         private_data_dir)

        if ansible_os == 'cisco.nxos.nxos':
            result = cnc.nxos_get_vlan_db(nxos_devices_username,
                                          nxos_devices_password,
                                          hostgroup,
                                          play_path,
                                          private_data_dir)

    if collector == 'vrfs':
        if ansible_os == 'cisco.ios.ios':
            result = cic.get_vrfs(ios_devices_username,
                                  ios_devices_password,
                                  hostgroup,
                                  play_path,
                                  private_data_dir)

        if ansible_os == 'cisco.nxos.nxos':
            result = cnc.nxos_get_vrfs(nxos_devices_username,
                                       nxos_devices_password,
                                       hostgroup,
                                       play_path,
                                       private_data_dir)

    # Write the result to the database
    if len(result.columns.to_list()) > 0:
        table_name = f'{ansible_os.split(".")[-1]}_{collector}'
        add_to_db(table_name,
                  result,
                  timestamp,
                  database_full_path,
                  method=database_method,
                  idx_cols=idx_cols)

    return result


def add_to_db(table_name: str,
              result: pd.DataFrame,
              timestamp: str,
              database_path: str,
              method: str = 'append',
              idx_cols: List[str] = list()) -> None:
    '''
    Adds the output of a collector to the database.

    Parameters
    ----------
    table_name : str
        The name of the table in the database to which the data will be added.
    result : DataFrame
        The output of a collector as a Pandas DataFrame.
    timestamp : str
        The timestamp for the data in YYYY-MM-DD_hhmm format.
    database_path : str
        The path to the database where the data will be stored.
    method : str, optional
        What to do if the table already exists in the database. Options are
        'append', 'fail', 'replace'. Defaults to 'append'.
    idx_cols : List[str], optional
        The list of columns to use for indexing the table in the database.
        Note that this is NOT related to the dataframe index; it is for
        indexing the SQLite database table.

    Returns
    -------
    None
    '''
    # Set the timestamp as the index of the dataframe (this is unrelated to
    # the 'idx_cols' arg)
    new_idx = list()
    for i in range(0, len(result)):
        new_idx.append(timestamp)

    # Display the output to the console
    result['timestamp'] = new_idx
    result = result.set_index('timestamp')

    # Check if the output directory exists. If it does not, then create it.
    exists = hp.check_dir_existence('/'.join(database_path.split('/')[:-1]))
    if not exists:
        hp.create_dir('/'.join(database_path.split('/')[:-1]))

    # Connect to the database
    con = hp.connect_to_db(database_path)
    cur = con.cursor()

    # Get the table schema. This also checks if the table exists, because the
    # length of 'schema' will be 0 if it hasn't been created yet.
    schema = hp.sql_get_table_schema(database_path, table_name)

    # If the table doesn't exist, create it. (Pandas will automatically create
    # the table, but doing it manually allows us to create an auto-incrementing
    # ID column))
    column_list = result.columns.to_list()
    if 'table_id' in column_list:
        column_list.remove('table_id')
        del result['table_id']
    columns = [f'"{c}"' for c in column_list]
    if len(schema) == 0 and len(result) > 0:
        fields = ',\n'.join(columns)
        cur.execute(f'''CREATE TABLE {table_name.upper()} (
                    table_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp,
                    {fields}
                    )''')

    # Check if all of the columns in 'result' are in the table schema and add
    # them if they are not. This accounts for a common scenario that happens
    # when device output is inconsistent. For example, on Cisco NXOS devices
    # this command returns different rows if the device is using Layer 3 VPC.
    # 'show vpc brief | begin "vPC domain id" | end "vPC Peer-link status'
    # If the collector is run against devices using Layer 2 VPC, then run again
    # on devices using Layer 3 VPC, an additional column must be added or the
    # table insertion will fail.
    #
    # This scenario is very common, and it's not always possible to
    # future-proof collectors to account for it,
    if len(schema) >= 1:
        for col in column_list:
            if col not in schema['name'].to_list():
                cur.execute(f'ALTER TABLE {table_name} ADD COLUMN "{col}"')

    # from tabulate import tabulate
    # print(tabulate(result, headers='keys', tablefmt='psql'))

    # Add the dataframe to the database
    table = table_name.upper()
    result.to_sql(table, con, if_exists=method)

    # Create the SQL table index, if applicable
    if idx_cols:
        idx_name = f'idx_{table_name.lower()}'
        try:
            cur.execute(f'''CREATE INDEX {idx_name}
                            ON {table_name.upper()} ({','.join(idx_cols)})
                        ''')
        except Exception as e:
            print(f'Caught Exception: {str(e)}')

    con.commit()
    con.close()


def create_parser() -> argparse.Namespace:
    '''
    Create command line arguments.

    Args:
        None

    Returns:
        args:   Parsed command line arguments (argparse.Namespace)
    '''
    pass
    # Create the parser for command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database',
                        help='''The database name. Defaults to
                                YYYY-MM-DD.db.''',
                        default=f'{str(dt.datetime.now()).split()[0]}.db',
                        action='store'
                        )
    parser.add_argument('-o', '--out_dir',
                        help='''The directory to save output to (the filename
                                will be auto-generated). The database will also
                                be saved here.''',
                        default=os.path.expanduser('~/output'),
                        action='store'
                        )
    parser.add_argument('-u', '--username',
                        help='''The username for connecting to the devices. If
                                missing, script will prompt for it.''',
                        default=str(),
                        action='store'
                        )
    parser.add_argument('-P', '--password',
                        help='''The password for connecting to the devices.
                                This is included for external automation, but I
                                do not recommend using it when running the
                                script manually. If you do, then your password
                                could show up in the command history.''',
                        default=str(),
                        action='store'
                        )
    # requiredNamed = parser.add_argument_group('required named arguments')
    parser.add_argument('-c', '--collectors',
                        help='''A comma-delimited list of collectors to
                                run.''',
                        required=True,
                        action='store'
                        )
    parser.add_argument('-H', '--hostgroups',
                        help='A comma-delimited list of hostgroups',
                        default=str(),
                        action='store'
                        )
    parser.add_argument('-n', '--netmanage_path',
                        help='The path to the Net-Manage repository',
                        required=True,
                        action='store'
                        )
    parser.add_argument('-p', '--private_data_dir',
                        help='''The path to the Ansible private data
                                directory (I.e., the directory
                                containing the 'inventory' and 'env'
                                folders).''',
                        required=True,
                        action='store'
                        )
    args = parser.parse_args()
    return args


def arg_parser(args: argparse.Namespace) -> tuple:
    '''
    Extract system args and assign variable names.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command line arguments.

    Returns
    -------
    tuple
        A tuple containing:
        - collectors: List of collectors
        - db: Database path
        - hostgroups: List of hostgroups
        - netmanage_path: Path for netmanage
        - out_dir: Output directory path
        - username: Username for authentication
        - password: Password for authentication
        - private_data_dir: Private data directory path
    '''
    # Set the collectors
    collectors = [c.strip() for c in args.collectors.split(',')]

    # Set the hostgroups
    hostgroups = [h.strip() for h in args.hostgroups.split(',')]

    # Set the netmanage_path, out_dir and private_data_dir
    netmanage_path = os.path.expanduser(args.netmanage_path)
    out_dir = os.path.expanduser(args.out_dir)
    private_data_dir = os.path.expanduser(args.private_data_dir)

    # Set the user credentials
    # TODO: Add support for using different credentials for each device or
    #       hostgroup. That is a common scenario.
    if args.username:
        username = args.username
    else:
        username = hp.get_username()
    if args.password:
        password = args.password
    else:
        password = hp.get_password()

    # Set the database path
    db = f'{out_dir}/{args.database}'

    return (
        collectors,
        db,
        hostgroups,
        netmanage_path,
        out_dir,
        username,
        password,
        private_data_dir,
    )
