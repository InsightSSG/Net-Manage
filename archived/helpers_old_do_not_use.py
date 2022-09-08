'''
A library of generic helper functions for dynamic runbooks.
'''

import ansible
import ansible_runner
import os
import pandas as pd
import re
import yaml
from getpass import getpass


def ansible_create_vars_df(test_dataframe, private_data_dir='.'):
    '''
    This function is created to be used with the maintenance tests notebooks.
    It reads all of the host groups from the 'df_test', gets the ansible
    variables for each group from the host file, creates a dataframe containing
    the variables, then returns it.

    Args:
        test_dataframe (DataFrame): The dataframe containing the tests.
        private_data_dir (str):     The path to the Ansible private_data_dir.
                                    It is the path that the 'inventory' folder
                                    is in. The default is the current folder.

    Returns:
        df_vars (DataFrame):        A dataframe containing the group variables
    '''
    cols = test_dataframe.columns.to_list()
    host_groups = list()
    for c in test_dataframe.columns.to_list():
        for item in test_dataframe[c].to_list():
            if item not in host_groups and item != 'nan':
                host_groups.append(item)

    host_vars = dict()

    for g in host_groups:
        group_vars = ansible_get_host_variables(g)
        host_vars[g] = group_vars

    # Create a dictionary to store the variable data for each group
    df_data = dict()
    df_data['host_group'] = list()

    # Iterate through the keys for each group in 'host_vars', adding it as a key to 'df_data'
    for key, value in host_vars.items():
        for k in value:
            if k != 'ansible_user' and k != 'ansible_password':
                df_data[k] = list()

    # Iterate through 'host_vars', populating 'df_data'
    for key, value in host_vars.items():
        df_data['host_group'].append(key)
        for item in df_data:
            if item != 'host_group':
                result = value.get(item)
                df_data[item].append(result)

    df_vars = pd.DataFrame.from_dict(df_data)

    return df_vars


def ansible_delete_extravars(extravars_dir='extravars'):
    '''
    Ansible--and therefore Ansible-runner--stores credentials in plain text.
    There are ways to get around that, but this function is an easy way
    to make sure it's deleted.

    Args:
        extravars_dir (str):    The directory to the file containing extra vars

    Returns:
        None
    '''
    # Get the list of files in the directory
    for item in os.listdir(extravars_dir):
        os.remove(f'{extravars_dir}/{item}')

        
def ansible_get_host_group():
    '''
    Gets the inventory host group to triage.

    Args:
        None

    Returns:
        host_group (str): The inventory host group
    '''
    host_group = input('Enter the name of the inventory host group: ')
    host_group = host_group.strip()
    return host_group
        

def ansible_get_host_variables(host_group, private_data_dir='.'):
    '''
    Gets the variables for a host or host group in the hosts file.

    Args:
        host_group (str):       The name of the host group
        private_data_dir (str): The path to the Ansible private_data_dir. This
                                is the path that the 'inventory' folder is in.
                                The default is the current folder.

    Returns:
        group_vars (dict):      The host group variables
    '''
    # Read the contents of the playbook into a dictionary
    with open(f'{private_data_dir}/inventory/hosts') as f:
        hosts = yaml.load(f, Loader=yaml.FullLoader)

    group_vars = hosts[host_group]['vars']

    return group_vars


