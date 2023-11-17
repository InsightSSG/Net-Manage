"""
This script uses the Azure SDK for Python to query Azure Resource Graph for
network information.

It retrieves network interfaces and associated virtual networks and subnets
across all subscriptions accessible to the user. The output can be saved to a
CSV file and optionally printed to the console.
"""

import argparse
import csv
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


def save_to_csv(data: List[Dict], file_path: str):
    """
    Save the provided data to a CSV file.

    Parameters
    ----------
    data : List[Dict]
        Data to be saved.
    file_path : str
        Path of the file where data will be saved.
    """
    keys = data[0].keys() if data else []
    with open(file_path, 'w', newline='') as file:
        dict_writer = csv.DictWriter(file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)


def main():
    """
    Main function to handle command line arguments and control the flow of the
    script.
    """
    parser = argparse.ArgumentParser(
        description="Azure Resource Graph Network Query Tool")
    parser.add_argument("--subscription_id",
                        required=True,
                        help="Initial subscription ID for authentication")
    parser.add_argument("--output",
                        default="output.csv",
                        help="Path to output CSV file")
    parser.add_argument("--print",
                        action="store_true",
                        help="Print the output to the console")

    args = parser.parse_args()

    credential = InteractiveBrowserCredential()

    subscription_ids = get_subscription_ids(credential)

    query = """
    Resources
    | where type =~ 'microsoft.network/networkinterfaces'
    | project id, ipConfigurations = properties.ipConfigurations
    | mvexpand ipConfigurations
    | project id, subnetId = tostring(ipConfigurations.properties.subnet.id)
    | parse kind=regex subnetId with '/virtualNetworks/' virtualNetwork '/subnets/' subnet  # noqa
    | project id, virtualNetwork, subnet
    """

    data = execute_resource_graph_query(credential, subscription_ids, query)

    save_to_csv(data, args.output)

    if args.print:
        for result in data:
            virtual_network = result.get('virtualNetwork', 'Not Found')
            subnet = result.get('subnet', 'Not Found')
            print(f"Virtual Network: {virtual_network}, Subnet: {subnet}")


if __name__ == "__main__":
    main()
