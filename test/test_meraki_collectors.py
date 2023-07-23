#!/usr/bin/env python3

import asyncio
import os
import sys
from dotenv import load_dotenv
from typing import Union

# Load environment variables
load_dotenv()
netmanage_path = os.path.expanduser(
    os.environ['netmanage_path'].strip('/'))
os.chdir(f'{netmanage_path}/test')
sys.path.append('..')
from collectors import meraki_collectors as mc  # noqa


def test_get_network_clients(api_key,
                             networks: list = [],
                             macs: list = [],
                             orgs: list = [],
                             per_page: int = 1000,
                             timespan: int = 86400,
                             total_pages: Union[int, str] = 'all'):
    try:
        df_clients = asyncio.run(
            mc.meraki_get_network_clients(api_key,
                                          networks=networks,
                                          macs=macs,
                                          orgs=orgs,
                                          per_page=per_page,
                                          timespan=timespan,
                                          total_pages=total_pages))
        expected_cols = ['id',
                         'mac',
                         'description',
                         'ip',
                         'ip6',
                         'ip6Local',
                         'user',
                         'firstSeen',
                         'lastSeen',
                         'manufacturer',
                         'os',
                         'deviceTypePrediction',
                         'recentDeviceSerial',
                         'recentDeviceName',
                         'recentDeviceMac',
                         'recentDeviceConnection',
                         'ssid',
                         'vlan',
                         'switchport',
                         'usage',
                         'status',
                         'notes',
                         'groupPolicy8021x',
                         'adaptivePolicyGroup',
                         'smInstalled',
                         'pskGroup']
        assert expected_cols == df_clients.columns.to_list()
        print(len(df_clients))
    except KeyboardInterrupt:
        pass


def main():
    # Load environment variables.
    meraki_api_key = os.environ['meraki_api_key']
    meraki_networks = list(filter(
        None, os.environ['meraki_networks'].split(',')))
    meraki_organizations = list(filter(
        None, os.environ['meraki_organizations'].split(',')))
    meraki_macs = os.environ['meraki_macs']
    meraki_lookback = os.environ['meraki_lookback_timespan']
    meraki_per_page = os.environ['meraki_per_page']
    try:
        meraki_tp = int(os.environ['meraki_total_pages'])
    except ValueError:
        meraki_tp = -1

    # Execute tests
    test_get_network_clients(meraki_api_key,
                             networks=meraki_networks,
                             macs=meraki_macs,
                             orgs=meraki_organizations,
                             per_page=meraki_per_page,
                             timespan=meraki_lookback,
                             total_pages=meraki_tp)


if __name__ == '__main__':
    main()