def ansible_get_cisco_asa_interface_descriptions(username,
                                                 password,
                                                 host_group,
                                                 net_discover_path,
                                                 private_data_dir,
                                                 ansible_timeout=300):
    '''
    Gathers the link status, description, last link flap, and config for
    physical Ethernet interfaces. Also create a list of devices in the host
    group.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group to run the command
                                against
        inventory (str):        The path to the inventory file inside private_dir
        private_data_dir (str): The path to the inventory file
        ansible_timeout (str):  The amount of time paramiko waits before timing out

    Returns:
        devices (list):  A list of devices in the host group
        inf_data (dict): A dictionary containing the data
    '''
    # Create the base variables
    devices = list()
    inf_data = dict()

    # Run the 'show interface' command to get interface data
    cmd = 'show interface | include Interface|Description'
    
    # Create the extra variables to pass to Ansible
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd,
                 'ansible_timeout': ansible_timeout}

    # Execute the command
    runner = ansible_runner.run(private_data_dir='.',
                                playbook=f'{net_discover_path}/playbooks/cisco_asa_run_commands.yml',
                                extravars=extravars,
                                inventory=f'{private_data_dir}/inventory')

    print(f'{runner.status}: {runner.rc}')

    # Parse the output; add the hosts to 'devices' and the output to 'results'
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            
            # Add the host to the 'devices' list
            device = event_data['remote_addr']
            if device not in devices:
                devices.append(device)
            
            output = event_data['res']['stdout'][0].split('\n')
            output = list(filter(None, output))
            
            # Parse the output to get the appropriate data and add it to inf_data            
            inf_data[device] = dict()
            inf_data[device]['device'] = list()
            inf_data[device]['interface'] = list()
            inf_data[device]['description'] = list()
            inf_data[device]['status'] = list()

            for line in output:
                if line[0] != ' ' and line[0] != '\t':
                    interface = line.split()[1]
                    status = line.split('is ')[-1]
                    description = str()
                    
                    pos = output.index(line)
                    try:
                        # This code accounts for ASAs that put an invisible '\t' before the description
                        if 'Description' in output[pos+1] or '\tDescription' in output[pos+1]:
                            description = output[pos+1]
                            description = description.split('\t')
                            description = list(filter(None, description))[0]
                            description = description.split('Description: ')[-1]
                    except Exception as e:
                        if str(e) == 'list index out of range':
                            pass
                        else:
                            print(str(e))
                    
                    # Add the data to inf_data
                    inf_data[device]['device'].append(device)
                    inf_data[device]['interface'].append(interface)
                    inf_data[device]['description'].append(description)
                    # TODO: Uncomment the line below once interface status is added for the other interface_descriptions functions
                    # inf_data[device]['status'].append(status)

    devices.sort()
                    
    return devices, inf_data


def ansible_get_cisco_ios_interface_descriptions(username,
                                                 password,
                                                 host_group,
                                                 net_discover_path,
                                                 private_data_dir,
                                                 ansible_timeout=300):
    '''
    Gathers the link status, description, last link flap, and config for interfaces.
    This function also supports IOS_XE.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group to run the command against
        inventory (str):        The path to the inventory file inside private_dir
        private_data_dir (str): The path to the inventory file
        ansible_timeout (str):  The amount of time paramiko waits before timing out

    Returns:
        devices (list):  A list of devices in the host group
        inf_data (dict): A dictionary containing the data
    '''
    # Create the base variables
    devices = list()
    inf_data = dict()

    # Run the 'show interface' command to get interface data
    cmd = 'show interface description'
    
    # Create the extra variables to pass to Ansible
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd,
                 'ansible_timeout': ansible_timeout}

    # Execute the command
    runner = ansible_runner.run(private_data_dir='.',
                                playbook=f'{net_discover_path}/playbooks/cisco_ios_run_commands.yml',
                                extravars=extravars,
                                inventory=f'{private_data_dir}/inventory')

    print(f'{runner.status}: {runner.rc}')

    # Parse the output; add the hosts to 'devices' and the output to 'results'
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            
            # Add the host to the 'devices' list
            device = event_data['remote_addr']
            if device not in devices:
                devices.append(device)
            
            output = event_data['res']['stdout'][0].split('\n')
            output = list(filter(None, output))
            
            # Parse the output to get the appropriate data and add it to inf_data            
            inf_data[device] = dict()
            inf_data[device]['device'] = list()
            inf_data[device]['interface'] = list()
            inf_data[device]['description'] = list()
            inf_data[device]['status'] = list()

            # Get the position of the beginning of the interface description
            header = output[0]
            desc_pos = header.index('Description')
            
            # Get the position of the beginning of the interface status
            status_pos = header.index('Status')
            
            for line in output[1:]:
                interface = line.split()[0]
                status = line[status_pos:desc_pos].strip()
                description = line[desc_pos:].strip()

                # Add the data to inf_data
                inf_data[device]['device'].append(device)
                inf_data[device]['interface'].append(interface)
                inf_data[device]['description'].append(description)
                # TODO: Uncomment the line below once interface status is added for the other interface_descriptions functions
                # inf_data[device]['status'].append(status)

    devices.sort()
                    
    return devices, inf_data


