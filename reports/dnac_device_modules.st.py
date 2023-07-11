#!/usr/bin/env python3

'''
This report gets the modules for device in a Cisco DNAC inventory. It gets all
modules by default, but it can be filtered by a list of platform_ids--e.g.,
['C9407R', 'N9K-C93180YC-FX'].
'''

import os
import pandas as pd
import sys
from getpass import getpass


def main(args):
    # Parse command line arguments
    args_dict = parse_args(args)
    # Get the user's password
    password = getpass('Enter the password to authenticate with DNAC: ')

    # Switch to the Net-Manage directory.
    os.chdir(args_dict['nm_path'])

    # Import dnac_collectors
    sys.path.append('.')
    from collectors import dnac_collectors as dnc

    # Get the list of device modules.
    df = dnc.devices_modules(args_dict['url'],
                             args_dict['username'],
                             password,
                             args_dict['platform_ids'],
                             verify=args_dict['verify'])

    # Export the DataFrame to a CSV file.
    from helpers import report_helpers
    full_path = report_helpers.export_dataframe_to_csv(df,
                                                       args_dict['out_path'],
                                                       'dnac_device_modules')

    if args_dict['report'] == 'report1':
        df = report1(df)

    if args_dict['verbose']:
        print(f'Report saved to: {full_path}')


if __name__ == '__main__':
    main()
