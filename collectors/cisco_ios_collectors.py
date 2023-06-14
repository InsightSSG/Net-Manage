#!/usr/bin/env python3

import ansible_runner
import pandas as pd


def get_vrfs(username,
             password,
             host_group,
             nm_path,
             play_path,
             private_data_dir):
    '''
    Gets the IOS ARP table and adds the vendor OUI.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        nm_path (str):          The path to the Net-Manage repository
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        interface (str):        The interface (defaults to all interfaces)

    Returns:
        df (DataFrame):         The ARP table and vendor OUI
    '''
    cmd = 'show vrf detail | include VRF Id'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_ios_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse the output, create the DataFrame and return it.
    data = []

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0]
            for line in output.strip().split("\n"):
                # Split each line into its name, vrf_id, default_rd, and
                # default_vpn_id components
                name_start = line.find("VRF ") + len("VRF ")
                name_end = line.find(" (VRF Id =")
                name = line[name_start:name_end].strip()

                vrf_id_start = line.find("VRF Id = ") + len("VRF Id = ")
                vrf_id_end = line.find(");")
                vrf_id = line[vrf_id_start:vrf_id_end].strip()

                default_rd = "not set" if "<not set>" in line else None
                default_vpn_id = "not set" if "<not set>" in line else None

                data.append([device, name, vrf_id, default_rd, default_vpn_id])

    # Convert the data to a DataFrame with the appropriate columns
    df = pd.DataFrame(
        data, columns=["device",
                       "name",
                       "vrf_id",
                       "default_rd",
                       "default_vpn_id"])

    return df
