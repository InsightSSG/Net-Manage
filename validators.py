#!/usr/bin/env python3

'''
Runs data collectors and stores them in a sqlite database.
'''

import pandas as pd
import sqlite3 as sl

from tabulate import tabulate


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
        # ts = '2022-09-18_0131'
        con = sl.connect(db)
        return_cols = ','.join(['device',
                                'partition',
                                'vip',
                                'destination',
                                'port,'
                                'availability,'
                                'reason'])
        where_1 = f'availability = "available" and timestamp = "{first_ts}"'
        where_2 = f'availability = "available" and timestamp = "{ts}"'
        query = f'''select {return_cols}
                    from f5_vip_availability
                    where {where_1}
                    except
                    select {return_cols}
                    from f5_vip_availability
                    where {where_2}
                    '''
        print(query)
        df_diff = pd.read_sql(query, con)

        if len(df_diff) > 0:
            print(tabulate(df_diff,
                           headers='keys',
                           tablefmt='psql',
                           showindex=False))

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
        # print(query)
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
