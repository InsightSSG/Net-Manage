from netmiko import ConnectHandler
from typing import List


def create_vrf_on_nexus(device_ip: str,
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
