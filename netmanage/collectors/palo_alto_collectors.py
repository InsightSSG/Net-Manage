#!/usr/bin/env python3

import requests
import json
import os
from xml.etree import ElementTree
import pandas as pd
import yaml
from dotenv import load_dotenv
from netmanage.parsers import palo_alto_parsers as parser

# Load variables from .env
load_dotenv()
api_ver = 'v10.2'
nm_path = os.getenv('netmanage_path')


def generate_api_key(firewall: str,
                     username: str,
                     password: str):
    """
    Generate an API key for PAN-OS firewall.

    Parameters
    ----------

    - firewall : str
        The hostname or IP address of the firewall.
    - username : str
        The administrative username.
    - password : str
        The administrative password.

    Returns
    -------
    str
        The generated API key or None if an error occurs.

    """

    # Construct the URL
    url = f"https://{firewall}/api/?type=keygen&user=" \
          f"{username}&password={password}"

    try:
        response = requests.get(url, verify=False)

        # Parse the XML response
        root = ElementTree.fromstring(response.content)
        status = root.attrib.get('status')

        if status == 'success':
            api_key = root.find(".//key").text
            return api_key
        else:
            return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None


def get_firewall_hostname(firewall: str,
                          api_key: str) -> str:
    """
    Get the hostname of a Palo Alto firewall using the PAN-OS API.

    Parameters
    ----------
    firewall : str
        The hostname or IP address of the firewall.
    api_key : str
        The API key for the firewall.

    Returns
    -------
    str
        The hostname of the firewall. Returns None if an error occurs.
    """

    # Construct the URL to retrieve system info
    cmd = "<show><system><info></info></system></show>"
    url = f"https://{firewall}/api/?type=op&cmd={cmd}&key={api_key}"

    try:
        response = requests.get(url, verify=False)

        # Parse the XML response
        root = ElementTree.fromstring(response.content)
        status = root.attrib.get('status')

        if status == 'success':
            hostname = root.find(".//result/system/hostname").text
            return hostname
        else:
            return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None


def get_credentials(firewall, api_key=None, username=None, password=None):
    if api_key:
        return api_key
    else:
        # Logic to retrieve stored API Key
        stored_api_key = None  # TODO: Add Function to retrieve Stored API Key
        if stored_api_key:
            return stored_api_key
        elif username and password:
            return generate_api_key(firewall, username, password)
        else:
            raise ValueError("No credentials provided or stored.")


def get_vsys_list(firewall: str,
                  api_key: str) -> pd.DataFrame:
    """
    Retrieves a list of virtual systems (vsys) and their display names from a
    Palo Alto firewall.

    Parameters
    ----------
    firewall : str
        The hostname or IP address of the firewall.
    api_key : str
        The generated API key for authentication.

    Returns
    -------
    pd.DataFrame
        A DataFrame with columns ['vsys_name', 'display_name'].
    """

    # Construct the URL to retrieve vsys list
    url = f"https://{firewall}/restapi/{api_ver}/Device/VirtualSystems"

    headers = {
        'X-PAN-KEY': api_key
    }

    vsys_info = []
    hostname = get_firewall_hostname(firewall, api_key=api_key)
    try:
        response = requests.get(url, headers=headers, verify=False)

        # Check for a valid response
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            return None

        # Parse the JSON response
        response_json = response.json()

        if response_json.get('@status') == 'success':
            entries = response_json.get('result', {}).get('entry', [])
            for entry in entries:
                vsys_name = entry.get('@name')
                display_name = entry.get('display-name')
                vsys_info.append((vsys_name, display_name, hostname, firewall))
        else:
            print(f"Error: {response_json.get('@status')}")
            return None

    except Exception as e:
        print(f"Error occurred while fetching vsys info: {e}")
        return None

    if vsys_info:
        df_vsys_info = pd.DataFrame(vsys_info,
                                    columns=['vsys_name',
                                             'display_name',
                                             'hostname',
                                             'device'])
        return df_vsys_info
    else:
        return pd.DataFrame(columns=['vsys_name',
                                     'display_name',
                                     'hostname',
                                     'device'])


def set_vsys_context(api_key: str, firewall: str, vsys: str):
    cmd = f"<set><system><setting><target-vsys>{vsys}</target-vsys></setting></system></set>" # noqa
    url = f"https://{firewall}/api/?key={api_key}&type=config&action=set&element={requests.utils.quote(cmd)}" # noqa
    response = requests.get(url, verify=False)
    response.raise_for_status()


