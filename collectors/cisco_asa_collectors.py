#!/usr/bin/env python3

import ansible_runner
import pandas as pd

from helpers import helpers as hp


def get_interface_ips(username: str,
                      password: str,
                      host_group: str,
                      play_path: str,
                      private_data_dir: str) -> pd.DataFrame:
    '''
    Gets the IP addresses assigned to interfaces on Cisco ASA devices.

    Parameters
    ----------
    username : str
        The username to login to devices
    password : str
        The password to login to devices
    host_group : str
        The inventory host group
    play_path : str
        The path to the playbooks directory
    private_data_dir : str
        The path to the Ansible private data directory

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the interfaces and IPs, subnet and network
        addresses related to each IP.
    '''
    cmd = 'show interface summary | include Interface|IP address'
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd}

    # Execute the command
    playbook = f'{play_path}/cisco_asa_run_commands.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse the results
    df_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout'][0].split('\n')

            output = [_.strip('\t') for _ in output]

            output = [_ for _ in output if _.split()[0] == 'Interface' or
                      ' '.join(_.split()[:2]) == 'IP address']

            counter = 0
            for line in output:
                counter += 1
                line = line.split(',')
                if line[0].split()[0] == 'Interface' and \
                        '"' in line[0].split()[-1]:
                    inf = line[0].split()[1]
                    nameif = line[0].split()[2].strip('"')

                    _line = output[counter]
                    if 'unassigned' in _line:
                        ip = 'unassigned'
                        netmask = 'unassigned'
                    else:
                        ip = _line.split(',')[0].split()[-1]
                        netmask = _line.split(',')[-1].split()[-1]
                        cidr = hp.convert_mask_to_cidr(netmask)
                        ip = f'{ip}/{cidr}'

                    row = [device, inf, ip, nameif]
                    df_data.append(row)
    # Create a dataframe from df_data and return it
    cols = ['device', 'interface', 'ip', 'nameif']
    df = pd.DataFrame(data=df_data, columns=cols)

    # Filter out interfaces that do not have an IP address.
    df = df[df['ip'] != 'unassigned']

    # Add the subnets, network IPs, and broadcast IPs.
    addresses = df['ip'].to_list()
    result = hp.generate_subnet_details(addresses)
    df['subnet'] = result['subnet']
    df['network_ip'] = result['network_ip']
    df['broadcast_ip'] = result['broadcast_ip']

    return df
