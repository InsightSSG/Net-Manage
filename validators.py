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
    print(df_stamps.info())

    cols = ['orgId',
            'networkId',
            'name',
            'model',
            'lanIp',
            'publicIp',
            'mac',
            'status']

    return_cols = ',\n'.join(cols)

    df_diff = pd.DataFrame(data=list(), columns=cols)

    # return df_stamps

    con = sl.connect(db_path)

    # query = f'''SELECT {return_cols}
    #             FROM meraki_get_org_device_statuses
    #             where timestamp = "{first_ts}"
    #             except
    #             SELECT {return_cols}
    #             FROM meraki_get_org_device_statuses
    #             where timestamp = "{first_ts}"
    # '''

    for idx, row in df_stamps.iterrows():
        mac = row['mac']
        first_ts = row['first_ts']
        last_ts = row['last_ts']

        # status = row['status']

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

        if len(df_left) > 0:
            from tabulate import tabulate
            print(tabulate(df_left, headers='keys', tablefmt='psql'))
            # break
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
            # print(query)
            df_right = pd.read_sql(query, con)
            from tabulate import tabulate
            print(tabulate(df_right, headers='keys', tablefmt='psql'))
            # break

            original_status = df_left['status'].to_list()
            new_status = df_right['status'].to_list()

            print(original_status)
            print(new_status)

            if original_status != new_status:
                df_left = df_left.rename(columns={'status': 'original_status'})
                df_left['new_status'] = new_status
                from tabulate import tabulate
                print(tabulate(df_left, headers='keys', tablefmt='psql'))
        # print(query)
            # break
        # df = pd.read_sql(query, con)
        # original_status = df[0]['original_status']
                df_diff = pd.concat([df_diff, df_left])
                from tabulate import tabulate
                print(tabulate(df_diff, headers='keys', tablefmt='psql'))
                break

    del df_diff['status']

    return df_diff
