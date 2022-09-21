#!/usr/bin/env python3

'''
Runs data collectors and stores them in a sqlite database.
'''

import argparse
import datetime as dt
# from re import S
import sys

# import collectors as cl
import helpers as hp
import os
import pandas as pd
import readline
import run_collectors as rc
import sqlite3 as sl
# import sys

from tabulate import tabulate

# Protect creds by not writing history to .python_history
readline.write_history_file = lambda *args: None


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
parser.add_argument('-u', '--username',
                    help='''The username for connecting to the devices. If
                            missing, script will prompt for it.''',
                    action='store'
                    )
parser.add_argument('-P', '--password',
                    help='''The password for connecting to the devices. This is
                            included for automation, but I do not recommend
                            using it when running the script manually. If you
                            do, then your password could show up in the command
                            history.''',
                    action='store'
                    )
requiredNamed = parser.add_argument_group('required named arguments')
requiredNamed.add_argument('-i', '--in_file',
                           help='''The path the Excel spreadsheet defining
                                   tests to run''',
                           required=True,
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


# Import the helpers and collectors libraries nm_path.
# sys.path.append(args.nm_path)
# import helpers as hp
# import collectors as cl


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

    if not args.username:
        username = hp.get_username()
    else:
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


def validate(collector, db, df, ts, testit=False):
    '''
    This function does four things:

    1. Connects to the specified database and gets the first timestamp for the
       specified collector (table).
    2. Queries the database for the results for that collector and timestamp
    3. Compares the query results to 'df'
    4. Returns a dataframe that contains *only* rows that are in the database
       query result but NOT in 'df'

    The use case is to find rows that were up (or available, ready, etc) but
    are not up anymore.

    Args:
        collector (str):    The name of the collector
        db (str):           The name of the database to query
        df (DataFrame):     The dataframe containing the data to compare
        col_name (str):     The column name to check ('interface', 'pool', etc)
        testit (bool):      Will drop random results from 'df' to simulate
                            a real-world event.

    Returns:
        df_missing (DataFrame): The missing rows
    '''
    if len(df) > 0:  # Skip empty dataframes
        table = collector
        con = sl.connect(db)
        df_ts = pd.read_sql(f'select timestamp from {table} limit 1', con)
        first_ts = df_ts['timestamp'].to_list()[0]
        df_pre = pd.read_sql(f'select * from {table} where timestamp = "{ts}"',
                             con)
        con.close()

    # Validate F5 Pool Availability
    if collector == 'f5_pool_availability':
        print(collector.upper())
        df_pre = df_pre.loc[df_pre['availability'] == 'available'].copy()
        down_rows = list()
        # missing_rows = list()
        for idx, row in df_pre.iterrows():
            device = row['device']
            partition = row['partition']
            pool = row['pool']
            pre_availability = row['availability']
            new_vals = df.loc[(df['device'] == device) &
                              (df['partition'] == partition) &
                              (df['pool'] == pool)]
            new_availability = new_vals['availability'].values
            # if pre_availability != new_availability[0]:
            if pre_availability != new_availability:
                # del new_vals['reason']
                down_rows.append(new_vals.iloc[0].to_list())
        if testit:  # Insert a false positive for testing
            down_rows.append(new_vals.iloc[0].to_list())
        if down_rows:
            cols = df_pre.columns.to_list()[1:]
            df_down = pd.DataFrame(data=down_rows, columns=cols)

            print(tabulate(df_down,
                           headers='keys',
                           tablefmt='psql',
                           showindex=False))

    # Validate F5 VIP availability
    if collector == 'f5_vip_availability':
        print(collector.upper())
        ts = '2022-09-18_0131'
        con = sl.connect(db)
        return_cols = 'device, partition, vip, destination, port, availability'
        query_1 = f'availability = "available" and timestamp = "{first_ts}"'
        query_2 = f'availability = "available" and timestamp = "{ts}"'
        query = f'''select {return_cols}
                    from f5_vip_availability
                    where {query_1}
                    except
                    select {return_cols}
                    from f5_vip_availability
                    where {query_2}
                    '''
        # print(query)
        df_diff = pd.read_sql(query, con)

        # if len(df_diff) > 0:
        #     print(tabulate(df_diff,
        #                    headers='keys',
        #                    tablefmt='psql',
        #                    showindex=False))

        query_1 = f'availability != "available" and timestamp = "{first_ts}"'
        query_2 = f'availability != "available" and timestamp = "{ts}"'
        query = f'''select {return_cols}
                    from f5_vip_availability
                    where {query_1}
                    except
                    select {return_cols}
                    from f5_vip_availability
                    where {query_2}
                    '''
        print(query)
        df_diff = pd.read_sql(query, con)

        con.close()
        if len(df_diff) > 0:
            print(tabulate(df_diff,
                           headers='keys',
                           tablefmt='psql',
                           showindex=False))

    # Validate F5 Pool Member Availability
    if collector == 'f5_pool_member_availability':
        print(collector.upper())
        df_pre = df_pre.loc[df_pre['pool_member_state'] == 'available'].copy()
        down_rows = list()
        # missing_rows = list()
        for idx, row in df_pre.iterrows():
            device = row['device']
            pool_name = row['pool_name']
            pool_member = row['pool_member']
            pre_availability = row['pool_member_state']
            new_vals = df.loc[(df['device'] == device) &
                              (df['pool_name'] == pool_name) &
                              (df['pool_member'] == pool_member)]
            new_availability = new_vals['pool_member_state'].values
            # if pre_availability != new_availability[0]:
            if pre_availability != new_availability:
                # del new_vals['reason']
                down_rows.append(new_vals.iloc[0].to_list())
        if testit:  # Insert a false positive for testing
            down_rows.append(new_vals.iloc[0].to_list())
        if down_rows:
            cols = df_pre.columns.to_list()[1:]
            df_down = pd.DataFrame(data=down_rows, columns=cols)

            print(tabulate(df_down,
                           headers='keys',
                           tablefmt='psql',
                           showindex=False))


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

                result = rc.collect(ansible_os,
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
                # print(tabulate(result, headers='keys', tablefmt='psql'))

                # Add the output to the database
                con = connect_to_db(db)

                # Add the dataframe to the database
                table = collector.upper()
                result.to_sql(table, con, if_exists='append')
                con.commit()
                con.close()

                # con = sl.connect(db)
                # df_tmp = pd.read_sql(f'select * from {table}', con)
                # try:
                #     # TODO: Re-write this to not rely on try/except.
                #     print(tabulate(df_tmp.drop('reason', axis=1),
                #                    headers='keys',
                #                    tablefmt='psql'))
                # except Exception as e:
                #     print(tabulate(df_tmp, headers='keys', tablefmt='psql'))
                #     print(str(e))
                # con.close()

                # print(result.info())
                # print(df_tmp.info())

                # Run validators
                validate(collector, db, result, ts, testit=False)


if __name__ == '__main__':
    main()
