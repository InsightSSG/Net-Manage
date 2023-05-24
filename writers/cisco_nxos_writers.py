#!/usr/bin/env python3

import ansible_runner


def nxos_create_vlan(vlan_id: str,
                     vlan_name: str,
                     enabled: bool,
                     host_group: str,
                     play_path: str,
                     private_data_dir: str,
                     username: str,
                     password: str,
                     state: str = 'merged') -> str:
    """
    This function is used to enable or disable a feature on a Cisco Nexus.

    Parameters
    ----------
    vlan_id : str
        The VLAN ID.
    vlan_name : str
        The VLAN name.
    enabled : bool
        Whether the VLAN should be enabled (True) or disabled (False).
    host_group : str
        The host group for which to modify the feature.
    play_path : str
        The path to netManage playbooks.
    private_data_dir : str
        The path to the Ansible private data directory.
    username : str
        The username for the switch login.
    password : str
        The password for the switch login.
    state : str
        Whether the VLAN config should be merged or replaced (default is
        merged).

    Returns
    -------
    summary : dict
        A dictionary containing the task results for each host.
    """
    if state not in ['merged', 'replaced']:
        raise ValueError('Incorrect state. Choose "merged" or "replaced".')
        return None

    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'vlan_id': vlan_id,
                 'vlan_name': vlan_name,
                 'state': state,
                 'enabled': enabled}

    playbook = f'{play_path}/rw_cisco_nxos_create_vlan.yml'

    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    summary = dict()
    for host_event in runner.events:
        if host_event['event'] == 'runner_on_ok':
            host = host_event['event_data']['host']
            task = host_event['event_data']['task']
            result = host_event['event_data']['res']
            if not summary.get(host):
                summary[host] = dict()
            summary[host][task] = dict()
            summary[host][task]['result'] = result

    return summary


def nxos_create_vrf(vrf_name: str,
                    description: str,
                    host_group: str,
                    play_path: str,
                    private_data_dir: str,
                    username: str,
                    password: str) -> str:
    """
    This function is used to enable or disable a feature on a Cisco Nexus.

    Parameters
    ----------
    vrf_name : str
        The VRF name
    description : str
        The VRF description.
    host_group : str
        The host group for which to modify the feature.
    play_path : str
        The path to netManage playbooks.
    private_data_dir : str
        The path to the Ansible private data directory.
    username : str
        The username for the switch login.
    password : str
        The password for the switch login.

    Returns
    -------
    summary : dict
        A dictionary containing the task results for each host.
    """
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'vrf_name': vrf_name,
                 'description': description}

    playbook = f'{play_path}/rw_cisco_nxos_create_vrf.yml'

    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    summary = dict()
    for host_event in runner.events:
        if host_event['event'] == 'runner_on_ok':
            host = host_event['event_data']['host']
            task = host_event['event_data']['task']
            result = host_event['event_data']['res']
            if not summary.get(host):
                summary[host] = dict()
            summary[host][task] = dict()
            summary[host][task]['result'] = result

    return summary


def nxos_delete_vrf(vrf_name: str,
                    host_group: str,
                    play_path: str,
                    private_data_dir: str,
                    username: str,
                    password: str) -> str:
    """
    This function is used to enable or disable a feature on a Cisco Nexus.

    Parameters
    ----------
    vrf_name : str
        The VRF name
    host_group : str
        The host group for which to modify the feature.
    play_path : str
        The path to netManage playbooks.
    private_data_dir : str
        The path to the Ansible private data directory.
    username : str
        The username for the switch login.
    password : str
        The password for the switch login.

    Returns
    -------
    summary : dict
        A dictionary containing the task results for each host.
    """
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'vrf_name': vrf_name}

    playbook = f'{play_path}/rw_cisco_nxos_delete_vrf.yml'

    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    summary = dict()
    for host_event in runner.events:
        if host_event['event'] == 'runner_on_ok':
            host = host_event['event_data']['host']
            task = host_event['event_data']['task']
            result = host_event['event_data']['res']
            if not summary.get(host):
                summary[host] = dict()
            summary[host][task] = dict()
            summary[host][task]['result'] = result

    return summary


def nxos_toggle_feature(feature_name: str,
                        host_group: str,
                        play_path: str,
                        private_data_dir: str,
                        state: bool,
                        username: str,
                        password: str) -> str:
    """
    This function is used to enable or disable a feature on a Cisco Nexus.

    Parameters
    ----------
    feature : str
        The name of the feature to enable or disable.
    state : bool
        A boolean indicating whether the feature should be enabled (True) or
        disabled (False).
    host_group : str
        The host group for which to modify the feature.
    play_path : str
        The path to netManage playbooks.
    private_data_dir : str
        The path to the Ansible private data directory.
    username : str
        The username for the switch login.
    password : str
        The password for the switch login.

    Returns
    -------
    summary : dict
        A dictionary containing the task results for each host.
    """
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'feature_name': feature_name,
                 'state': state}

    playbook = f'{play_path}/rw_cisco_nxos_toggle_feature.yml'

    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    summary = dict()
    for host_event in runner.events:
        if host_event['event'] == 'runner_on_ok':
            host = host_event['event_data']['host']
            task = host_event['event_data']['task']
            result = host_event['event_data']['res']
            if not summary.get(host):
                summary[host] = dict()
            summary[host][task] = dict()
            summary[host][task]['result'] = result

    return summary
