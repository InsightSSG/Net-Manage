import ipaddress
import concurrent.futures
import os
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import SubscriptionClient
from dotenv import load_dotenv
from netmanage.helpers import helpers as hp
from typing import Dict, List

load_dotenv()

logger = hp.setup_logger()

# Function definitions (get_subscription_ids, get_private_ips, get_public_ips, get_subnets) should be included here

def get_azure_default_credential():
    """
    Creates an instance of DefaultAzureCredential. Uses the cached token(s) created
    when a user logs in with the Azure CLI.

    Parameters
    ----------
    None

    Returns
    -------
    credential : DefaultAzureCredential
        An instance of DefaultAzureCredential which contains the cached tokens.

    Notes
    -----
    This method is designed for developers, since it requires that a user login
    interactively through Azure CLI.
    """
    credential = DefaultAzureCredential()
    return credential
    

def get_subscription_ids(credential: DefaultAzureCredential) -> List[str]:
    """
    Retrieve all subscription IDs associated with the authenticated Azure account.
    
    Parameters
    ----------
    credential : DefaultAzureCredential
        The credential object used for authentication.
    
    Returns
    -------
    List[str]
        A list of subscription IDs.
    
    Raises
    ------
    azure.core.exceptions.HttpResponseError
        If the request to the Azure API fails.
    """
    subscription_client = SubscriptionClient(credential)
    
    subscription_ids = []
    for subscription in subscription_client.subscriptions.list():
        subscription_ids.append(subscription.subscription_id)
    
    return subscription_ids


def get_subnets(subscription_id: str, credential: DefaultAzureCredential) -> Dict[str, List[str]]:
    """
    Retrieve all subnets associated with the given subscription ID.
    
    Parameters
    ----------
    subscription_id : str
        The Azure subscription ID.
    credential : DefaultAzureCredential
        The credential object used for authentication.
    
    Returns
    -------
    Dict[str, List[str]]
        A dictionary with virtual network names as keys and lists of subnet names as values.
    
    Raises
    ------
    azure.core.exceptions.HttpResponseError
        If the request to the Azure API fails.
    """
    network_client = NetworkManagementClient(credential, subscription_id)
    
    subnets_dict = {}
    for vnet in network_client.virtual_networks.list_all():
        subnets = []
        for subnet in network_client.subnets.list(resource_group_name=vnet.id.split('/')[4], virtual_network_name=vnet.name):
            subnets.append(subnet.as_dict())
        subnets_dict[vnet.name] = subnets
    
    return subnets_dict



def parse_subnets(subnets: List[Dict[str, List[Dict[str, str]]]]) -> pd.DataFrame:
    """
    Convert a list of dictionaries containing subnets to a Pandas DataFrame.
    
    Parameters
    ----------
    subnets : List[Dict[str, List[Dict[str, str]]]]
        A list of dictionaries with virtual network names as keys and lists of subnet details as values.
    
    Returns
    -------
    pd.DataFrame
        A DataFrame containing subnet details with an additional 'network_name' column.
    """
    # Flatten the list of dictionaries
    data = []
    for subnet_dict in subnets:
        for network_name, subnet_list in subnet_dict.items():
            for subnet in subnet_list:
                subnet['network_name'] = network_name
                data.append(subnet)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    return df


def get_subscription_ids(credential: DefaultAzureCredential) -> List[str]:
    """
    Retrieve all subscription IDs associated with the authenticated Azure account.
    
    Parameters
    ----------
    credential : DefaultAzureCredential
        The credential object used for authentication.
    
    Returns
    -------
    List[str]
        A list of subscription IDs.
    
    Raises
    ------
    azure.core.exceptions.HttpResponseError
        If the request to the Azure API fails.
    """
    subscription_client = SubscriptionClient(credential)
    
    subscription_ids = []
    for subscription in subscription_client.subscriptions.list():
        subscription_ids.append(subscription.subscription_id)
    
    return subscription_ids

def get_private_ips(subscription_id: str, credential: DefaultAzureCredential) -> List[str]:
    """
    Retrieve all private IP addresses associated with the given subscription ID.
    
    Parameters
    ----------
    subscription_id : str
        The Azure subscription ID.
    credential : DefaultAzureCredential
        The credential object used for authentication.
    
    Returns
    -------
    List[str]
        A list of private IP addresses.
    
    Raises
    ------
    azure.core.exceptions.HttpResponseError
        If the request to the Azure API fails.
    """
    network_client = NetworkManagementClient(credential, subscription_id)
    
    private_ips = []
    for nic in network_client.network_interfaces.list_all():
        for ip_config in nic.ip_configurations:
            private_ips.append(ip_config.as_dict())
        # if private_ips:
        #     break
    return private_ips


def parse_public_ips(private_ips: List[Dict[str, any]]) -> pd.DataFrame:
    """
    Convert a list of public IP dictionaries to a Pandas DataFrame.
    
    Parameters
    ----------
    private_ips : List[Dict[str, any]]
        A list of dictionaries containing public IP details.
    
    Returns
    -------
    pd.DataFrame
        A DataFrame containing public IP details.
    """
    # Create DataFrame
    df = pd.DataFrame(private_ips)
    
    return df