def inventory(firewall: str,
              api_key: str) -> pd.DataFrame:
    """
    Retrieve system information (inventory) from PAN-OS firewall using the
    API and parse it into a DataFrame.

    Parameters
    ----------
    firewall : str
        The hostname or IP address of the firewall.
    api_key : str
        The generated API key for authentication.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the system information.
    """

    # Construct the URL for system info retrieval
    cmd = "<show><system><info></info></system></show>"
    url = f"https://{firewall}/api/?type=op&cmd={cmd}&key={api_key}"

    try:
        response = requests.get(url, verify=False)

        # Parse the XML response
        root = ElementTree.fromstring(response.content)
        status = root.attrib.get('status')

        if status == 'success':
            system_info = {}
            for child in root.find(".//result/system"):
                system_info[child.tag] = child.text
            # Parse the inventory data using the 'parse_inventory' function
            return parser.parse_inventory({firewall: system_info})
        else:
            return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None


def bgp_neighbors(firewall: str,
                  api_key: str) -> pd.DataFrame:
    """
    Gets BGP neighbors for Palo Alto firewalls using the PAN-OS API.

    Parameters
    ----------
    firewall : str
        The hostname or IP address of the firewall.
    api_key : str
        The API key for authentication.

    Returns
    -------
    df : Pandas Dataframe
        A dataframe containing the BGP neighbors.

    Examples
    --------
    # ... your examples ...

    Raises
    ------
    ValueError
        If neither api_key nor both username and password are provided.
    """

    # Construct the URL to send the command
    cmd = "<show><routing><protocol><bgp><peer></peer></bgp></protocol></routing></show>" # noqa
    url = f"https://{firewall}/api/?type=op&cmd={cmd}&key={api_key}"

    try:
        test_response = requests.get(url, verify=False)
        if 'Command deprecated in Advanced Routing Mode' in test_response.text:
            cmd = "<show><advanced-routing><bgp><peer><status></status></peer></bgp></advanced-routing></show>" # noqa
            url = f"https://{firewall}/api/?type=op&cmd={cmd}&key={api_key}"
            response = requests.get(url, verify=False)

        else:
            cmd = "<show><routing><protocol><bgp><peer><status></status></peer></bgp></protocol></routing></show>"  # noqa
            url = f"https://{firewall}/api/?type=op&cmd={cmd}&key={api_key}"
            response = requests.get(url, verify=False)

        root = ElementTree.fromstring(response.content)
        json_data = root.find(".//json").text
        response_dict = json.loads(json_data)

        # Pass the parsed JSON directly to the parser function
        return parser.parse_bgp_neighbors({firewall: response_dict})

    except Exception as e:
        print(f"Error: {e}")
        return None


def get_arp_table(firewall: str,
                  api_key: str,
                  interface: str = '',
                  vsys: str = None) -> pd.DataFrame:
    """
    Parses the Palo Alto ARP table and adds vendor OUIs.

    Parameters
    ----------
    firewall : str
        The hostname or IP address of the firewall.
    api_key : str
        The API key for the firewall.
    interface : str, optional
        The interface for which to return the ARP table. The default is to
        return the ARP table for all interfaces.
    vsys : str, optional
        The virtual system for which to return the ARP table. The default is to
        return the ARP table for all systems.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the ARP table and vendor OUIs.
    """

    hostname = get_firewall_hostname(firewall, api_key=api_key)
    if not hostname:
        print("Error retrieving hostname.")
        return pd.DataFrame()  # Return an empty DataFrame on error

    # Construct the URL and command for the ARP table request
    if interface:
        cmd = f"<show><arp><entry name='{interface}'/></arp></show>"
    else:
        cmd = "<show><arp><entry name='all'/></arp></show>"

    url = f"https://{firewall}/api/?type=op&cmd={cmd}&key={api_key}"

    # Set the vsys context if specified
    if vsys:
        vsys_cmd = f"<set><system><setting><target-vsys>{vsys}</target-vsys></setting></system></set>" # noqa
        vsys_url = f"https://{firewall}/api/?type=op&cmd={vsys_cmd}&key={api_key}" # noqa
        vsys_response = requests.post(vsys_url, verify=False)
        if vsys_response.status_code != 200:
            print(f"Error setting vsys context: {vsys_response.content}")
            return pd.DataFrame()  # Return an empty DataFrame on error

    # Send the request for the ARP table
    response = requests.get(url, verify=False)
    if response.status_code != 200:
        print(f"Error fetching ARP table: {response.content}")
        return pd.DataFrame()  # Return an empty DataFrame on error

    # Parse the XML response to a dict
    root = ElementTree.fromstring(response.content)
    response_dict = {hostname: {'event_data': {'res': {'stdout': ElementTree.tostring(root, encoding='utf-8').decode()}}}} # noqa
    # Parse the response dict to a DataFrame
    return parser.parse_arp_table(response_dict, nm_path)


