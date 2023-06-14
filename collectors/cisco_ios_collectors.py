#!/usr/bin/env python3

import ansible_runner
import pandas as pd


def get_vrfs(username: str,
             password: str,
             host_group: str,
             play_path: str,
             private_data_dir: str) -> pd.DataFrame:
    """Retrieve VRF information and return it as a DataFrame.

    Parameters
    ----------
    username : str
        The username to use for authentication.
    password : str
        The password to use for authentication.
    host_group : str
        The host group to query for VRF information.
    play_path : str
        The path to playbooks in Ansible.
    private_data_dir : str
        The path to private data directories in Ansible.

    Returns
    -------
    pandas.DataFrame
        A DataFrame containing VRF information, with columns ["device", "name",
        "vrf_id", "default_rd", "default_vpn_id"].
    """
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
