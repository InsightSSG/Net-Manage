#!/usr/bin/env python3

import argparse
import os
import sys
sys.path.append(os.path.expanduser('~/source/repos/InsightSSG/Net-Manage'))  # noqa
from netmanage.collectors.solarwinds_collectors import get_npm_node_ips  # noqa
from netmanage.collectors.solarwinds_collectors import get_npm_node_machine_types  # noqa
from netmanage.helpers.solarwinds_helpers import map_machine_type_to_ansible_os  # noqa


def custom_yaml_dump(data, indent=0):
    lines = []
    indent_space = '  ' * indent

    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{indent_space}{key}:")
            lines.extend(custom_yaml_dump(value, indent + 1))
        else:
            lines.append(f"{indent_space}{key}: {value}")
    return lines


def main(args):
    # Get node machine types.
    df = get_npm_node_machine_types(args.server,
                                    args.username,
                                    args.password)

    # Get the Ansible OS for the machine types.
    ansible_os = list()
    for item in df['machine_type'].to_list():
        ansible_os.append(map_machine_type_to_ansible_os(item))
    df['ansible_os'] = ansible_os

    # Get the node IPs and add them to the DataFrame.
    node_ips = get_npm_node_ips(args.server,
                                args.username,
                                args.password)
    df['ip'] = node_ips['device_ip'].to_list()

    # Drop rows without an ansible_os.
    df = df[df['ansible_os'].str.strip() != '']
    df = df.reset_index(drop=True)

    # Define group names to exclude.
    excluded = ['meraki']

    inventory = {"all_hosts": {}}
    host_groups = {}  # This will temporarily store host names for each group

    for idx, row in df.iterrows():
        if row['ansible_os'] not in excluded:
            inventory['all_hosts'][row['device_name']] = \
                {'ansible_host': row['ip']}
        g_name = str()
        # Create or update top level hosts groups.
        ansible_os = row['ansible_os']
        if 'cisco.ios' in ansible_os:
            g_name = 'all_cisco_ios'
        if 'cisco.nxos' in ansible_os:
            g_name = 'all_cisco_nxos'
        if 'paloaltonetworks.panos' in ansible_os:
            g_name = 'all_palo_altos'
        if 'cisco.asa' in ansible_os:
            g_name = 'all_cisco_asa'
        if g_name:
            if g_name not in host_groups:
                host_groups[g_name] = set()
            host_groups[g_name].add(row['device_name'])

    # Now, build the final inventory structure using the collected host names
    for g_name, hosts in host_groups.items():
        inventory[g_name] = {
            'hosts': {host: {} for host in hosts},
            'vars': {
                'ansible_become': 'yes',
                'ansible_become_method': 'enable',
                'ansible_network_os': df[df['device_name'] ==
                                         list(hosts)[0]]['ansible_os'].iloc[0],
                'ansible_username': '"{{ username }}"',
                'ansible_password': '"{{ password }}"'
            }
        }

    # Check if the file already exists, and take appropriate action.
    if os.path.exists(args.file) and not args.overwrite:
        print(f"Error: The file {args.file} already exists. Use the --overwrite option to overwrite it.")  # noqa
        sys.exit(1)

    # Write the output to the hosts file.
    with open(os.path.expanduser(args.file), "w") as f:
        f.write('---\n')

        # Modify the all_hosts structure to include the "hosts" key
        all_devices_structure = {"all_devices":
                                 {"hosts": inventory["all_hosts"]}}

        # Dump all hosts
        f.write('\n'.join(custom_yaml_dump(all_devices_structure, indent=1)))
        f.write('\n\n')

        # Dump the host groups
        for group, data in inventory.items():
            if group != "all_hosts":
                f.write('\n'.join(custom_yaml_dump({group: data}, indent=1)))
                f.write('\n\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Ansible inventory from Solarwinds NPM")
    parser.add_argument('-f',
                        '--file',
                        required=True,
                        help='The full path to save the file to.')
    parser.add_argument('-s',
                        '--server',
                        required=True,
                        help='The hostname or IP address of the Orion server.')
    parser.add_argument('-u',
                        '--username',
                        required=True,
                        help='The username to use for authentication.')
    parser.add_argument('-p',
                        '--password',
                        required=True,
                        help='The password to use for authentication.')
    parser.add_argument('-o',
                        '--overwrite',
                        action='store_true',
                        help='Overwrite the file if it already exists.')

    args = parser.parse_args()
    main(args)

    print(f"Ansible inventory saved to {args.file}.")
