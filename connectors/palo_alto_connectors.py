#!/usr/bin/env python3

import ansible_runner
import json


def get_arp_table(username,
                  password,
                  host_group,
                  play_path,
                  private_data_dir,
                  interface=str()):
    """Gets the ARP table from one or more Palo Alto firewalls.

    Parameters
    ----------
    username : str
        The user's username.
    password : str
        The user's password.
    host_group : str
        The name of the Ansible inventory host group.
    play_path : str
        The path to the directory containing Ansible playbooks
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    ----------
    result : dict
        A dictionary containing the ARP table, where the keys are devices
        and the value is a dictionary containing the ARP table.

    Other Parameters
    ----------
    interface: str
        The interface for which to return the ARP table. The default is to
        return the ARP table for all interfaces.

    Examples
    ----------
    >>> (write examples)
    """
    if interface:
        cmd = f'show arp {interface}'
        cmd = f"<show><arp><entry name='{interface}'/></arp></show>"
    else:
        cmd = "<show><arp><entry name='all'/></arp></show>"
    extravars = {'user': username,
                 'password': password,
                 'host_group': host_group,
                 'command': cmd}

    playbook = f'{play_path}/palo_alto_get_arp_table.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Create a dictionary for storing the output by device name
    result = dict()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']
            output = event_data['res']['stdout']

            output = json.loads(output)
            if output['response']['result'].get('entries'):
                output = output['response']['result']['entries']['entry']
                result[device] = output

    return result