def get_logical_interfaces(firewall: str,
                           api_key: str) -> pd.DataFrame:
    """
    Gets the logical interfaces on Palo Altos using the PAN-OS API.

    Parameters
    ----------
    firewall : str
        The hostname or IP address of the firewall.
    api_key : str
        The API key for the firewall.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the logical interfaces.
    """

    # Construct the URL for logical interfaces retrieval
    cmd = "<show><interface>logical</interface></show>"
    url = f"https://{firewall}/api/?type=op&cmd={cmd}&key={api_key}"

    try:
        response = requests.get(url, verify=False)

        # Parse the XML response
        root = ElementTree.fromstring(response.content)
        status = root.attrib.get('status')

        if status == 'success':
            # Parse the logical interfaces data using the
            return parser.parse_logical_interfaces(
                {firewall: root.find(".//result/ifnet")})
        else:
            return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None


def get_physical_interfaces(firewall: str,
                            api_key: str) -> pd.DataFrame:
    """
    Gets the physical interfaces on Palo Altos using the PAN-OS API.

    Parameters
    ----------
    firewall : str
        The hostname or IP address of the firewall.
    api_key : str
        The API key for the firewall.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the physical interfaces.
    """

    # Construct the URL for physical interfaces retrieval
    url = f"https://{firewall}/restapi/{api_ver}/Network/EthernetInterfaces"
    headers = {'X-PAN-KEY': api_key}

    try:
        response = requests.get(url, headers=headers, verify=False)
        response_json = response.json()

        if response.status_code == 200 and response_json["@status"] == "success":
            # Preparing data for the parser
            entries = response_json["result"]["entry"]
            response_dict = {firewall: entries}

            # Parsing the data
            return parser.parse_physical_interfaces(response_dict)
        else:
            print(f"Error: {response_json.get('@code', 'Unknown error code')}")
            return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None


def get_security_rules(firewall: str,
                       api_key: str,
                       vsys: str = None) -> pd.DataFrame:
    '''
    Gets the security rules on Palo Alto firewall using the REST API.

    Parameters
    ----------
    firewall : str
        The hostname or IP address of the firewall.
    api_key : str
        The API key for the firewall.
    vsys : str, optional
        The virtual system identifier.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing the security rules.
    '''

    # Define the endpoint URL with query parameters for vsys and location
    if vsys is None:
        url = f"https://{firewall}/restapi/{api_ver}/Policies/SecurityRules?location=vsys&vsys=vsys1" # noqa
    else:
        url = f"https://{firewall}/restapi/{api_ver}/Policies/SecurityRules?location=vsys&vsys={vsys}" # noqa

    # Define the headers for authentication
    headers = {
        'X-PAN-KEY': api_key
    }

    hostname = get_firewall_hostname(firewall, api_key=api_key)

    try:
        # Send the request to the endpoint
        response = requests.get(url, headers=headers, verify=False)

        # Check for a successful response
        if response.status_code == 200:
            # Parse the JSON response
            rules_data = response.json().get('result', {}).get('entry', [])

            # Extract relevant data and create a DataFrame
            rules_list = []
            for rule in rules_data:
                rule_dict = {
                    'Name': rule.get('@name'),
                    'UUID': rule.get('@uuid'),
                    'Location': rule.get('@location'),
                    'Vsys': rule.get('@vsys'),
                    'To': ', '.join(rule.get('to', {}).get('member', [])),
                    'From': ', '.join(rule.get('from', {}).get('member', [])),
                    'Source': ', '.join(rule.get('source', {}).get('member', [])),
                    'Destination': ', '.join(rule.get('destination', {}).get('member', [])),
                    'Action': rule.get('action'),
                    'Source User': ', '.join(rule.get('source-user', {}).get('member', [])),
                    'Category': ', '.join(rule.get('category', {}).get('member', [])),
                    'Application': ', '.join(rule.get('application', {}).get('member', [])),
                    'Service': ', '.join(rule.get('service', {}).get('member', [])),
                    'Source HIP': ', '.join(rule.get('source-hip', {}).get('member', [])),
                    'Destination HIP': ', '.join(rule.get('destination-hip', {}).get('member', [])),
                    'Hostname': hostname,
                    'Device': firewall,
                }
                rules_list.append(rule_dict)

            df = pd.DataFrame(rules_list)

            return df
        else:
            print(f"Error: Received status code {response.status_code}")
            return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None


