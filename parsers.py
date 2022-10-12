#!/usr/bin/env python3

'''
A library of functions for parsing network device command output.
'''

import pandas as pd
import re
from tabulate import tabulate

def main():
    output = '''VRF-Name: PEER, VRF-ID: 3, State: Up
    Description:
        VPC KEEP-ALIVE
    VPNID: unknown
    RD: 0:0
    Max Routes: 0  Mid-Threshold: 0
    Table-ID: 0x80000003, AF: IPv6, Fwd-ID: 0x80000003, State: Up
    Table-ID: 0x00000003, AF: IPv4, Fwd-ID: 0x00000003, State: Up

VRF-Name: Peer-keepalive, VRF-ID: 4, State: Up
    Description:
        VRF for VPC Peer-Keepalive
    VPNID: unknown
    RD: 0:0
    Max Routes: 0  Mid-Threshold: 0
    Table-ID: 0x80000004, AF: IPv6, Fwd-ID: 0x80000004, State: Up
    Table-ID: 0x00000004, AF: IPv4, Fwd-ID: 0x00000004, State: Up

VRF-Name: default, VRF-ID: 1, State: Up
    VPNID: unknown
    RD: 0:0
    Max Routes: 0  Mid-Threshold: 0
    Table-ID: 0x80000001, AF: IPv6, Fwd-ID: 0x80000001, State: Up
    Table-ID: 0x00000001, AF: IPv4, Fwd-ID: 0x00000001, State: Up

VRF-Name: management, VRF-ID: 2, State: Up
    VPNID: unknown
    RD: 0:0
    Max Routes: 0  Mid-Threshold: 0
    Table-ID: 0x80000002, AF: IPv6, Fwd-ID: 0x80000002, State: Up
    Table-ID: 0x00000002, AF: IPv4, Fwd-ID: 0x00000002, State: Up

VRF-Name: managment, VRF-ID: 5, State: Up
    VPNID: unknown
    RD: 0:0
    Max Routes: 0  Mid-Threshold: 0
    Table-ID: 0x80000005, AF: IPv6, Fwd-ID: 0x80000005, State: Up
    Table-ID: 0x00000005, AF: IPv4, Fwd-ID: 0x00000005, State: Up'''

    cols = ['device', #all
            'name', #all
            'description', # nxos
            'vrf_id', # ios / ios-xe
            'state', # nxos
            'route_domain', # nxos
            'default_rd', # ios / ios-xe
            'protocols', # ios / ios-xe
            'interfaces' # ios / ios-xe
            ]

    df_data = dict()
    for c in cols:
        df_data[c] = list()

    for item in output.split('\n\n'):
        device = 'abc'

        data = dict()
        for c in cols:
            data[c] = str()    
        
        line = re.findall(r'VRF-Name.*', item)[0]
        line = [l.split(': ')[-1] for l in line.split(', ')]
        name, vrf_id, state = line[0], line[1], line[2]

        data['device'] = device
        data['name'] = name
        data['state'] = state
        data['vrf_id'] = vrf_id

        _ = re.findall(r'Description:\n.*', item)
        desc = _[0].split('\n')[-1].strip() if _ else str()
        data['description'] = desc

        rd = re.findall(r'RD: .*:.*', item)[0].split()[-1]
        data['route_domain'] = rd

        for key, value in data.items():
            df_data[key].append(value)


    df_vrfs = pd.DataFrame.from_dict(df_data)

    print(tabulate(df_vrfs,
                   headers='keys',
                   tablefmt='psql',
                   showindex=False))


if __name__ == '__main__':
    main()