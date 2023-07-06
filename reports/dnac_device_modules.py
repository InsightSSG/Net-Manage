#!/usr/bin/env python3

'''
This report gets the modules for device in a Cisco DNAC inventory. It gets all
modules by default, but it can be filtered by a list of platform_ids--e.g.,
['C9407R', 'N9K-C93180YC-FX'].
'''

import argparse
import os
import pandas as pd
import sys
from getpass import getpass

parser = argparse.ArgumentParser()
parser.add_argument('netmanage_path',
                    type=str,
                    help='Path to the Net-Manage folder.')
parser.add_argument('url',
                    type=str,
                    help='The URL of the DNAC server.')
parser.add_argument('username',
                    type=str,
                    help='The username for authenticating with DNAC.')
parser.add_argument('out_path',
                    type=str,
                    help='The directory to store the report in.')
parser.add_argument('-p', '--platform_ids',
                    type=str,
                    help='Comma-delimited string of platform IDs.')
parser.add_argument('-r', '--report',
                    type=str,
                    help='''The report name. If not specified, all columns are
                            returned.''')
parser.add_argument('--verbose',
                    action='store_true',
                    help='Whether to print verbose output.')
parser.add_argument('-v', '--verify',
                    action='store_true',
                    help='Whether to validate certs. Defaults to True.')
args = parser.parse_args()


def parse_args(args):
    '''
    Parses and validates the command line arguments.

    Args:
    ----
    args (argparse.Namespace):
        An object containing the command line arguments.

    Returns:
    ----
    args_dict (dict):
        A dictionary with the following keys:
        - nm_path : The path to the Net-Manage folder.
        - out_path : The path to store the report as a CSV file.
        - platform_ids : A list containing the platform IDs.
        - report : A string containing the report name.
        - url : The URL of the DNAC server.
        - username : The username for authenticating with DNAC.
        - verbose : Whether to print verbose output.
        - verify : Whether to verify certificates.
    '''
    # Check if the netmanage_path is valid
    if not os.path.isdir(args.netmanage_path):
        parser.error('The specified netmanage_path is not a valid folder.')

    # Retrieve the platform IDs
    if args.platform_ids:
        platform_ids = args.platform_ids.split(',')
    else:
        platform_ids = []

    args_dict = {'nm_path': args.netmanage_path,
                 'out_path': args.out_path,
                 'platform_ids': platform_ids,
                 'report': args.report,
                 'url': args.url,
                 'username': args.username,
                 'verbose': args.verbose,
                 'verify': args.verify}

    return args_dict


def report1(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Removes all but the following columns:
    - platformId
    - hostname
    - name
    - description
    - partNumber
    - serialNumber
    - vendorEquipmentType

    Args:
    ----
    df (pd.DataFrame)
        A Pandas DataFrame containing the unmodified columns.

    Returns:
    ----
    df (pd.DataFrame)
        A Pandas DataFrame containing the modified columns.
    '''
    columns = ['platformId',
               'hostname',
               'name',
               'description',
               'partNumber',
               'serialNumber',
               'vendorEquipmentType']
    df = df[columns]
    return df


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
    main(args)
