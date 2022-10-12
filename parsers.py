#!/usr/bin/env python3

'''
A library of functions for parsing network device command output.
'''

import pandas as pd
from tabulate import tabulate

def main():
    cols = ['device', #all
            'name', #all
            'vrf_id', # nxos
            'state', # nxos
            'reason', # nxos
            'default_rd', # ios / ios-xe
            'protocols', # ios / ios-xe
            'interfaces' # ios / ios-xe
            ]
    
    df_data = list()

    nxos_output = '''VRF-Name                           VRF-ID State   Reason
AZURE                                   3 Up      --
CC                                      4 Up      --
DC                                      5 Up      --
MARS                                    6 Up      --
TDC                                     7 Up      --
TESTING                                 8 Up      --
USERS                                   9 Up      --
WAN                                    10 Up      --
WIFI                                   11 Up      --
default                                 1 Up      --
management                              2 Up      --
vpc_keepalive                          12 Up      --'''.split('\n')

    device = 'abc'
    for _ in nxos_output[1:]:
        _ = _.split()
        name = _[0]
        vrf_id = _[1]
        state = _[2]
        reason = _[3]
        default_rd = str()
        protocols = str()
        interfaces = str()

        row = [device,
               name,
               vrf_id,
               state,
               reason,
               default_rd,
               protocols,
               interfaces]
        df_data.append(row)



    ios_output = '''  Name                             Default RD          Protocols   Interfaces
  MGMT                             <not set>           ipv4        Gi0/0.227'''.split('\n')

    device = 'cde'
    for _ in ios_output[1:]:
        _ = _.split()
        name = _[0]
        vrf_id = str()
        state = str()
        reason = str()
        default_rd = _[1]
        protocols = _[2]
        interfaces = _[3]

        row = [device,
               name,
               vrf_id,
               state,
               reason,
               default_rd,
               protocols,
               interfaces]
        df_data.append(row)

    df_vrfs = pd.DataFrame(data=df_data, columns=cols)

    print(tabulate(df_vrfs,
                   headers='keys',
                   tablefmt='psql',
                   showindex=False))


if __name__ == '__main__':
    main()