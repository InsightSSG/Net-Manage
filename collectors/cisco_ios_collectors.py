#!/usr/bin/env python3

import ansible_runner
import pandas as pd


def gather_facts(username: str,
                 password: str,
                 host_group: str,
                 play_path: str,
                 private_data_dir: str,
                 gather_info: dict) -> dict:
    """Gathers specified facts on Cisco IOS devices.

    Parameters
    ----------
    username : str
        The username to use for authentication.
    password : str
        The password to use for authentication.
    host_group : str
        The host group for which to gather facts.
    play_path : str
        The path to playbooks in Ansible.
    private_data_dir : str
        The path to private data directories in Ansible.
    gather_info : dict
        A nested dictionary containing either (or both) of the following keys:
        'subset' and/or 'network_subset'. The value of each of those keys is a
        list containing the subset of data to gather. A complete list can be
        found here:
        https://docs.ansible.com/ansible/latest/collections/cisco/ios/ios_facts_module.html

    Returns
    -------
    facts : dict
        A dictionary where each key is a device in the host_group and the value
        is the requested facts.

    Notes
    -------
    If a dictionary is empty then nothing will be returned. This is different
    from the default Ansible behavior. It is done this way to save memory.

    Examples:
    -------
    >>> gather_info = {'subset': ['config']}
    >>> facts = gather_facts(username,
    ...                      password,
    ...                      host_group,
    ...                      play_path,
    ...                      private_data_dir,
    ...                      gather_info)
    >>> for key, value in facts.items():
    >>>     for k, v in value.items():
    >>>         print(k, type(v))
    >>>     break
    >>> ansible_network_resources <class 'dict'>
    >>> ansible_net_gather_network_resources <class 'list'>
    >>> ansible_net_gather_subset <class 'list'>
    >>> ansible_net_config <class 'str'>
    >>> ansible_net_system <class 'str'>
    >>> ansible_net_model <class 'str'>
    >>> ansible_net_image <class 'str'>
    >>> ansible_net_version <class 'str'>
    >>> ansible_net_hostname <class 'str'>
    >>> ansible_net_api <class 'str'>
    >>> ansible_net_python_version <class 'str'>
    >>> ansible_net_iostype <class 'str'>
    >>> ansible_net_operatingmode <class 'str'>
    >>> ansible_net_serialnum <class 'str'>

    >>> gather_info =  {'subset': ['hardware', 'config'],
    ...                 'network_subset': ['hostname', 'snmp_server']}
    >>> facts = gather_facts(username,
    ...                      password,
    ...                      host_group,
    ...                      play_path,
    ...                      private_data_dir,
    ...                      gather_info)
    >>> for key in facts:
    ...     for k in facts[key]['ansible_network_resources']:
    ...         print(k, type(k))
    ...     break

    >>> hostname <class 'str'>
    >>> snmp_server <class 'str'>
    """
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'gather_info': gather_info}

    # Execute the pre-checks
    playbook = f'{play_path}/cisco_ios_gather_facts.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse the output, store it in 'facts', and return it
    facts = dict()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']
            output = event_data['res']['ansible_facts']

            facts[device] = output

    return facts


def get_config(username: str,
               password: str,
               host_group: str,
               play_path: str,
               private_data_dir: str) -> pd.DataFrame:
    """Gets the config on Cisco IOS devices.

    Parameters
    ----------
    username : str
        The username to use for authentication.
    password : str
        The password to use for authentication.
    host_group : str
        The host group for which to gather configs.
    play_path : str
        The path to playbooks in Ansible.
    private_data_dir : str
        The path to private data directories in Ansible.

    Returns
    -------
    df : pandas.DataFrame
        A DataFrame containing the device configurations.
    """
    gather_info = {'subset': ['config']}
    facts = gather_facts(username,
                         password,
                         host_group,
                         play_path,
                         private_data_dir,
                         gather_info)

    configs = dict()
    for key, value in facts.items():
        configs[key] = value['ansible_net_config']

    df = pd.DataFrame(list(configs.items()), columns=['device', 'config'])

    return df


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
