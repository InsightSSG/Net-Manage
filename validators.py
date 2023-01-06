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
    df_stamps = hp.get_first_last_timestamp(db_path, table, 'mac')

    # Define the columns to query
    cols = ['orgId',
            'networkId',
            'name',
            'model',
            'lanIp',
            'publicIp',
            'mac',
            'status']
    return_cols = ',\n'.join(cols)

    # Create an empty dataframe to store the devices that have changed status
    df_diff = pd.DataFrame(data=list(), columns=cols)

    # Create the database connection
    con = sl.connect(db_path)

    # For each device, compare the most recent status to the original status.
    # This method deserves some explanation.
    #
    # I experimented with many ways to compare the original status to the most
    # recent status. Out of all of them, this method was the fastest, even
    # though it requires running two queries for each device.
    #
    # The reason two queries are necessary is because a comparison done with
    # 'except' only returns the left side of the query (e.g., the first
    # timestamp). In other words, the comparison actually happens, but the
    # output only shows what the original status was.
    #
    # That is why two queries are needed. The first query compares the first
    # timestamp to the last timestamp, and the second query compares the last
    # timestamp to the first timestamp. That way we can see exactly what
    # changed--e.g., 'online' to 'alerting', 'dormant' to 'online', etc.
    for idx, row in df_stamps.iterrows():
        mac = row['mac']
        first_ts = row['first_ts']
        last_ts = row['last_ts']

        # This query compares the status of the device in the first timestamp
        # to the status in the second timestamp, and stores the results in a
        # dataframe.
        query = f'''select {return_cols} from {table}
                    where (status = "online"
                        or status != "online")
                      and timestamp = "{first_ts}"
                      and mac = "{mac}"
                    except
                    select {return_cols} from {table}
                    where (status = "online"
                        or status != "online")
                      and timestamp = "{last_ts}"
                      and mac = "{mac}"
                '''
        df_left = pd.read_sql(query, con)

        # If any results were returned, then we know that data in one of the
        # 'return_cols' has changed.
        if len(df_left) > 0:
            # This query compares the status of the device in the last
            # timestamp to the status in the first timestamp, then stores the
            # result in a dataframe.
            query = f'''select {return_cols} from {table}
                        where (status = "online"
                            or status != "online")
                        and timestamp = "{last_ts}"
                        and mac = "{mac}"
                        except
                        select {return_cols} from {table}
                        where (status = "online"
                            or status != "online")
                        and timestamp = "{first_ts}"
                        and mac = "{mac}"
                    '''
            df_right = pd.read_sql(query, con)

            # 'except' will return results if the data in any of the columns
            # changed, so it is necessary to compare the two statuses.
            original_status = df_left['status'].to_list()
            new_status = df_right['status'].to_list()

            # If the status changed, then add the new status to 'df_left' as a
            # new column, then add 'df_left' to 'df_diff'
            if original_status != new_status:
                df_left['new_status'] = new_status
                df_diff = pd.concat([df_diff, df_left])

    # Rename the 'status' column to 'original_status'
    df_diff.rename(columns={'status': 'original_status'},
                   inplace=True)

    return df_diff
