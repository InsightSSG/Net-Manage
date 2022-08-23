#!/usr/bin/env python3

'''
Runs data collectors and stores them in a sqlite database.
'''

import argparse
import datetime as dt
import getpass

import helpers as hp
import collectors as cl
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


def validate(collector, db, df, testit=False):
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
    table = collector
    con = sl.connect(db)
    df_ts = pd.read_sql(f'select timestamp from {table} limit 1', con)
    ts = df_ts['timestamp'].to_list()[0]
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
            new_availability = new_vals['availability'][0]
            new_avail = new_vals['avail'][0]
            new_total = new_vals['total'][0]
            new_cur = new_vals['cur'][0]
            new_reason = new_vals['reason'][0]
            if pre_availability != new_availability:
                # down_rows.append(row)
                # down_rows.append(row.to_list())
                _row = row.to_list()
                print(_row)
                _row[-7] = new_availability
                _row[-5] = new_total
                _row[-4] = new_avail
                _row[-3] = new_cur
                _row[-1] = new_reason
                down_rows.append(_row)

        if down_rows:
            cols = df_pre.columns.to_list()
            df_down = pd.DataFrame(data=down_rows, columns=cols)

            print(tabulate(df_down,
                           headers='keys',
                           tablefmt='psql'))
            # print(df_down.info())

    # Validate F5 VIP availability
    if collector == 'f5_vip_availability':
        print(collector.upper())
        df_pre = df_pre.loc[df_pre['availability'] == 'available'].copy()
        down_rows = list()
        for idx, row in df_pre.iterrows():
            device = row['device']
            partition = row['partition']
            vip = row['vip']
            avail = row['availability']
            new_vals = df.loc[(df['device'] == device) &
                              (df['partition'] == partition) &
                              (df['vip'] == vip)]
            new_avail = new_vals['availability'][0]
            new_state = new_vals['state'][0]
            new_reason = new_vals['reason'][0]
            if avail != new_avail:
                _row = row.to_list()
                _row[-3] = new_avail
                _row[-2] = new_state
                _row[-1] = new_reason
                down_rows.append(_row)
        if down_rows:
            cols = df_pre.columns.to_list()
            df_down = pd.DataFrame(data=down_rows, columns=cols)
            print(tabulate(df_down,
                           headers='keys',
                           tablefmt='psql'))

    # Validate F5 pool member availability
    if collector == 'f5_pool_member_availability':
        print(collector.upper())
        df['timestamp'] = df.index.to_list()  # TODO: Move this out of if/then
        df_pre = df_pre.loc[df_pre['pool_member_state'] == 'available'].copy()
        down_rows = list()
        for idx, row in df_pre.iterrows():
            device = row['device'].strip()
            pool = row['pool_name'].strip()
            member = row['pool_member'].strip()
            pre_state = row['pool_member_state']
            new_vals = df.loc[(df['device'] == device) &
                              (df['pool_name'] == pool) &
                              (df['pool_member'] == member)]
            new_state = new_vals['pool_member_state'][0].strip()
            if pre_state != new_state:
                _row = row.to_list()
                _row[-1] = new_state
                down_rows.append(_row)
                # down_rows.append(new_vals.iloc[0].to_list()[1:])
        if down_rows:
            cols = df_pre.columns.to_list()
            df_down = pd.DataFrame(data=down_rows, columns=cols)

            print(tabulate(df_down,
                           headers='keys',
                           tablefmt='psql'))

    print(len(df))
    if testit:
        df = df_pre[10:-10].copy()

        # val_1 = df['vip'].to_list()
        # val_2 = df['partition'].to_list()
        # val_3 = df['destination'].to_list()
        # val_4 = df['port'].to_list()
        # val_5 = df['device'].to_list()

        # Returns correct number of results (9)
        # '''df_missing = df_pre.query('vip not in @val_1 and partition not in
        #    @val_2 and destination not in @val_3')'''

        # Returns only 2 results, even though combination does not appear
        # elsewhere in dataframe
        # '''df_missing = df_pre.query('vip not in @val_1 and partition not in
        #    @val_2 and destination not in @val_3 and port not in @val_4')'''

        # Note: When I tried to include device (@val_5) it returned no results

        # TODO: Re-write this using df.query (see comments above). I tried to
        #       do it that way, but could not get consistent results. I had
        #       the same problem when using ".isna". I am sure it is user
        #       error on my part, but this method is acceptable for now.

        # Iterate over the pre_check data and ensure each row is present in
        # 'df'. If it is not present, add it to 'missing_rows,' then create a
        # dataframe from it.
        missing_rows = list()
        for idx, row in df_pre.iterrows():
            device = row['device']
            partition = row['partition']
            vip = row['vip']
            new_vals = df.loc[(df['device'] == device) &
                              (df['partition'] == partition) &
                              (df['vip'] == vip)]
            if len(new_vals) == 0:
                missing_rows.append(row)

        if missing_rows:
            cols = df_pre.columns.to_list()
            df_missing = pd.DataFrame(data=missing_rows, columns=cols)

        print(tabulate(df_missing.drop('reason', axis=1),
                       headers='keys',
                       tablefmt='psql'))
        print(df_missing.info())


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

    sys.exit()

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

                result = cl.collect(ansible_os,
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
                validate(collector, db, result, testit=False)


if __name__ == '__main__':
    main()
