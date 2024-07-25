import pandas as pd
import requests
import sqlite3
from netmanage.helpers import helpers as hp
from requests.exceptions import HTTPError
from sqlalchemy import create_engine
from typing import Optional


def get_auth_token(
    url: str, username: str, password: str, verify: bool = True
) -> Optional[str]:
    """
    Obtain an authentication token from a Cisco ACI APIC.

    This function sends a request to the specified APIC URL with the given credentials,
    and retrieves an authentication token if the credentials are valid.

    Parameters
    ----------
    url : str
        The base URL of the APIC to authenticate against, including scheme (e.g.,
        'https://apic.example.com' or 'https://172.25.99.208').
    username : str
        The username to use for authentication.
    password : str
        The password to use for authentication.
    verify : bool, optional
        Whether to verify the server's TLS certificate, by default True.

    Returns
    -------
    Optional[str]
        The authentication token as a string if authentication is successful, None
        otherwise.

    Raises
    ------
    HTTPError
        If an HTTP error occurs during the authentication request.
    Exception
        If any other exception occurs during the authentication request.

    Examples
    --------
    >>> apic_url = 'https://172.25.99.208'
    >>> username = 'admin'
    >>> password = 'password'
    >>> token = get_auth_token(apic_url, username, password)
    >>> type(token)
    <class 'str'>

    >>> token = get_auth_token(apic_url, 'wronguser', password)
    >>> token is None
    True

    """
    # Setup the logger
    logger = hp.setup_logger()

    # Disable warnings for invalid certs(only used for self-signed certs)
    requests.packages.urllib3.disable_warnings()

    # Create the request parameters
    login_url = f"{url}/api/aaaLogin.json"
    login_body = {"aaaUser": {"attributes": {"name": username, "pwd": password}}}

    # Attempt to retrieve an authentication token
    try:
        response = requests.post(login_url, json=login_body, verify=verify)
        response.raise_for_status()
        token = response.json()["imdata"][0]["aaaLogin"]["attributes"]["token"]
        return token
    except HTTPError as http_err:
        err_message = f"HTTP error occurred: {http_err}"
        logger.critical(err_message)
    except Exception as err:
        err_message = f"An error occurred: {err}"
        logger.critical(err_message)

    return None


def store_results_in_db(
    df: pd.DataFrame,
    db_path: str,
    table_name: str,
    jobs_timestamp: str,
    id_columns=None,
):
    """
    Makes any necessary adjustments to the DataFrame, then calls `sync_table_with_df`

    Parameters
    ----------

    Returns
    -------
    None
    """
    # Add the jobs timestamp to the dataframe, if it is not already part of it
    if "timestamp" not in df.columns:
        df["timestamp"] = jobs_timestamp

    # Make the jobs timestamp the first column of the dataframe
    new_col_order = ["timestamp"]
    new_col_order = new_col_order + [
        col for col in df.columns if col not in new_col_order
    ]

    # Ensure that `timestamp` is not part of the index columns. This method also
    # ensures that a list of index columns is created (if one was not passed to this
    # function, then it uses all dataframe columns except `timestamp`)
    if not id_columns:
        id_columns = df.columns.to_list()
    id_columns = [_ for _ in id_columns if _ != "timestamp"]

    # Sync the dataframe with the database table
    sync_table_with_df(db_path, table_name, df, id_columns)


def sync_table_with_df(db_path, table_name, df, id_columns):
    # Create a connection to the database
    engine = create_engine(f"sqlite:///{db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Convert id_columns to a list if it is not already
    if not isinstance(id_columns, list):
        id_columns = [id_columns]

    # Check if the table exists
    cursor.execute(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    )
    table_exists = cursor.fetchone()

    # Convert the dataframe to a string, and replace 'nan' values with empty strings
    df.fillna("", inplace=True)
    df = df.astype(str)
    # df = df.replace("nan", "")

    # Set the dataframe columns to lowercase
    df.columns = df.columns.str.lower()

    if not table_exists:
        # If the table does not exist, create it from the DataFrame
        df.to_sql(table_name, engine, index=False)

        # Create an index on the ID columns
        index_name = f"{table_name}_{'_'.join(id_columns)}_idx"
        index_columns = ", ".join(
            [f'"{col}"' for col in id_columns]
        )  # Quote column names

        # Quote the index_name and table_name as well
        cursor.execute(
            f'CREATE INDEX "{index_name}" ON "{table_name}" ({index_columns})'
        )
    else:
        # If the table exists, check for schema discrepancies
        # Get existing table columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = [info[1] for info in cursor.fetchall()]

        # Add missing DataFrame columns to the table
        df_columns = df.columns.tolist()
        for column in df_columns:
            if column not in existing_columns:
                cursor.execute(
                    f'ALTER TABLE {table_name} ADD COLUMN "{column}" TEXT DEFAULT ""'
                )

        # Add missing table columns to the DataFrame
        for column in existing_columns:
            if column not in df_columns:
                df[column] = ""

        # Sync rows between the DataFrame and the table
        temp_table_name = f"{table_name}_temp"
        df.to_sql(temp_table_name, engine, index=False, if_exists="replace")

        # Adjust the INSERT query for the composite or single key
        where_clause = " AND ".join(
            [
                f't2."{col}" = {temp_table_name}."{col}"' for col in id_columns
            ]  # Quote column names
        )
        insert_query = f"""
        INSERT INTO {table_name}
        SELECT * FROM {temp_table_name}
        WHERE NOT EXISTS(
            SELECT 1 FROM {table_name} t2
            WHERE {where_clause}
        )
        """
        cursor.execute(insert_query)

        # Drop the temporary table
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table_name}")

    # Commit changes and close the connection
    conn.commit()
    cursor.close()
    conn.close()