def ansible_get_cisco_nxos_interface_data_no_vdc(username,
                                                 password,
                                                 host_group,
                                                 net_discover_path,
                                                 private_data_dir,
                                                 ansible_timeout=240):
    '''
    Gathers the link status, description, last link flap, and config for physical
    Ethernet interfaces. Also create a list of devices in the host group.

    Args:
        username (str):          The username to login to devices
        password (str):          The password to login to devices
        host_group (str):        The inventory host group to run the command against
        net_discover_path (str): The path to the Net-Discover repository
        private_data_dir (str):  The path to the inventory file
        ansible_timeout (str):   The amount of time paramiko waits before timing out

    Returns:
        devices (list):  A list of devices in the host group
        inf_data (dict): A dictionary containing the data
    '''
    # Create the base variables
    devices = list()
    inf_data = dict()
    
    # Run the 'show interface' command to get interface data
    cmd = 'show interface | egrep -A 20 "^Ethernet" | grep "Ethernet\|Description\|Last link flapped" | grep -v Hardware'
    
    # Create the extra variables to pass to Ansible
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd,
                 'ansible_timeout': ansible_timeout}

    # Execute the command
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=f'{net_discover_path}/playbooks/cisco_nxos_run_commands.yml',
                                extravars=extravars)

    print(f'{runner.status}: {runner.rc}')

    # Parse the output; add the hosts to 'devices' and the output to 'results'
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            
            # Add the host to the 'devices' list
            device = event_data['remote_addr']
            if device not in devices:
                devices.append(device)
            
            output = event_data['res']['stdout'][0].split('\n')
            output = list(filter(None, output))
            
            # Parse the output to get the appropriate data and add it to inf_data            
            inf_data[device] = dict()
            inf_data[device]['device'] = list()
            inf_data[device]['interface'] = list()
            inf_data[device]['description'] = list()
            inf_data[device]['status'] = list()
            inf_data[device]['last_link_flap'] = list()
            inf_data[device]['config'] = list()

            for line in output:
                if line[0] != ' ':
                    interface = line.split()[0]
                    status = line.split('is ')[-1]

                    description = str()
                    last_link_flap = str()

                    pos = output.index(line) + 1

                    try:
                        while output[pos][0] == ' ':
                            if '  Description: ' in output[pos]:
                                description = output[pos].split('Description: ')[-1]

                            if '  Last link flapped' in output[pos]:
                                last_link_flap = output[pos].split('flapped ')[-1]
                            pos += 1
                    except Exception as e:
                        if str(e) == 'list index out of range':
                            pass
                        else:
                            print(str(e))

                    inf_data[device]['device'].append(device)
                    inf_data[device]['interface'].append(interface)
                    inf_data[device]['description'].append(description)
                    inf_data[device]['status'].append(status)
                    inf_data[device]['last_link_flap'].append(last_link_flap)

    # Run the 'show run | section "interface Ethernet"' command to get interface configurations
    cmd = 'show run | section "interface Ethernet"'
    extravars['commands'] = cmd
                    
    # Execute the command
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=f'{net_discover_path}/playbooks/cisco_nxos_run_commands.yml',
                                extravars=extravars)

    print(f'{runner.status}: {runner.rc}')

    # Parse the output to get the configs and add them to inf_data 
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            
            # Set the device name so that the correct device in inf_data will be updated
            device = event_data['remote_addr']
            
            output = event_data['res']['stdout'][0]
            
            # Use regex to search the output for each interface in inf_data
            for inf in inf_data[device]['interface']:
                pattern = f'^interface {inf}$(.*?)interface'

                config = '\n'.join(re.findall(pattern, output, flags=re.M|re.S))
                
                # Cleanup the data by removing "\n" characters, leading and trailing spaces, etc
                config = config.split('\n')
                config = list(filter(None, config))
                config = [c.strip() for c in config]
                
                # Convert the config to a string so that it is easier to work with in Pandas
                config = ','.join(config)

                # Add the config to inf_data
                inf_data[device]['config'].append(config)
                
    # Combine each device in inf_data so that they are a single dictionary with no nesting
    # inf_data[device] = dict()
    # inf_data[device]['device'] = list()
    # inf_data[device]['interface'] = list()
    # inf_data[device]['description'] = list()
    # inf_data[device]['status'] = list()
    # inf_data[device]['last_link_flap'] = list()
    # inf_data[device]['config'] = list()
    
    devices.sort()
    
    df_data = dict()
    
    for key, value in inf_data.items():
        for k, v in value.items():
            df_data[k] = list()
        break
        
    for device in devices:
        for key, value in inf_data[device].items():
            for item in value:
                df_data[key].append(item)

    inf_data = df_data
                
    return devices, inf_data


