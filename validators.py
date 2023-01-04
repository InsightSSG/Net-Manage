#!/usr/bin/env python3

'''
Runs data collectors and stores them in a sqlite database.
'''

import helpers as hp
import pandas as pd
import sqlite3 as sl


def f5_pool_availability(db_path, table):
    '''
    Validates a table based on a single column (I.e., "available", "status,
    etc)

    Args:
        db_path (str):  The path to the database
        table (str):    The name of the table
        col_name (str): The name of the column to validate against
        columns (list): A list of specific columns to include in the query.
                        This is so columns that have data that frequently
                        changes--like traffic counters--will not create false
                        positives. If the table does not have any data like
                        that then the arg does not need to be passed.

    Returns:
        df_diff (obj):  A DataFrame containing any differences
    '''
    # Get the first and last timestamp for each unique device in the table
    df_stamps = hp.get_first_last_timestamp(db_path, table)

    cols = ['device',
            'partition',
            'pool',
            'availability',
            'state',
            'total',
            'avail',
            'cur',
            'reason']

    return_cols = ','.join(cols)

    df_diff = pd.DataFrame(data=list(), columns=cols)

    con = sl.connect(db_path)
    for idx, row in df_stamps.iterrows():
        device = row['device']
        first_ts = row['first_ts']
        last_ts = row['last_ts']

        query = f'''select {return_cols} from {table}
                    where (availability = "available"
                        or availability != "available")
                      and timestamp = "{first_ts}"
                      and device = "{device}"
                    except
                    select {return_cols} from {table}
                    where (availability = "available"
                        or availability != "available")
                      and timestamp = "{last_ts}"
                      and device = "{device}"
                 '''
        df = pd.read_sql(query, con)
        df_diff = pd.concat([df_diff, df])

    return df_diff


def f5_pool_member_availability(db_path, table):
    '''
    Validates a table based on a single column (I.e., "available", "status,
    etc)

    Args:
        db_path (str):  The path to the database
        table (str):    The name of the table
        col_name (str): The name of the column to validate against
        columns (list): A list of specific columns to include in the query.
                        This is so columns that have data that frequently
                        changes--like traffic counters--will not create false
                        positives. If the table does not have any data like
                        that then the arg does not need to be passed.

    Returns:
        df_diff (obj):  A DataFrame containing any differences
    '''
    # Get the first and last timestamp for each unique device in the table
    df_stamps = hp.get_first_last_timestamp(db_path, table)

    cols = ['device',
            'pool_name',
            'pool_member',
            'pool_member_state']

    return_cols = ','.join(cols)

    df_diff = pd.DataFrame(data=list(), columns=cols)

    con = sl.connect(db_path)
    for idx, row in df_stamps.iterrows():
        device = row['device']
        first_ts = row['first_ts']
        last_ts = row['last_ts']

        query = f'''select {return_cols} from {table}
                    where (pool_member_state = "available"
                        or pool_member_state != "available")
                      and timestamp = "{first_ts}"
                      and device = "{device}"
                    except
                    select {return_cols} from {table}
                    where (pool_member_state = "available"
                        or pool_member_state != "available")
                      and timestamp = "{last_ts}"
                      and device = "{device}"
                 '''
        df = pd.read_sql(query, con)
        df_diff = pd.concat([df_diff, df])

    return df_diff


def f5_vip_availability(db_path, table):
    '''
    Validates a table based on a single column (I.e., "available", "status,
    etc)

    Args:
        db_path (str):  The path to the database
        table (str):    The name of the table
        col_name (str): The name of the column to validate against
        columns (list): A list of specific columns to include in the query.
                        This is so columns that have data that frequently
                        changes--like traffic counters--will not create false
                        positives. If the table does not have any data like
                        that then the arg does not need to be passed.

    Returns:
        df_diff (obj):  A DataFrame containing any differences
    '''
    # Get the first and last timestamp for each unique device in the table
    df_stamps = hp.get_first_last_timestamp(db_path, table)

    cols = ['device',
            'partition',
            'vip',
            'destination',
            'port',
            'availability',
            'reason']

    return_cols = ','.join(cols)

    df_diff = pd.DataFrame(data=list(), columns=cols)

    con = sl.connect(db_path)
    for idx, row in df_stamps.iterrows():
        device = row['device']
        first_ts = row['first_ts']
        last_ts = row['last_ts']

        query = f'''select {return_cols} from {table}
                    where (availability = "available"
                        or availability != "available")
                      and timestamp = "{first_ts}"
                      and device = "{device}"
                    except
                    select {return_cols} from {table}
                    where (availability = "available"
                        or availability != "available")
                      and timestamp = "{last_ts}"
                      and device = "{device}"
                 '''
        df = pd.read_sql(query, con)
        df_diff = pd.concat([df_diff, df])

    return df_diff


def meraki_device_statuses_availability(db_path, table):
    '''
    Validates the state of Meraki devices based on the 'status' column.

    Args:
        db_path (str):  The path to the database
        table (str):    The name of the table

    Returns:
        df_diff (obj):  A DataFrame containing any differences
    '''
    # Get the first and last timestamp for each unique device in the table
    df_stamps = hp.get_first_last_timestamp(db_path, table, 'name')

    cols = ['orgId',
            'networkId',
            'name',
            'model',
            'lanIp',
            'publicIp',
            'status']

    return_cols = ','.join(cols)

    df_diff = pd.DataFrame(data=list(), columns=cols)

    con = sl.connect(db_path)
    for idx, row in df_stamps.iterrows():
        name = row['name']
        first_ts = row['first_ts']
        last_ts = row['last_ts']

        query = f'''select {return_cols} from {table}
                    where (status = "online"
                        or status != "online")
                      and timestamp = "{first_ts}"
                      and name = "{name}"
                    except
                    select {return_cols} from {table}
                    where (status = "online"
                        or status != "online")
                      and timestamp = "{last_ts}"
                      and name = "{name}"
                '''

        df = pd.read_sql(query, con)
        df_diff = pd.concat([df_diff, df])

    return df_diff
