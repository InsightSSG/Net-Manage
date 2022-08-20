#!/usr/bin/env python3

'''
Runs data collectors and stores them in a sqlite database.
'''

import argparse
import datetime as dt
import getpass
import helpers as hp
# import nmap3
import data_collectors as dc
# import openpyxl
import os
import pandas as pd
import sqlite3 as sl
import sys

from tabulate import tabulate


# Create the parser for command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-d', '--database',
                    help='''The database name. Defaults to YYYY-MM-DD.db.''',
                    default=f'{str(dt.datetime.now()).split()[0]}.db',
                    action='store'
                    )
parser.add_argument('-o', '--out_dir',
                    help='''The directory to save output to (the filename will
                            be auto-generated). The database will also be saved
                            here.''',
                    default=os.path.expanduser('~'),
                    action='store'
                    )
parser.add_argument('-P', '--password',
                    help='''SSH password. DO NOT use on a shared computer or
                            unencrypted drive. Follow your organization's
                            policies.''',
                    action='store'
                    )
parser.add_argument('-u', '--username',
                    help='''The username for connecting to the devices. If
                            missing, will default to current user.''',
                    default=getpass.getuser(),
                    action='store'
                    )
requiredNamed = parser.add_argument_group('required named arguments')
requiredNamed.add_argument('-i', '--in_file',
                           help='''The path the Excel spreadsheet defining
                                   tests to run''',
                           action='store'
                           )
requiredNamed.add_argument('-n', '--nm_path',
                           help='The path to the Net-Manage repository',
                           required=True,
                           action='store'
                           )
requiredNamed.add_argument('-p', '--private_data_dir',
                           help='''The path to the Ansible private data
                                   directory (I.e., the directory containing
                                   the 'inventory' and 'env' folders).''',
                           required=True,
                           action='store'
                           )
args = parser.parse_args()


def arg_parser():
    '''
    Extract system args and assign variable names.

    Args:
        None

    Returns:
        vars_dict (dict):   A dictionary containing arg variables
    '''
    # Parse the command line arguments
    in_file = os.path.expanduser(args.in_file)
    nm_path = os.path.expanduser(args.nm_path)
    out_dir = os.path.expanduser(args.out_dir)
    private_data_dir = os.path.expanduser(args.private_data_dir)
    username = args.username
    db = f'{out_dir}/{args.database}'
    # Get the user's SSH password
    if not args.password:
        password = hp.get_password()
    else:
        password = args.password
    return db, in_file, nm_path, out_dir, private_data_dir, username, password


def connect_to_db(db):
    '''
    Opens a connection to the sqlite database.

    Args:
        db (str):   Path to the database

    Returns:
        con (ob):   Connection to the database
    '''
    try:
        con = sl.connect(db)
    except Exception as e:
        if str(e) == 'unable to open database file':
            print(f'Cannot connect to db "{db}". Does directory exist?')
            sys.exit()
        else:
            print(f'Caught exception "{str(e)}"')
            sys.exit()
    return con


def main():
    # Parse the command line arguments
    db, in_file, nm_path, out_dir, private_data_dir, username, password = \
        arg_parser()

    # Create the variables required for running data collectors
    df_collectors, df_vars, nm_path, play_path = \
        hp.map_tests_to_os(private_data_dir,
                           nm_path,
                           in_file)

    print('COLLECTORS:')
    print(tabulate(df_collectors,
                   headers='keys',
                   tablefmt='psql',
                   showindex=False))

    print('COLLECTOR VARIABLES')
    print(tabulate(df_vars,
                   headers='keys',
                   tablefmt='psql',
                   showindex=False))

    # Set the timestamp. This is for database queries. Setting it a single time
    # at the start of the script will allow all collectors to have the same
    # timestamp.
    ts = dt.datetime.now()
    ts = ts.strftime('%Y-%m-%d_%H%M')

    # Execute collectors and store the output in a SQLite database.
    # Collectors are executed by column. If column_1 is 'interface_status' and
    # column_2 is 'interface_description', the interface statuses for all
    # hostgroups will be gathered, then the interface descriptions for all
    # hostgroups, and so on.
    for c in df_collectors.columns.to_list():
        collector = c
        for idx, row in df_collectors.iterrows():
            hostgroup = row[c]
            if hostgroup != 'nan':
                collect_vars = df_vars.loc[df_vars['host_group'] == hostgroup]
                ansible_os = collect_vars['ansible_network_os'].values[0]

                result = dc.collect(ansible_os,
                                    collector,
                                    username,
                                    password,
                                    hostgroup,
                                    play_path,
                                    private_data_dir,
                                    nm_path)
                # Set the timestamp as the index
                new_idx = list()
                for i in range(0, len(result)):
                    new_idx.append(ts)

                # Display the output to the console
                result['timestamp'] = new_idx
                result = result.set_index('timestamp')
                print(tabulate(result, headers='keys', tablefmt='psql'))

                # Add the output to the database
                con = connect_to_db(db)

                # Add the dataframe to the database
                table = collector.upper()
                result.to_sql(table, con, if_exists='append')
                con.commit()
                con.close()

                con = sl.connect(db)
                df_tmp = pd.read_sql(f'select * from {table}', con)
                print(tabulate(df_tmp, headers='keys', tablefmt='psql'))
                con.close()


if __name__ == '__main__':
    main()