def ansible_get_cisco_nxos_interface_descriptions(username,
                                                  password,
                                                  host_group,
                                                  net_discover_path,
                                                  private_data_dir,
                                                  ansible_timeout=300):
    '''
    Gathers the link status, description, last link flap, and config for physical
    Ethernet interfaces. Also create a list of devices in the host group.

    Args:
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group to run the command against
        inventory (str):        The path to the inventory file inside private_dir
        private_data_dir (str): The path to the inventory file
        ansible_timeout (str):  The amount of time paramiko waits before timing out

    Returns:
        devices (list):  A list of devices in the host group
        inf_data (dict): A dictionary containing the data
    '''
    # Create the base variables
    devices = list()
    inf_data = dict()

    # Run the 'show interface' command to get interface data
    cmd = 'show interface description'
    
    # Create the extra variables to pass to Ansible
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd,
                 'ansible_timeout': ansible_timeout}

    # Execute the command
    runner = ansible_runner.run(private_data_dir='.',
                                playbook=f'{net_discover_path}/playbooks/cisco_nxos_run_commands.yml',
                                extravars=extravars,
                                inventory=f'{private_data_dir}/inventory')

    print(f'{runner.status}: {runner.rc}')

    # Parse the output; add the hosts to 'devices' and the output to 'results'
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            
            # Add the host to the 'devices' list
            device = event_data['remote_addr']

            if device not in devices:
                devices.append(device)
            
            output = event_data['res']['stdout'][0].split('\n')
            output = list(filter(None, output))
            
            # Parse the output to get the appropriate data and add it to inf_data            
            inf_data[device] = dict()
            inf_data[device]['device'] = list()
            inf_data[device]['interface'] = list()
            inf_data[device]['description'] = list()
            # TODO: Add support for gathering the interface statuses
            # inf_data[device]['status'] = list()
            
            # Create a list to capture the index number of lines that do not contain an interface description
            no_desc_lines = ['-'*79]

            for line in output:
                # Get the line position of the beginning of the interface description column. This is
                # necessary because Nexuses have different columns depending on the interface type
                pos = output.index(line)
                
                try:
                    if 'Description' in line or 'Interface' in line:
                        # Avoid capturing interface descriptions that contain 'Description' or 'Port'
                        if '-----------' in output[pos+1].split()[0]:
                            desc_pos = line.index('Description')
                            no_desc_lines.append(line)
                except Exception as e:
                    if str(e) == 'list index out of range':
                        pass
                    else:
                        print(str(e))
                
                # Get the interface descriptions
                if line not in no_desc_lines:
                    interface = line.split()[0]
                    description = line[desc_pos:]
                    inf_data[device]['device'].append(device)
                    inf_data[device]['interface'].append(interface)
                    inf_data[device]['description'].append(description)
                
    devices.sort()
                
    return devices, inf_data


