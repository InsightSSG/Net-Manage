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


def validator_single_col(columns,
                         db_path,
                         expected,
                         identifier_col,
                         table,
                         validation_col):
    '''
    A generic validator for collectors that can be validated with the state of
    a single column--e.g., 'status', 'availability', etc.

    Args:
        columns (list):         A list of columns to return. One of the columns
                                must be the one that is being used for
                                validation.
        db_path (str):          The path to the database
        expected (str):         The expected value of 'validation_col' (see
                                below)
        identifier_col (str):   The column name to use for identifying a unique
                                entity (e.g., device, network, organization,
                                etc)
        table (str):            The name of the table
        validation_col (str):   The column name to use for validation

    Returns:
        df_diff (obj):  A DataFrame containing any differences
    '''
    return_cols = ',\n'.join(columns)

    # Get the first and last timestamp for each unique device in the table
    df_stamps = hp.get_first_last_timestamp(db_path, table, identifier_col)

    # Create an empty dataframe to store the devices that have changed status
    df_diff = pd.DataFrame(data=list(), columns=columns)

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
        unique = row[identifier_col]
        first_ts = row['first_ts']
        last_ts = row['last_ts']

        # This query compares the status of the device in the first timestamp
        # to the status in the second timestamp, and stores the results in a
        # dataframe.
        query = f'''select {return_cols} from {table}
                    where ({validation_col} = "{expected}"
                        or {validation_col} != "{expected}")
                      and timestamp = "{first_ts}"
                      and {identifier_col} = "{unique}"
                    except
                    select {return_cols} from {table}
                    where ({validation_col} = "{expected}"
                        or {validation_col} != "{expected}")
                      and timestamp = "{last_ts}"
                      and {identifier_col} = "{unique}"
                '''
        df_left = pd.read_sql(query, con)

        # If any results were returned, then we know that data in one of the
        # 'return_cols' has changed.
        if len(df_left) > 0:
            # This query compares the status of the device in the last
            # timestamp to the status in the first timestamp, then stores the
            # result in a dataframe.
            query = f'''select {return_cols} from {table}
                        where ({validation_col} = "{expected}"
                            or {validation_col} != "{expected}")
                        and timestamp = "{last_ts}"
                        and {identifier_col} = "{unique}"
                        except
                        select {return_cols} from {table}
                        where ({validation_col} = "{expected}"
                            or {validation_col} != "{expected}")
                        and timestamp = "{first_ts}"
                        and {identifier_col} = "{unique}"
                    '''
            df_right = pd.read_sql(query, con)

            # 'except' will return results if the data in any of the columns
            # changed, so it is necessary to compare the two statuses.
            original = df_left[validation_col].to_list()
            new = df_right[validation_col].to_list()

            # If the expected value changed, then add the new value to
            # 'df_left' as a new column, then add'df_left' to 'df_diff' as a
            # new row.
            if original != new:
                df_left[f'new_{validation_col}'] = new
                df_diff = pd.concat([df_diff, df_left])

    # Rename the 'status' column to 'original_status'
    df_diff.rename(columns={validation_col: f'original_{validation_col}'},
                   inplace=True)

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
    # # Get the first and last timestamp for each unique device in the table
    # df_stamps = hp.get_first_last_timestamp(db_path, table, 'mac')

    # Define the columns to query
    cols = ['orgId',
            'networkId',
            'name',
            'model',
            'lanIp',
            'publicIp',
            'mac',
            'status']

    df_diff = validator_single_col(cols,
                                   db_path,
                                   'online',
                                   'mac',
                                   table,
                                   'status')

    return df_diff