def get_public_ips(subscription_id: str, credential: DefaultAzureCredential) -> List[str]:
    """
    Retrieve all public IP addresses associated with the given subscription ID.
    
    Parameters
    ----------
    subscription_id : str
        The Azure subscription ID.
    credential : DefaultAzureCredential
        The credential object used for authentication.
    
    Returns
    -------
    List[str]
        A list of public IP addresses.
    
    Raises
    ------
    azure.core.exceptions.HttpResponseError
        If the request to the Azure API fails.
    """
    network_client = NetworkManagementClient(credential, subscription_id)
    
    public_ips = []
    for ip in network_client.public_ip_addresses.list_all():
        if ip.ip_address:
            public_ips.append(ip.as_dict())
        # if public_ips:
        #     break
    return public_ips


def parse_public_ips(public_ips: List[Dict[str, any]]) -> pd.DataFrame:
    """
    Convert a list of public IP dictionaries to a Pandas DataFrame.
    
    Parameters
    ----------
    public_ips : List[Dict[str, any]]
        A list of dictionaries containing public IP details.
    
    Returns
    -------
    pd.DataFrame
        A DataFrame containing public IP details.
    """
    # Create DataFrame
    df = pd.DataFrame(public_ips)
    
    return df


def fetch_subscription_data(sub: str, credential: DefaultAzureCredential) -> Dict[str, List[str]]:
    data = {
        "subscription_id": sub,
        "private_ips": [],
        "public_ips": [],
        "subnets": {}
    }
    try:
        data["private_ips"] = get_private_ips(sub, credential)
    except Exception as e:
        logger.warning(f"An error occurred while fetching private IPs for subscription {sub}: {e}")

    try:
        data["public_ips"] = get_public_ips(sub, credential)
    except Exception as e:
        logger.warning(f"An error occurred while fetching public IPs for subscription {sub}: {e}")

    try:
        data["subnets"] = get_subnets(sub, credential)
    except Exception as e:
        logger.warning(f"An error occurred while fetching subnets for subscription {sub}: {e}")

    return data


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


def save_collector(
    df, logger, db_path, db_table, excluded_columns
):
    """
    Collects data from ACI site using the specified collector function and stores it in the database.

    Args:
        logger (logging.Logger): Logger instance for logging messages.
        config (AppConfig): Configuration object containing ACI site details and database path.
        site (str): Name of the ACI site.
        params (dict): Dictionary containing site parameters including APIC URLs and tokens.
        collector_func (function): Function to collect data from the ACI site.
        db_table (str): Name of the database table to store the collected data.
        excluded_columns (list): List of columns to exclude from the database index.

    Returns:
        None
    """
    timestamp = hp.set_db_timestamp()
    if not df.empty:
        id_cols = [_ for _ in df.columns.to_list() if _ not in excluded_columns]
        logger.info(f"table: {db_table}, records: {df.shape}")
        store_results_in_db(
            df, db_path, db_table, timestamp, id_cols
        )


# Function to get CIDR based on matching the IP address to a subnet
def get_cidr_for_ip(ip_address, subnets_df):
    for _, row in subnets_df.iterrows():
        network = ipaddress.ip_network(row['address_prefix'])
        if ipaddress.ip_address(ip_address) in network:
            return row['address_prefix'].split('/')[-1]
    return None

def main():
    credential = get_azure_default_credential()
    db_path = os.path.expanduser(os.environ["database_path"])
    database_name = os.environ["database_name"]
    database_full_path = f'{db_path}/{database_name}'
    # logging.basicConfig(level=logging.INFO)

    # Example usage
    private_ips = list()
    public_ips = list()
    subnets = list()

    try:
        subs = get_subscription_ids(credential)
        # subs = subs[:5]
        logger.info(f"Subscription IDs: {subs}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_sub = {executor.submit(fetch_subscription_data, sub, credential): sub for sub in subs}
            for future in concurrent.futures.as_completed(future_to_sub):
                sub = future_to_sub[future]
                try:
                    data = future.result()
                    private_ips.extend(data["private_ips"])
                    public_ips.extend(data["public_ips"])
                    subnets.append(data["subnets"])
                    logger.info(f"Finished fetching data for subscription {sub}")

                except Exception as e:
                    logger.warning(f"An error occurred while processing subscription {sub}: {e}")
            subnets_df = parse_subnets(subnets)
            save_collector(
                subnets_df, logger, database_full_path,
                "AZURE_IPAM_SUBNETS", []
            )
            public_ips_df = parse_public_ips(public_ips)
            private_ips_df = parse_public_ips(private_ips)
            # Creating a dictionary for subnet id to CIDR mapping
            subnet_dict = {k: v.split('/')[-1] for k, v in subnets_df.set_index('id')['address_prefix'].to_dict().items()}

            # Adding the CIDR to the private_ips_df based on subnet
            private_ips_df['cidr'] = private_ips_df['private_ip_address'].apply(lambda x: get_cidr_for_ip(x, subnets_df))

            save_collector(
                private_ips_df, logger, database_full_path,
                "AZURE_IPAM_PRIVATE_IPS", []
            )

            # Adding the CIDR to the public_ips_df based on subnet
            public_ips_df['cidr'] = public_ips_df['ip_address'].apply(lambda x: get_cidr_for_ip(x, subnets_df))

            save_collector(
                public_ips_df, logger, database_full_path,
                "AZURE_IPAM_PUBLIC_IPS", []
            )


    except Exception as e:
        logger.warning(f"An error occurred while fetching subscription IDs: {e}")

if __name__ == "__main__":
    main()