def get_nxos_interface_data_no_vdc(username,
                                   password,
                                   host_group,
                                   net_discover_path,
                                   private_data_dir,
                                   ansible_timeout=240):
    '''
    Gathers the link status, description, last link flap, and config for physical
    Ethernet interfaces. Also create a list of devices in the host group.

    Args:
        username (str):          The username to login to devices
        password (str):          The password to login to devices
        host_group (str):        The inventory host group to run the command against
        net_discover_path (str): The path to the Net-Discover repository
        private_data_dir (str):  The path to the inventory file
        ansible_timeout (str):   The amount of time paramiko waits before timing out

    Returns:
        devices (list):  A list of devices in the host group
        inf_data (dict): A dictionary containing the data
    '''
    # Create the base variables
    devices = list()
    inf_data = dict()

    # Run the 'show interface' command to get interface data
    cmd = 'show interface | egrep -A 20 "^Ethernet" | grep "Ethernet\|Description\|Last link flapped" | grep -v Hardware'
    
    # Create the extra variables to pass to Ansible
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd,
                 'private_data_dir': private_data_dir,
                 'ansible_timeout': ansible_timeout}

    # Execute the command
    runner = ansible_runner.run(private_data_dir='.',
                                playbook=f'{net_discover_path}/playbooks/cisco_nxos_run_commands.yml',
                                extravars=extravars)

    print(f'{runner.status}: {runner.rc}')

    # Parse the output; add the hosts to 'devices' and the output to 'results'
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            
            # Add the host to the 'devices' list
            device = event_data['remote_addr']
            if device not in devices:
                devices.append(device)
            
            output = event_data['res']['stdout'][0].split('\n')
            output = list(filter(None, output))
            
            # Parse the output to get the appropriate data and add it to inf_data            
            inf_data[device] = dict()
            inf_data[device]['device'] = list()
            inf_data[device]['interface'] = list()
            inf_data[device]['description'] = list()
            inf_data[device]['status'] = list()
            inf_data[device]['last_link_flap'] = list()
            inf_data[device]['config'] = list()

            for line in output:
                if line[0] != ' ':
                    interface = line.split()[0]
                    status = line.split('is ')[-1]

                    description = str()
                    last_link_flap = str()

                    pos = output.index(line) + 1

                    try:
                        while output[pos][0] == ' ':
                            if '  Description: ' in output[pos]:
                                description = output[pos].split('Description: ')[-1]

                            if '  Last link flapped' in output[pos]:
                                last_link_flap = output[pos].split('flapped ')[-1]
                            pos += 1
                    except Exception as e:
                        if str(e) == 'list index out of range':
                            pass
                        else:
                            print(str(e))

                    inf_data[device]['device'].append(device)
                    inf_data[device]['interface'].append(interface)
                    inf_data[device]['description'].append(description)
                    inf_data[device]['status'].append(status)
                    inf_data[device]['last_link_flap'].append(last_link_flap)

    # Run the 'show run | section "interface Ethernet"' command to get interface configurations
    cmd = 'show run | section "interface Ethernet"'
    extravars['commands'] = cmd
                    
    # Execute the command
    runner = ansible_runner.run(private_data_dir='.',
                                playbook=f'{net_discover_path}/playbooks/cisco_nxos_run_commands.yml',
                                extravars=extravars)

    print(f'{runner.status}: {runner.rc}')

    # Parse the output to get the configs and add them to inf_data 
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            
            # Set the device name so that the correct device in inf_data will be updated
            device = event_data['remote_addr']
            
            output = event_data['res']['stdout'][0]
            
            # Use regex to search the output for each interface in inf_data
            for inf in inf_data[device]['interface']:
                pattern = f'^interface {inf}$(.*?)interface'

                config = '\n'.join(re.findall(pattern, output, flags=re.M|re.S))
                
                # Cleanup the data by removing "\n" characters, leading and trailing spaces, etc
                config = config.split('\n')
                config = list(filter(None, config))
                config = [c.strip() for c in config]
                
                # Convert the config to a string so that it is easier to work with in Pandas
                config = ','.join(config)

                # Add the config to inf_data
                inf_data[device]['config'].append(config)
                
    return devices, inf_data



def ansible_read_hosts_to_dict(hosts_file=str()):
    '''
    Reads the contents of the host file into a dictionary

    Args:
        hosts_file (str):   The full path to the hosts file

    Returns:
        hosts (dict):       The contents of the hosts file as a Python
                            dictionary
    '''
    # If the hosts file was not defined, then use the default one
    if not hosts_file:
        hosts_file = f'{os.getcwd()}/inventory/hosts'

    # Read the hostfiles into a dictionary and return it
    with open(hosts_file, 'r') as stream:
        hosts = yaml.safe_load(stream)

    return hosts

        
def ansible_read_playbook_to_dict(playbook):
    '''
    Reads the contents of a playbook into a dictionary

    Args:
        playbook (str): The full path to the playbook file

    Returns:
        pb_dict (dict): The playbook as a dictionary
    '''
    with open(playbook, 'r') as stream:
        pb_dict = yaml.safe_load(stream)

    return pb_dict
    
    