def ospf_neighbors(firewall: str,
                   api_key: str) -> pd.DataFrame:
    """
    Gets OSPF neighbors for Palo Alto firewalls using the PAN-OS API.

    Parameters
    ----------
    firewall : str
        The hostname or IP address of the firewall.
    api_key : str
        The API key for authentication. api_key must be provided.

    Returns
    -------
    df : Pandas DataFrame
        A DataFrame containing the OSPF neighbors.

    Raises
    ------
    ValueError
        If neither api_key nor both username and password are provided.

    """

    # Construct the URL to send the command
    cmd = "<show><advanced-routing><ospf><neighbor></neighbor></ospf></advanced-routing></show>"  # noqa
    url = f"https://{firewall}/api/?type=op&cmd={cmd}&key={api_key}"

    try:
        response = requests.get(url, verify=False)
        # Check for a valid response
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            return None

        root = ElementTree.fromstring(response.content)
        json_data = root.find(".//json").text
        response_dict = json.loads(json_data)

        # Pass the parsed JSON directly to the parser function
        return parser.parse_ospf_neighbors({firewall: response_dict})

    except Exception as e:
        print(f"Error: {e}")
        return None


collector_mapping = {
    'get_vsys_list': get_vsys_list,
    'ospf_neighbors': ospf_neighbors,
    'get_security_rules': get_security_rules,
    'get_physical_interfaces': get_physical_interfaces,
    'get_logical_interfaces': get_logical_interfaces,
    'get_arp_table': get_arp_table,
    'bgp_neighbors': bgp_neighbors,
    'inventory': inventory,
}


def parse_ansible_hosts(hosts_file_path, host_groups):
    # Read the YAML file
    with open(hosts_file_path, 'r') as stream:
        try:
            pa_inventory = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return None

    # Get username and password from environment variables
    username = os.getenv('palo_alto_username')
    password = os.getenv('palo_alto_password')

    # Initialize a list to hold all host variables for the specified groups
    all_host_vars = []

    # Go through each specified group
    for group_name in host_groups:
        # Check if the group_name is in the inventory
        if group_name not in pa_inventory:
            print(f"Group {group_name} not found in inventory.")
            continue

        group_data = pa_inventory[group_name]

        # Get common variables for the group, if they exist
        common_vars = group_data.get('vars', {})
        # Replace placeholders in common_vars
        common_vars['ansible_password'] = common_vars.get('ansible_password','').replace('{{ password }}', password) # noqa
        common_vars['ansible_user'] = common_vars.get('ansible_user','').replace('{{ username }}', username) # noqa

        # Go through each host in the group, if 'hosts' is present
        if 'hosts' in group_data:
            for host_name, host_data in group_data['hosts'].items():
                # Combine host-specific vars with group-level vars
                host_vars = {**common_vars, **host_data}
                host_vars['host_name'] = host_name
                host_vars['group_name'] = group_name
                all_host_vars.append(host_vars)

    # Convert the list of dictionaries to a DataFrame
    return pd.DataFrame(all_host_vars)


def process_single_firewall(firewall,
                            collector_function,
                            api_key=None,
                            username=None,
                            password=None):
    api_key = get_credentials(firewall, api_key, username, password)
    return collector_function(firewall, api_key)


def process_firewalls_from_host_group(host_group,
                                      hosts_file,
                                      collector_function):
    # Parse Ansible hosts file and extract firewall IPs and respective API keys
    firewalls = parse_ansible_hosts(hosts_file, host_group)
    results = []

    for index, row in firewalls.iterrows():
        firewall_ip = row['ansible_host']
        creds = {
            'username': row['ansible_user'],
            'password': row['ansible_password']
        }
        api_key = get_credentials(firewall_ip, **creds)
        result = collector_function(firewall_ip, api_key)
        results.append(result)

    return pd.concat(results)


def palo_collector(collector_function_name,
                   firewall=None,
                   api_key=None,
                   username=None,
                   password=None,
                   host_group=None,
                   hosts_file=None):
    if collector_function_name not in collector_mapping:
        raise ValueError(f"No such collector function: {collector_function_name}")

    collector_function = collector_mapping[collector_function_name]

    if firewall is not None:
        return process_single_firewall(firewall,
                                       collector_function,
                                       api_key,
                                       username,
                                       password)
    elif host_group is not None and hosts_file is not None:
        return process_firewalls_from_host_group(host_group,
                                                 hosts_file,
                                                 collector_function)
    else:
        raise ValueError("Invalid input provided.")
