#!/usr/bin/env python3

"""
A module for executing network commands on devices using Netmiko.

This module provides utility functions that allow for parallel execution
of commands on multiple network devices. It leverages the Netmiko library
for device connections and the concurrent.futures module for multithreading.

Functions:
- execute_commands_on_single_device: Executes commands on a single device.
- execute_commands_on_devices: Executes commands on multiple devices
    concurrently.
"""

from netmiko import ConnectHandler
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Union, Tuple


def execute_commands_on_single_device(device_name: str,
                                      device_data: Dict[str, Union[Dict[str, str], Dict[str, Dict[str, str]]]]) -> Tuple[str, Dict[str, Union[str, Dict[str, str]]]]:  # noqa
    """
    Execute network commands on a single device using Netmiko.

    Parameters
    ----------
    device_name : str
        The name of the device.
    device_data : dict
        The data associated with the device, including credentials,
        device_info, and jobs.

    Returns
    -------
    tuple
        A tuple containing the device name and eutger the results of the
        command execution or an error string.
    """

    credentials = device_data['credentials']
    device_info = device_data['device_info']
    device_ip = device_info.get('device_ip')
    device_type = device_info.get('device_type', 'cisco_ios')

    device = {
        'device_type': device_type,
        'ip': device_ip,
        'username': credentials['username'],
        'password': credentials['password']
    }

    job_results = {}

    try:
        connection = ConnectHandler(**device)

        for job_name, tasks in device_data['jobs'].items():
            task_results = {}
            for task_name, command in tasks.items():
                try:
                    result = connection.send_command(command)
                    task_results[task_name] = result
                except Exception as e:
                    task_results[task_name] =\
                        f"Error executing command '{command}': {str(e)}"
            job_results[job_name] = task_results

        connection.disconnect()
        return device_name, job_results
    except Exception as e:
        return device_name, \
            f"Error connecting to device '{device_name}': {str(e)}"


def execute_commands_on_devices(devices: Dict[str, Dict[str, Union[Dict[str, str], Dict[str, Dict[str, str]]]]]) -> Tuple[Dict[str, Dict[str, Union[str, Dict[str, str]]]], Dict[str, str]]:  # noqa
    """
    Execute network commands on multiple devices concurrently using Netmiko.

    Parameters
    ----------
    devices : dict
        A dictionary containing device names as keys and their associated data
        as values.

    Returns
    -------
    tuple
        A tuple containing two dictionaries:
        1. A dictionary with the device names as keys and the results of the
           command execution as values.
        2. A dictionary with the device names that Netmiko couldn't connect to
           as keys and the accompanying error as values.
    """

    results = {}
    connection_errors = {}

    with ThreadPoolExecutor() as executor:
        future_to_device = {
            executor.submit(
                execute_commands_on_single_device,
                device_name,
                device_data):
            device_name for device_name, device_data in devices.items()}

        for future in as_completed(future_to_device):
            device_name = future_to_device[future]
            try:
                device_name, outcome = future.result()
                if isinstance(outcome, dict):
                    results[device_name] = outcome
                else:
                    connection_errors[device_name] = outcome
            except Exception as e:
                connection_errors[device_name] = \
                    f"Unexpected error with device '{device_name}': {str(e)}"

    return results, connection_errors