def f5_count_active_pool_members(output):
    '''
    Parses the output of 'show ltm pool | grep "Current Active Members"' to get
    the total number of active pool members on an F5

    Args:
        output (list):      The output of the above command

    Returns:
        num_members (int):  The total number of active pool members
    '''
    num_members = 0
    for line in output:
        count = int(line.split()[-1])
        num_members += count

    return num_members


def get_username():
    '''
    Gets the username to login to a device with

    Args:
        None

    Returns:
        username (str): The username
    '''
    username = input('Enter the username to login to the devices with: ')

    return username


def get_password():
    '''
    Gets the password to login to a device with

    Args:
        None

    Returns:
        password (str): The password
    '''
    # Get the user's password and have them type it twice for verification
    pass1 = str()
    pass2 = None
    while pass1 != pass2:
        pass1 = getpass('Enter your password: ')
        pass2 = getpass('Confirm your password: ')
        if pass1 != pass2:
            print('Error: Passwords do not match.')
    password = pass1

    return password


def get_creds():
    '''
    Gets the username and password to login to devices with.

    Args:
        None

    Returns:
        username (str): The username
        password (str): The password
    '''
    username = get_username()
    password = get_password()
    return username, password


def get_interface_data_nxos(username, password, host_group, ansible_timeout=240):
    '''
    Gathers the link status, description, last link flap, and config for physical
    Ethernet interfaces. It can be expanded to include additional data later.
    
    It also returns a sorted list of devices in the host group.

    The reason data collection is limited is because Nexus 5Ks with many FEXes
    exceeded Ansible's timeouts. If this function is changed then it should be
    carefully tested for backwards compatibility.

    Args:
        username (str):        The username to login to devices
        password (str):        The password to login to devices
        host_group (str):      The inventory host group to run the command against
        ansible_timeout (str): The amount of time paramiko waits before timing out

    Returns:
        devices (list):  A list of devices in the host group
        inf_data (dict): A dictionary containing the data
    '''
    # Create the base variables
    devices = list()
    inf_data = dict()

    # Run the 'show interface' command to get interface data
    cmd = 'show interface | egrep -A 17 "^Ethernet" | grep "Ethernet\|Description\|Last link flapped" | grep -v Hardware'
    
    # Create the extra variables to pass to Ansible
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': cmd,
                 'ansible_timeout': ansible_timeout}

    # Execute the command
    runner = ansible_runner.run(private_data_dir='.',
                                playbook='../../Net-Discover/ansible/plays/cisco/cisco_nxos_run_commands.yml',
                                extravars=extravars)

    print(f'{runner.status}: {runner.rc}')

    # Parse the output; add the hosts to 'devices' and the output to 'results'
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            
            # Add the host to the 'devices' list
            device = event_data['remote_addr']
            if device not in devices:
                devices.append(device)
            
            output = event_data['res']['stdout'][0].split('\n')
            output = list(filter(None, output))
            
            # Parse the output to get the appropriate data and add it to inf_data            
            inf_data[device] = dict()
            inf_data[device]['device'] = list()
            inf_data[device]['interface'] = list()
            inf_data[device]['description'] = list()
            inf_data[device]['status'] = list()
            inf_data[device]['last_link_flap'] = list()
            inf_data[device]['config'] = list()

            for line in output:
                if line[0] != ' ':
                    interface = line.split()[0]
                    status = line.split('is ')[-1]

                    description = str()
                    last_link_flap = str()

                    pos = output.index(line) + 1

                    try:
                        while output[pos][0] == ' ':
                            if '  Description: ' in output[pos]:
                                description = output[pos].split('Description: ')[-1]

                            if '  Last link flapped' in output[pos]:
                                last_link_flap = output[pos].split('flapped ')[-1]
                            pos += 1
                    except Exception as e:
                        if str(e) == 'list index out of range':
                            pass
                        else:
                            print(str(e))

                    inf_data[device]['device'].append(device)
                    inf_data[device]['interface'].append(interface)
                    inf_data[device]['description'].append(description)
                    inf_data[device]['status'].append(status)
                    inf_data[device]['last_link_flap'].append(last_link_flap)

    # Run the 'show run | section "interface Ethernet"' command to get interface configurations
    cmd = 'show run | section "interface Ethernet"'
    extravars['commands'] = cmd
                    
    # Execute the command
    runner = ansible_runner.run(private_data_dir='.',
                                playbook='../../Net-Discover/ansible/plays/cisco/cisco_nxos_run_commands.yml',
                                extravars=extravars)

    print(f'{runner.status}: {runner.rc}')

    # Parse the output to get the configs and add them to inf_data 
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            
            # Set the device name so that the correct device in inf_data will be updated
            device = event_data['remote_addr']
            
            output = event_data['res']['stdout'][0]
            
            # Use regex to search the output for each interface in inf_data
            for inf in inf_data[device]['interface']:
                pattern = f'^interface {inf}$(.*?)interface'

                config = '\n'.join(re.findall(pattern, output, flags=re.M|re.S))
                
                # Cleanup the data by removing "\n" characters, leading and trailing spaces, etc
                config = config.split('\n')
                config = list(filter(None, config))
                config = [c.strip() for c in config]
                
                # Convert the config to a string so that it is easier to work with in Pandas
                config = ','.join(config)

                # Add the config to inf_data
                inf_data[device]['config'].append(config)

    devices.sort()
                
    return devices, inf_data

