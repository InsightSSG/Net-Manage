#!/usr/bin/env python3

'''
A library of functions for parsing network device command output.
'''


def f5_get_vip_data(line):
    '''
    Parses the command output for the 'f5_get_vip_data' collector.
    
    Example of VIP input and output:
    - 'ltm virtual /PARTITION_A/VIP_A' = 'PARTITION_A', 'VIP_A', None
    
    Example of Destination input and output:
    - 'destination 1.1.1.1:443': 'Common', '1.1.1.1', '443'
        

    Examples of Pool input and output:
    - 'pool /PARTITION_B/POOL_A': 'PARTITION_B', 'POOL_A', None
    - 'pool none': 'Common', 'none', None

    Args:
        line (str): One line of command output.

    Returns:
        item (str):        The VIP, destination or pool, without the partition
        partition (str):   The F5 partition that the VIP, destination and/or pool
                           are in.
        port (str):        The port for the destination. If the line does not
                           contain 'destination' then an emptry string is
                           returned.
    '''
    # Separate the partition from the item name
    if '/' in line:
        partition = line.split('/')[-2]
        item = line.split('/')[-1]
    else:
        partition = 'Common'
        item = line.split()[-1]

    # Set the port variable and modify 'item', if the line contains
    # 'destination'
    if 'destination' in line:
        port = item.split(':')[-1]
        item = item.split(':')[0]
    else:
        port = str()

    return partition, item, port