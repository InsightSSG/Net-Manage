#!/usr/bin/env python3

import ansible_runner
from netmiko import ConnectHandler
from typing import List


def nxos_create_vrf(device_ip: str,
                    username: str,
                    password: str,
                    vrf_name: str,
                    vrf_rd: str,
                    vrf_rt: str,
                    interfaces: List[str]) -> str:
    """
    Creates a VRF on a Cisco Nexus device and assigns interfaces to it.

    Parameters:
    device_ip (str): The IP address of the Cisco Nexus device.
    username (str): The SSH username for the device.
    password (str): The SSH password for the device.
    vrf_name (str): The name of the VRF to create.
    vrf_rd (str): The VRF route distinguisher.
    vrf_rt (str): The VRF route target.
    interfaces (List[str]): A list of interface names to assign to the VRF.

    Returns:
    str: The response output from configuring the device.

    Examples:
    >>> output = create_vrf_on_nexus('192.168.1.1',
                                     'admin',
                                     'password',
                                     'my_vrf',
                                     '100:1',
                                     '100:1',
                                     ['ethernet1/1', 'ethernet1/2'])
    """
    # Define the device credentials and connection settings
    nexus_device = {
                   'device_type': 'cisco_nxos',
                   'ip': device_ip,
                   'username': username,
                   'password': password
                    }

    # Create a Netmiko SSH connection to the device
    try:
        net_connect = ConnectHandler(**nexus_device)
    except Exception as e:
        print(f"Connection error: {e}")
        return

    # Send the commands to create the VRF
    create_vrf_commands = [
                          "config terminal",
                          f"vrf context {vrf_name}",
                          f"rd {vrf_rd}",
                          f"import route-target {vrf_rt}",
                          f"export route-target {vrf_rt}",
                          "exit",
                          f"interface {','.join(interfaces)}",
                          f"vrf member {vrf_name}",
                          "exit"
                          ]
    output = net_connect.send_config_set(create_vrf_commands)

    # Close the SSH connection to the device
    net_connect.disconnect()

    return output


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