def create_df_interfaces(devices, inf_data):
    '''
    Creates a dataframe of all interfaces. The columns include device, interface, description,
    status, last_link_flap, config
    
    For instructions on the format of the dictionary, see:
    - https://www.geeksforgeeks.org/how-to-create-dataframe-from-dictionary-in-python-pandas/
    
    Args:
        devices (list):  A list of devices in the Ansible inventory host group
        inf_data (dict): A dictionary containing the data for the dataframe

    Returns:
        df_interfaces (DataFrame): A dataframe containing the interface data
    '''
    # Delete the dataframe if it already exists. This is to avoid corruption when
    # modifying dataframes inside of Jupyter notebooks.
    try:
        del df_interfaces
    except Exception:
        pass

    # Create the DataFrame columns (these are the same as the 'inf_data[device]' keys
    cols = list()
    for device in devices:
        for key in inf_data[device]:
            cols.append(key)
        break

    # Create the empty dataframe
    df_interfaces = pd.DataFrame(columns=cols)

    # Create a dataframe from each device in 'inf_data' and concatenate it with 'df_interfaces'
    for device in devices:
        df_interfaces = pd.concat([df_interfaces, pd.DataFrame.from_dict(inf_data[device])], axis=0)

    # Reset the index so that each row will have a unique index
    df_interfaces = df_interfaces.reset_index(drop=True)

    return df_interfaces


def create_df_inactive(df_interfaces):
    '''
    Creates the dataframe of all interfaces that are shutdown or disconnected.
    
    Args:
        df_interfaces (DataFrame): The DataFrame containing data for all interfaces

    Returns:
        df_inactive (DataFrame): A DataFrame containing the interfaces that are shutdown or disconnected
    '''
    # Delete the dataframe if it already exists. This it to avoid corruption
    try:
        del df_inactive
    except Exception:
        pass

    # Create the dataframe
    df_inactive = df_interfaces.loc[df_interfaces['status'] != 'up']

    # Reset the index so that the row numbers will be sequential
    df_inactive = df_inactive.reset_index(drop=True)
    
    return df_inactive


def df_inactive_configured(df_inactive):
    '''
    Creates the dataframe of all interfaces that are shutdown or disconnected and have a config.
    Interfaces that only have 'shutdown' in the config are excluded
    '''
    # Delete the dataframe if it already exists. This it to avoid corruption
    try:
        del df_inactive_configured
    except Exception:
        pass
    
    # Create 'df_inactive_configured' and reset the index so that the row numbers will be sequential
    df_inactive_configured = df_inactive.loc[(df_inactive['config'] != str()) & (df_inactive['config'] != 'shutdown')].reset_index(drop=True)
    
    return df_inactive_configured


