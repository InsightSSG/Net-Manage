#!/usr/bin/env python3

import asyncio
import datetime as dt
import os
import sys
import time
from dotenv import load_dotenv
from typing import Union

# Load environment variables
load_dotenv()
netmanage_path = os.path.expanduser(os.environ['netmanage_path'].strip('/'))
os.chdir(f'{netmanage_path}/test')
sys.path.append('..')
import netmanage.run_collectors as rc  # noqa
from netmanage.collectors import meraki_collectors as mc  # noqa


def test_get_network_clients(api_key,
                             networks: list = [],
                             macs: list = [],
                             orgs: list = [],
                             db_path: str = '',
                             per_page: int = 1000,
                             timespan: int = 86400,
                             total_pages: Union[int, str] = 'all'):
    try:
        while True:
            start_time = time.time()  # record start time

            timestamp = dt.datetime.now()
            timestamp = timestamp.strftime('%Y-%m-%d_%H%M')
            df_clients = asyncio.run(
                mc.meraki_get_network_clients(api_key,
                                              networks=networks,
                                              macs=macs,
                                              orgs=orgs,
                                              per_page=per_page,
                                              timespan=timespan,
                                              total_pages=total_pages))
            expected_cols = [
                'id', 'mac', 'description', 'ip', 'ip6', 'ip6Local', 'user',
                'firstSeen', 'lastSeen', 'manufacturer', 'os',
                'deviceTypePrediction', 'recentDeviceSerial',
                'recentDeviceName', 'recentDeviceMac',
                'recentDeviceConnection', 'ssid', 'vlan', 'switchport',
                'usage', 'status', 'notes', 'groupPolicy8021x',
                'adaptivePolicyGroup', 'smInstalled', 'pskGroup'
            ]
            assert expected_cols == df_clients.columns.to_list()
            print(len(df_clients))

            rc.add_to_db('MERAKI_NETWORK_CLIENTS',
                         df_clients,
                         timestamp,
                         db_path,
                         method='append')

            elapsed_time = time.time() - start_time  # calculate elapsed time

            print('sleeping...')
            # Wait for the remaining time of the 10 minutes.
            time.sleep(max(900 - elapsed_time, 0))

    except KeyboardInterrupt:
        pass


def test_get_appliance_ports(api_key):
    df = asyncio.run(mc.meraki_get_appliance_ports(api_key))

    expected_cols = [
        'device', 'number', 'enabled', 'type', 'dropUntaggedTraffic',
        'allowedVlans', 'vlan', 'accessPolicy'
    ]

    assert expected_cols == df.columns.to_list()


def test_get_switch_ports(api_key):
    df = asyncio.run(mc.meraki_get_switch_ports(api_key))

    expected_cols = [
        "device", "portId", "name", "tags", "enabled", "poeEnabled", "type",
        "vlan", "voiceVlan", "allowedVlans", "rstpEnabled", "stpGuard",
        "linkNegotiation", "accessPolicyType"
    ]

    assert expected_cols == df.columns.to_list()


def main():
    # Load environment variables.
    meraki_api_key = os.environ['meraki_api_key']
    meraki_networks = list(
        filter(None, os.environ['meraki_networks'].split(',')))
    meraki_organizations = list(
        filter(None, os.environ['meraki_organizations'].split(',')))
    meraki_macs = os.environ['meraki_macs']
    meraki_lookback = os.environ['meraki_lookback_timespan']
    meraki_per_page = os.environ['meraki_per_page']
    try:
        meraki_tp = int(os.environ['meraki_total_pages'])
    except ValueError:
        meraki_tp = -1

    database_name = os.environ['database_name']
    database_path = os.path.expanduser(os.environ['database_path'])
    database_full_path = f'{database_path}/{database_name}'

    # Execute tests
    test_get_network_clients(meraki_api_key,
                             networks=meraki_networks,
                             macs=meraki_macs,
                             orgs=meraki_organizations,
                             db_path=database_full_path,
                             per_page=meraki_per_page,
                             timespan=meraki_lookback,
                             total_pages=meraki_tp)

    test_get_switch_ports(meraki_api_key)

    test_get_appliance_ports(meraki_api_key)


if __name__ == '__main__':
    main()
