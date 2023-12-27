"""
This script uses the Azure SDK for Python to query Azure Resource Graph for
network information.

It retrieves network interfaces and associated virtual networks and subnets
across all subscriptions accessible to the user. The output can be saved to a
CSV file and optionally printed to the console.
"""

import argparse
import pandas as pd
import re
from typing import List, Dict
from azure.identity import InteractiveBrowserCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.resourcegraph.models import QueryRequest


def get_subscription_ids(credential) -> List[str]:
    """
    Retrieve a list of subscription IDs accessible with the provided
    credentials.

    Parameters
    ----------
    credential : azure.identity.InteractiveBrowserCredential
        Azure credentials used for authentication.

    Returns
    -------
    List[str]
        A list of subscription IDs.
    """
    subscription_client = SubscriptionClient(credential)
    return [subscription.subscription_id for subscription in
            subscription_client.subscriptions.list()]


def execute_resource_graph_query(credential,
                                 subscription_ids: List[str],
                                 query: str) -> List[Dict]:
    """
    Execute a query against the Azure Resource Graph.

    Parameters
    ----------
    credential : azure.identity.InteractiveBrowserCredential
        Azure credentials used for authentication.
    subscription_ids : List[str]
        List of subscription IDs to query against.
    query : str
        The query string to execute.

    Returns
    -------
    List[Dict]
        A list of dictionaries containing the query results.
    """
    resource_graph_client = ResourceGraphClient(credential)
    request_options = QueryRequest(query=query, subscriptions=subscription_ids)
    response = resource_graph_client.resources(request_options)
    return response.data if response.data else []


def save_to_csv(df, file_path: str):
    """
    Saves the DataFrame to a CSV file.

    Args:
    df (DataFrame): The Pandas DataFrame to save.
    file_path (str): The path to the CSV file where the DataFrame will be saved.
    """
    df.to_csv(file_path, index=False)


def remove_prefix(text, pattern=r'/subscriptions/[^/]+/resourceGroups/'):
    """
    Removes the specified prefix from the text.

    Args:
    text (str): The input text from which to remove the prefix.

    Returns:
    str: The text with the prefix removed.
    """
    return re.sub(pattern, '', text)


def process_data_with_pandas(data, subscription_ids):
    df = pd.DataFrame(data)

    # Apply the removal function to each element in the DataFrame
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].map(
                lambda x: remove_prefix(x) if isinstance(x, str) else x)

    # Extract the common prefix and add it as a new column
    common_prefix_pattern = \
        f'/subscriptions/{subscription_ids[0]}/resourceGroups/'
    df.insert(0, 'commonPrefix', common_prefix_pattern)

    return df


def main():
    """
    Main function to handle command line arguments and control the flow of
    the script.
    """

    parser = argparse.ArgumentParser(
        description="Azure Resource Graph Network Query Tool"
    )
    parser.add_argument(
        "--subscription_id",
        required=True,
        help="Initial subscription ID for authentication"
    )
    parser.add_argument("--output",
                        default="output.csv",
                        help="Path to output CSV file"
                        )
    parser.add_argument("--print",
                        action="store_true",
                        help="Print the output to the console"
                        )

    args = parser.parse_args()

    credential = InteractiveBrowserCredential()
    # credential = ClientSecretCredential(tenant_id, client_id, client_secret)
    subscription_ids = get_subscription_ids(credential)

    # Query 1: Network Interfaces
    query_network_interfaces = """
    Resources
    | where type =~ 'microsoft.network/networkinterfaces'
    | extend ipConfigurations = properties.ipConfigurations
    | mvexpand ipConfigurations
    | extend publicIPAddressId = tostring(
        ipConfigurations.properties.publicIPAddress.id)
    | project networkInterfaceId = id,
              subnetId = tostring(ipConfigurations.properties.subnet.id),
              privateIPAddress = tostring(
                ipConfigurations.properties.privateIPAddress),
              privateIPAllocationMethod = tostring(
                ipConfigurations.properties.privateIPAllocationMethod),
              publicIPAddressId
    """
    network_interfaces_data = execute_resource_graph_query(
        credential,
        subscription_ids,
        query_network_interfaces)

    # Query 2: Virtual Networks
    query_virtual_networks = """
    Resources
    | where type == 'microsoft.network/virtualnetworks'
    | extend subnets = properties.subnets
    | mvexpand subnets
    | project vnetId = id,
                       VNetname = name,
                       SubnetId = tostring(subnets.id),
                       CIDR = subnets.properties.addressPrefix
    """
    virtual_networks_data = execute_resource_graph_query(
        credential,
        subscription_ids,
        query_virtual_networks)

    # Query 3: Public IP Addresses
    query_public_ips = """
    Resources
    | where type contains 'publicIPAddresses' and isnotempty(properties.ipAddress)
    | project publicIPAddressId = id, ipAddress = properties.ipAddress
    """
    public_ips_data = execute_resource_graph_query(
        credential,
        subscription_ids,
        query_public_ips)

    public_ips_dict = {item['publicIPAddressId']: item['ipAddress'] for item in
                       public_ips_data}

    # Join the results based on SubnetId
    joined_data = []
    for interface in network_interfaces_data:
        subnet_id = interface.get('subnetId')
        public_ip_id = interface.get('publicIPAddressId')
        public_ip = public_ips_dict.get(public_ip_id, 'None')
        for network in virtual_networks_data:
            if network.get('SubnetId') == subnet_id:
                joined_data.append(
                    {**interface, **network, 'publicIPAddress': public_ip})

    joined_data_df = process_data_with_pandas(joined_data, subscription_ids)

    save_to_csv(joined_data_df, args.output)

    if args.print:
        for result in joined_data:
            print(f"Network Interface ID: {result['networkInterfaceId']}, "
                  f"Virtual Network: {result['VNetname']}, "
                  f"Subnet: {result['CIDR']}")


if __name__ == "__main__":
    main()