def format_check_data(check_dict):
    '''
    Formats the pre- / post-check data into a dictionary consumable by Pandas
    
    Args:
        check_dict (dict): A dictionary containing the pre- or post-check data

    Returns:
        check_df_data (dict): The formatted dictionary
    '''
    check_df_data = dict()
    check_df_data['device'] = list()
    check_df_data['config_diff'] = list()
    check_df_data['stp_blocked_ports'] = list()
    check_df_data['stp_log_errors'] = list()
    check_df_data['stp_err_disabled'] = list()
    check_df_data['vpc_consistent_port_channels'] = list()
    check_df_data['vpc_suspended_vlans'] = list()
    check_df_data['vpc_keepalive'] = list()

    for device in devices:
        if check_dict[device]['show running-config diff']:
            config_diff = True
        else:
            config_diff = False

        try:
            stp_blocked_ports = str(int(check_dict[device]['show spanning-tree blockedports'][-1].split()[-1]))
        except Exception:
            stp_blocked_ports = str(0)

        stp_log_errors = check_dict[device]['show interface status err-disabled'][3:]
        if stp_log_errors:
            stp_log_errors = str(len(stp_log_errors))
        else:
            stp_log_errors = '0'

        stp_err_disabled = [l for l in check_dict[device]['show logging last 9999 | grep "err-disable\|BPDU"'] if l != '']
        if len(stp_err_disabled) > 0:
            stp_err_disabled = True
        else:
            stp_err_disabled = False

        counter = 0
        for line in check_dict[device]['show vpc brief | grep Po']:
            if 'success' in line:
                counter += 1
        vpc_consistent_port_channels = counter

        try:
            vpc_suspended_vlans = check_dict[device]['show vpc consistency-parameters global | grep "Local suspended"'][0].split()[-2]
        except Exception:
            vpc_suspended_vlans = '-'

        vpc_keepalive = check_dict[device]['show vpc peer-keepalive | grep -v "ms\|msec"'][0]
        if 'peer is alive' in vpc_keepalive:
            vpc_keepalive = True
        else:
            vpc_keepalive = False

        # Add the variables to check_df_data
        check_df_data['device'].append(device)
        check_df_data['config_diff'].append(config_diff)
        check_df_data['stp_blocked_ports'].append(stp_blocked_ports)
        check_df_data['stp_log_errors'].append(stp_log_errors)
        check_df_data['stp_err_disabled'].append(stp_err_disabled)
        check_df_data['vpc_consistent_port_channels'].append(vpc_consistent_port_channels)
        check_df_data['vpc_suspended_vlans'].append(vpc_suspended_vlans)
        check_df_data['vpc_keepalive'].append(vpc_keepalive)

    return check_df_data


def cisco_nxos_run_checks(username, password, host_group, play_path):
    '''
    Run the pre- and post-checks on a Cisco NXOS and adds the results to
    a dictionary. Also creates a list of devices in the host group.
    
    Args:
        username (str):        The username to login to devices
        password (str):        The password to login to devices
        host_group (str):      The inventory host group to run the command against
        play_path (str):       The path to the directory containing the playbooks

    Returns:
        devices (list):    A list of devices in the host group
        check_data (dict): A dictionary containing the pre-checks
    '''
    # Create the base variables
    check_data = dict()
    
    # Define the commands to run
    commands = {'diff_command': 'show running-config diff',
                'interface_status_command': 'show interface status | grep -v -\-\-\-',
                'err_disabled_command': 'show interface status err-disabled',
                'logging_command': 'show logging last 9999 | grep "err-disable\|BPDU"',
                'stp_blocked_ports_command': 'show spanning-tree blockedports',
                'vpc_brief_command': 'show vpc brief | grep Po',
                'vpc_consistency_command': 'show vpc consistency-parameters global | grep "Local suspended"',
                'vpc_keepalive_command': 'show vpc peer-keepalive | grep -v "ms\|msec"'}

    # Create the extra variables to pass to Ansible
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    for command in commands:
        extravars[command] = commands[command]

    # Execute the pre-checks
    runner = ansible_runner.run(private_data_dir='.',
                                playbook=f'{play_path}/cisco_nxos_pre_post_checks.yml',
                                extravars=extravars)
    
    # Parse the output; add the hosts to 'devices' and the command output to 'check_data'
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']
            
            # Create the dictionary keys for 'check_data'
            if not check_data.get(device):
                check_data[device] = dict()
            
            # Add the command output to 'check_data'
            cmd = event_data['res']['invocation']['module_args']['commands'][0]
            output = event_data['res']['stdout'][0].split('\n')
            check_data[device][cmd] = output

    return check_data
