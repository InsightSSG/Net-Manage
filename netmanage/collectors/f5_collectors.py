#!/usr/bin/env python3

import ansible_runner
import ast
import pandas as pd
import requests
from netmanage import run_collectors as rc
from netmanage.helpers import f5_helpers as f5h
from netmanage.helpers import helpers as hp
from netmanage.parsers import f5_parsers as f5p


def build_pool_table(username: str,
                     password: str,
                     host_group: str,
                     play_path: str,
                     private_data_dir: str,
                     db_path: str,
                     timestamp: str,
                     validate_certs: bool = True) -> pd.DataFrame:
    '''
    Creates a custom table that contains the F5 pools, associated VIPs (if
    applicable), and pool members (if applicable).

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        Path to the Ansible private data directory.
    db_path : str
        The path to the database.
    timestamp : str
        The timestamp for the table.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df_members : pd.DataFrame
        The pool availability and associated data.
    '''
    # TODO: Optimize this so the table is only built for any device in the
    #       hostgroup that does not exist in the table (or if the table is not
    #       yet present)
    df_pools = get_pools_and_members(username,
                                     password,
                                     host_group,
                                     play_path,
                                     private_data_dir)

    rc.add_to_db('f5_pool_summary',
                 df_pools,
                 timestamp,
                 db_path,
                 method='replace')

    df_vips = get_vip_summary(username,
                              password,
                              host_group,
                              play_path,
                              private_data_dir,
                              df_pools)

    rc.add_to_db('f5_vip_summary',
                 df_vips,
                 timestamp,
                 db_path,
                 method='replace')

    return df_vips


def convert_tmsh_output_to_dict(in_data: str):
    '''
    Converts F5 'tmsh list' output to a Python dictionary.

    Parameters
    ----------
    in_data : str
        The output to convert to a dictionary.

    Returns
    -------
    out : dict
        'in_data' formatted as a Python dictionary.

    Notes
    -----
    F5 'tmsh list' output is close enough to a Python dictionary or JSON to be
    confusing, but in reality it is neither. However, it does follow certain
    rules.

    Rule 1: After the first line, the maximum number of elements is 2.

    Rule 2: If more than two words are in a line, then the second element will
            be wrapped in quotes. (e.g., 'vendor "F5 NETWORKS INC.")

    Rule 3: If a line contains a single word, then it is a member of an array.

    Rule 4: If a line contains a single word followed by '{ }', then '{ }'
            indicates an empty array.

    By combining these rules, we can create a relatively simple parser that
    will convert the output to a Python dictionary. It works like this:

    1. The rules listed above are used to format each line of the output into
       a form that is a valid part of a Python dictionary. For example, the
       line 'net vlan VLAN1 {' becomes, '"net vlan VLAN1": {'.

    2. Each line is added to a list.

    3. Any additional formatting is completed.

    4. The list is joined to create a string.

    5. A simple string.replace() inserts any commas that are missing between a
       '}' and a '"'. (It was easier to do it this way than to embed the logic
       inside the parser.)

    6. Formatting is finalized.

    7. ast.literal_eval is used to convert 'out' into a dictionary.

    Examples
    ----------
>>> in_data = """net interface 1.0 {
...     if-index 542
...     mac-address 00:94:a1:91:23:44
...     media-active 1000SX-FD
...     media-max 1000T-FD
...     module-description "F5 Qualified Optic"
...     mtu 9198
...     serial N395NEY
...     vendor "F5 NETWORKS INC."
...     vendor-oui 009065
...     vendor-partnum OPT-0010
...     vendor-revision 00
... }"""
>>> output = convert_tmsh_output_to_dict(in_data)
>>> assert type(output) == dict()

    '''
    # Convert the data to a list and strip all spaces.
    in_data = [_.strip() for _ in in_data.split('\n')]

    # Create a list to store each line of the formatted data. Begin the list
    # with a '{'.
    out = ['{']

    for line in in_data:
        # Format lines that look like the following:
        # 'net interface mgmt {'
        # 'net self BIGIQ {'
        # 'net vlan SERVERS {'
        if len(line.split('{')) > 1 and '}' not in line:
            line = line.replace(' {', '": {')
            line = f'"{line}'

        # Format lines that look like the following:
        # 'fwd-mode l3'
        # 'vendor "F5 NETWORKS INC."'
        # 'module-description "F5 Qualified Optic"'
        # 'tcp:ssh'
        # 'default'
        if '{' not in line and '}' not in line:
            if len(line.split()) > 1:
                if '"' in line:
                    line = line.split('"')
                    line = list(filter(None, line))
                    line = [_.strip() for _ in line]
                else:
                    line = line.split()
                line = [f'"{_}"' for _ in line]
                line = ': '.join(line)
                line = f'{line},'
            else:
                line = f'"{line}",'

        # Format lines that look like the following:
        # '2.0 { }'
        elif '{' in line and '}' in line:
            line = f'"{line.split()[0]}": [],'

        out.append(line)

    # Additional formatting needs to be done, so create a dictionary to store
    # the line numbers that require updates. Each key will be the line number
    # and the value will be the formatted line.
    replacements = dict()

    counter = 0
    for line in out:
        # Check each line to find out if it is a member of an array. If it is,
        # then do the following:
        # 1. Convert the leading or trailing '{' or '}' to a '[' or ']'.
        # 2. Insert a comma so ast.literal_eval can convert it to a list item.
        if '{' in line:
            if len(out[counter+1].split()) == 1:
                replacements[counter] = line.replace('{', '[')
        if '}' in line:
            if len(out[counter-1].split()) == 1:
                if '}' not in out[counter-1]:
                    replacements[counter] = line.replace('}', '],')
        counter += 1

    # Update 'out' with the data from 'replacements'.
    for key, value in replacements.items():
        out[key] = value

    # Add a trailing '}' to 'out'.
    out.append('}')

    # Convert 'out' to a string.
    out = ''.join(out)

    # Add a comma between '}' and '".
    out = out.replace('}"', '},"')

    # Convert 'out' to a dictionary
    out = ast.literal_eval(out)

    return out


def get_arp_table(username: str,
                  password: str,
                  host_group: str,
                  nm_path: str,
                  play_path: str,
                  private_data_dir: str,
                  validate_certs: bool = True) -> pd.DataFrame:
    '''
    Get the ARP table on F5 LTMs.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to the device.
    host_group : str
        The Ansible inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df : pd.DataFrame
        A Pandas DataFrame containing the ARP table.
    '''
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'command': r'show net arp | grep -v "\\-\\-\\-\\-\|Net::Arp"'}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    playbook = f'{play_path}/f5_run_adhoc_command.yml'

    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Create a list to store the ARP data for `df`.
    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']

            output = event_data['res']['stdout_lines'][0]

            # Create the dataframe columns.
            columns = ['device'] + output[0].split()

            # Parse the output and add it to `df_data`
            for line in output[1:]:
                line = [device] + line.split()
                df_data.append(line)

    # Create `df`.
    df = pd.DataFrame(df_data, columns=columns).astype(str)

    # Get the MAC OUIs and add them to `df`
    df_macs = hp.find_mac_vendors(df['HWaddress'], nm_path)
    df['vendor'] = df_macs['vendor']

    return df


def get_f5_logs(username: str,
                password: str,
                base_url: str,
                range_str: str = "",
                lines: int = 500,
                verify_ssl: bool = True) -> str:
    """
    Fetch the logs from an F5 BIG-IP system using the iControl REST API.

    Parameters
    ----------
    username : str
        Username to authenticate with the F5 BIG-IP system.
    password : str
        Password to authenticate with the F5 BIG-IP system.
    base_url : str
        Base URL of the F5 BIG-IP system's iControl REST API.
    range_str : str, optional
        Specifies the date-time range of the logs to fetch in F5's tmsh format.
        It can be a single date, a date range (e.g., "2023-08-14--2023-08-15"),
        or a relative period like "now-2d". Defaults to an empty string.
    lines : int, optional
        Number of log lines to fetch. Defaults to 500.
    verify_ssl : bool, optional
        Whether or not to verify SSL certificates. Defaults to True.

    Returns
    -------
    str
        Raw log data as a string. Returns an empty string if logs couldn't be
        fetched.

    Raises
    ------
    requests.exceptions.HTTPError
        If there was an HTTP error during the request.
    """
    # Parsing the time range
    times = range_str.split('--')
    if 'now' in range_str and '-' in range_str:
        start_time, end_time = f5h.convert_tmsh_time(times[0])
    else:
        start_time = f5h.convert_tmsh_time(times[0])
        end_time = f5h.convert_tmsh_time(times[1],
                                         True) if len(times) > 1 else ""

    # Forming the endpoint URL
    endpoint = [f"{base_url}/mgmt/tm/sys/log/ltm/stats?options=lines,{lines}",
                f"range,{start_time}--{end_time}"]
    endpoint = ','.join(endpoint)

    response = requests.get(
        endpoint,
        auth=(username, password),
        headers={"Content-Type": "application/json"},
        verify=verify_ssl
    )

    response.raise_for_status()
    try:
        logs = response.json().get('apiRawValues', {}).get('apiAnonymous', "")
        success = True
    except ValueError:
        logs = "Failed to decode JSON: " + response.text
        success = False

    # Tokenize the logs, add them to 'df_data', and create a DataFrame.
    if success:
        df_data = dict()
        logs = logs.split('\n')
        logs = list(filter(None, logs))
        for msg in logs[1:]:
            msg = f5p.tokenize_f5_log(msg)
            for key, value in msg.items():
                try:
                    df_data[key].append(value)
                except KeyError:
                    df_data[key] = list()
                    df_data[key].append(value)

    df = pd.DataFrame(df_data)

    return df


def get_self_ips(username: str,
                 password: str,
                 host_group: str,
                 play_path: str,
                 private_data_dir: str,
                 validate_certs: bool = True) -> pd.DataFrame:
    '''
    Get the self IPs on F5 LTMs.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to the device.
    host_group : str
        The Ansible inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df : pd.DataFrame
        A Pandas DataFrame containing the self IPs.
    '''
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'command': 'list net self recursive /*/*'}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    playbook = f'{play_path}/f5_run_adhoc_command.yml'

    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Create a dictionary to store each self IP.
    data = dict()

    # Create a dictionary to store the data for `df`
    df_data = dict()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']
            data[device] = list()
            output = event_data['res']['stdout_lines'][0]

            # Parse the output and add it to `data``
            counter = 0
            for line in output:
                if line[:8] == 'net self':
                    block = list()
                    pos = counter
                    while output[pos][0] != '}':
                        block.append(output[pos])
                        pos += 1
                    block.append('}')

                    # Convert the block to a dictionary then flatten it.
                    # pprint(block)
                    block = '\n'.join(block)
                    block = convert_tmsh_output_to_dict(block)

                    for key, value in block.items():
                        self_name = key.split()[-1]
                        value['name'] = self_name

                    # Add the device name to `value`, then add `block` to
                    # `data`.
                    value['device'] = device
                    data[device].append(value)

                    # Add each key in `block` to `df_data`.
                    for key in value:
                        if not df_data.get(key):
                            df_data[key] = list()

                counter += 1

    # Iterate over `data`, adding the values to `df_data`.
    for key, value in data.items():
        for item in value:
            for k in df_data:
                df_data[k].append(item.get(k))

    # Create `df`.
    df = pd.DataFrame.from_dict(df_data).astype(str)

    # Make `device` the first column, then return `df`.
    col_1 = df.pop('device')
    df.insert(0, 'device', col_1)

    # Add the subnets, network IPs, and broadcast IPs.
    addresses = df['address'].to_list()

    df['cidr'] = [_.split('/')[-1] for _ in df['address'].to_list()]
    df['address'] = [_.split('/')[0] for _ in df['address'].to_list()]

    result = hp.generate_subnet_details(addresses)
    df['subnet'] = result['subnet']
    df['network_ip'] = result['network_ip']
    df['broadcast_ip'] = result['broadcast_ip']

    # Place 'cidr' column to the right of 'address' column.
    cols = df.columns.tolist()
    ip_index = cols.index('address')
    cols.insert(ip_index + 1, cols.pop(cols.index('cidr')))
    df = df[cols]

    return df


def get_interface_descriptions(username: str,
                               password: str,
                               host_group: str,
                               nm_path: str,
                               play_path: str,
                               private_data_dir: str,
                               reverse_dns: bool = False,
                               validate_certs: bool = True) -> pd.DataFrame:
    '''
    Gets F5 interface descriptions.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    nm_path : str
        The path to the Net-Manage repository.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    reverse_dns : bool, optional
        Whether to run a reverse DNS lookup. Defaults to False because the test
        can take several minutes on large ARP tables.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df_desc : pd.DataFrame
        The interface descriptions.
    '''
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the command and parse the results
    playbook = f'{play_path}/f5_get_interface_description.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Create a list to store the rows for the dataframe
    df_data = list()
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout_lines'][0]
            pos = 1
            for line in output:
                if 'net interface' in line or 'net trunk' in line:
                    inf = line.split()[-2]
                    desc = output[pos].split()[1:]
                    desc = ' '.join(desc)  # To account for spaces in desc
                    df_data.append([device, inf, desc])
                pos += 1

    # Create the dataframe and return it
    cols = ['device', 'interface', 'description']
    df_desc = pd.DataFrame(data=df_data, columns=cols)
    return df_desc


def get_interface_status(username: str,
                         password: str,
                         host_group: str,
                         play_path: str,
                         private_data_dir: str,
                         validate_certs: bool = True) -> pd.DataFrame:
    '''
    Gets the interface and trunk statuses for F5 devices.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df_inf_status : pd.DataFrame
        The interface statuses.
    '''
    # Get the interface statuses
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the pre-checks
    playbook = f'{play_path}/f5_get_interface_status.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse the output and add it to 'data'
    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            # The playbook runs two commands--show net interface and show net
            # trunk. The output of both commands is in the same event.
            output = event_data['res']['stdout_lines']
            net_inf = output[0]
            try:
                net_trunk = output[1]
            except IndexError:
                net_trunk = []

            # Parse the interface statuses and add it to 'df_data'.
            for line in net_inf:
                line = line.split()
                inf = line[0]
                status = line[1]
                vlan = str()
                duplex = str()
                speed = str()
                media = line[8]
                row = [device,
                       inf,
                       status,
                       vlan,
                       duplex,
                       speed,
                       media]
                df_data.append(row)

            for line in net_trunk:
                line = line.split()
                inf = line[0]
                status = line[1]
                vlan = str()
                duplex = str()
                speed = line[2]
                media = str()
                row = [device,
                       inf,
                       status,
                       vlan,
                       duplex,
                       speed,
                       media]
                df_data.append(row)

    # Create the dataframe and return it
    cols = ['device',
            'interface',
            'status',
            'vlan',
            'duplex',
            'speed',
            'type']

    df_inf_status = pd.DataFrame(data=df_data, columns=cols)

    return df_inf_status


def get_node_availability(username: str,
                          password: str,
                          host_group: str,
                          play_path: str,
                          private_data_dir: str,
                          validate_certs: bool = True) -> pd.DataFrame:
    '''
    Gets node availability from F5 LTMs.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        Path to the Ansible private data directory.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df_nodes : pd.DataFrame
        The node availability and associated data.
    '''
    # Get the interface statuses
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the pre-checks
    playbook = f'{play_path}/f5_get_node_availability.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    df_data = dict()
    df_data['device'] = list()
    df_data['partition'] = list()
    df_data['node'] = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout_lines'][0]

            # Create remaining dictionary structure for 'df_data'
            for line in output:
                if 'ltm node' in line and '{' in line:
                    pos = output.index(line)
                    while '}' not in output[pos+1]:
                        key = output[pos+1].split()[0]
                        if not df_data.get(key):
                            df_data[key] = list()
                        pos += 1
                break

            # Populate 'df_data'
            for line in output:
                if 'ltm node' in line and '{' in line:
                    # Add the device to 'df_data'
                    df_data['device'].append(device)

                    # Set the partition and node and add them to 'df_data'
                    if '/' not in line:
                        partition = 'Common'
                        node = line.split()[2]
                    else:
                        partition = line.split()[2].split('/')[1]
                        node = line.split()[2].split('/')[-1]

                    # Add the node to 'df_data'
                    df_data['partition'].append(partition)
                    df_data['node'].append(node)

                    # Add the node details to 'df_data'
                    pos = output.index(line)
                    while '}' not in output[pos+1]:
                        key = output[pos+1].split()[0]
                        value = ' '.join(output[pos+1].split()[1:])
                        df_data[key].append(value)
                        pos += 1

    # Create the dataframe
    df_nodes = pd.DataFrame.from_dict(df_data)

    return df_nodes


def get_pool_availability(username: str,
                          password: str,
                          host_group: str,
                          play_path: str,
                          private_data_dir: str,
                          validate_certs: bool = True) -> pd.DataFrame:
    '''
    Gets pool availability from F5 LTMs.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        Path to the Ansible private data directory.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df_pools : pd.DataFrame
        The pool availability and associated data.
    '''
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the pre-checks
    playbook = f'{play_path}/f5_get_pool_availability.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Parse the pool data and add it to two dictionaries--'pools' and
    # 'pool_members'. The data from those dictionaries will be used to
    # create the two dataframes
    pools = dict()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']
            pools[device] = dict()

            # The playbook runs two commands--show net interface and show net
            # trunk. The output of both commands is in the same event.
            output = event_data['res']['stdout_lines'][0]

            pos = 0
            for line in output:
                if 'Ltm::Pool:' in line:
                    if '/' in line:
                        pool = line.split('/')[-1].strip()
                        partition = line.split('/')[1].split('/')[-1]
                    else:
                        pool = line.split()[-1].strip()
                        partition = 'Common'
                    pools[device][pool] = dict()
                    pools[device][pool]['device'] = device
                    pools[device][pool]['partition'] = partition
                    counter = pos+1
                    while 'Ltm::Pool:' not in output[counter]:
                        _ = output[counter]
                        if _.split()[0] != '|':
                            if 'Availability' in _:
                                pools[device][pool]['availability'] = \
                                    _.split()[-1]
                            if 'State' in _:
                                pools[device][pool]['state'] = _.split()[-1]
                            if 'Reason' in _:
                                pools[device][pool]['reason'] = \
                                    _.split(':')[-1].strip()
                            if 'Minimum Active Members' in _:
                                pools[device][pool]['minimum_active'] = \
                                    _.split()[-1]
                            if 'Current Active Members' in _:
                                pools[device][pool]['current_active'] = \
                                    _.split()[-1]
                            if 'Available Members' in _:
                                pools[device][pool]['available'] = \
                                    _.split()[-1]
                            if 'Total Members' in _:
                                pools[device][pool]['total'] = _.split()[-1]
                        counter += 1
                        if counter == len(output):
                            break
                pos += 1

    df_pools_data = list()
    for key, value in pools.items():
        for k, v in value.items():
            pool = k
            device = v['device']
            available = v['available']
            availability = v['availability']
            current_active = v['current_active']
            minimum_active = v['minimum_active']
            partition = v['partition']
            reason = v['reason']
            state = v['state']
            total = v['total']
            df_pools_data.append([device,
                                  partition,
                                  pool,
                                  availability,
                                  state,
                                  total,
                                  available,
                                  current_active,
                                  minimum_active,
                                  reason])

    cols = ['device',
            'partition',
            'pool',
            'availability',
            'state',
            'total',
            'avail',
            'cur',
            'min',
            'reason']

    df_pools = pd.DataFrame(data=df_pools_data, columns=cols)

    return df_pools


def get_pool_data(username: str,
                  password: str,
                  host_group: str,
                  play_path: str,
                  private_data_dir: str,
                  validate_certs: bool = False) -> pd.DataFrame:
    '''
    Gets F5 pool and pool members.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        Path to the Ansible private data directory.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to False.

    Returns
    -------
    df_pools : pd.DataFrame
        The F5 pools and members.
    '''
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the pre-checks
    playbook = f'{play_path}/f5_get_pool_data.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True,
                                quiet=True)

    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']

            # Extract the command output and clean it up
            output = event_data['res']['stdout_lines'][0]

            output = [_ for _ in output if 'members {' not in _]
            counter = 0
            for line in output:
                if 'ltm pool' in line:
                    if '/' in line:
                        partition = line.split('/')[-2]
                    else:
                        partition = 'Common'

                    pool = line.strip(' {').split()[-1].split('/')[-1]

                    next_line = output[counter+1]
                    if ':' not in next_line and ' {' not in next_line:
                        member = str()
                        port = str()
                        address = str()

                        row = [device,
                               partition,
                               pool,
                               str(),
                               str(),
                               str()]
                        df_data.append(row)

                if ':' in line and ' {' in line:
                    member = line.split()[0]
                    port = line.split(':')[-1].split()[0]
                    address = output[counter+1].split()[-1]

                    row = [device,
                           partition,
                           pool,
                           member,
                           port,
                           address]
                    df_data.append(row)

                counter += 1

    # Create the dataframe
    cols = ['device',
            'partition',
            'pool',
            'member',
            'member_port',
            'address']

    df_pools = pd.DataFrame(data=df_data, columns=cols)

    return df_pools


def get_pool_member_availability(username: str,
                                 password: str,
                                 host_group: str,
                                 play_path: str,
                                 private_data_dir: str,
                                 validate_certs: bool = True) -> pd.DataFrame:
    '''
    Gets F5 pool member availability from F5 LTMs.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        Path to the Ansible private data directory.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df_members : pd.DataFrame
        The pool availability and associated data.
    '''
    # Get the interface statuses
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the pre-checks
    playbook = f'{play_path}/f5_get_pool_member_availability.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    df_data = list()
    # df_dict = dict()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']
            # df_dict[device] = dict()

            output = event_data['res']['stdout_lines'][0]
            pos = 0
            for line in output:
                if 'Ltm::Pool:' in line:
                    # TODO: Separate partition from pool name.
                    if '/' in line:
                        name = line.split('/')
                        partition = name[1].strip()
                        pool = name[-1].strip()
                    else:
                        pool = line.split()[-1].strip()
                        partition = 'Common'

                    # df_dict[device][pool] = dict()
                    counter = pos+1
                    while 'Ltm::Pool:' not in output[counter]:
                        _ = output[counter]
                        if _.split()[0] == '|':
                            if 'Ltm::Pool Member:' in _:
                                member = _.split()[-1]
                            if 'Availability' in _:
                                availability = _.split()[-1]
                                df_data.append([device,
                                                partition,
                                                pool,
                                                member,
                                                availability])
                        counter += 1
                        if counter == len(output):
                            break

                pos += 1

    cols = ['device',
            'partition',
            'pool_name',
            'pool_member',
            'pool_member_state']

    df_members = pd.DataFrame(data=df_data, columns=cols)

    return df_members


def get_pools_and_members(username: str,
                          password: str,
                          host_group: str,
                          play_path: str,
                          private_data_dir: str,
                          validate_certs: bool = False) -> pd.DataFrame:
    '''
    Gets F5 pools and members.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        Path to the Ansible private data directory.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to False.

    Returns
    -------
    df_pools : pd.DataFrame
        The F5 pools and members.
    '''
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the pre-checks
    playbook = f'{play_path}/f5_get_pools_and_members.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True,
                                quiet=True)

    df_data = dict()
    df_data['device'] = list()
    df_data['partition'] = list()
    df_data['pool'] = list()
    df_data['member'] = list()
    df_data['address'] = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout_lines'][0]

            for line in output:
                if 'ltm pool ' in line:
                    pos = output.index(line)+1
                    if '/' in line:
                        name = line.split()[-1]
                        partition = name.split('/')[1]
                        pool = name.split('/')[-1]
                    else:
                        partition = 'Common'
                        pool = line.split()[-1]

                    addresses = False

                    if pos < len(output):
                        while 'ltm pool ' not in output[pos]:
                            if 'address' in output[pos]:
                                addresses = True
                                df_data['device'].append(device)
                                df_data['partition'].append(partition)
                                df_data['pool'].append(pool)
                                member = output[pos-1].split()[0]
                                address = output[pos].split()[-1]
                                df_data['member'].append(member)
                                df_data['address'].append(address)
                            pos += 1
                            if pos == len(output):
                                break
                    if not addresses:
                        df_data['device'].append(device)
                        df_data['partition'].append(partition)
                        df_data['pool'].append(pool)
                        df_data['member'].append(str())
                        df_data['address'].append(str())

    df_pools = pd.DataFrame.from_dict(df_data)
    return df_pools


def get_timezone(username: str,
                 password: str,
                 host_group: str,
                 play_path: str,
                 private_data_dir: str,
                 validate_certs: bool = True) -> pd.DataFrame:
    '''
    Converts a timezone abbreviation (e.g., PDT) to a pytz-recognized
    timezone (e.g., America/Los_Angeles).

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to the device.
    host_group : str
        The Ansible inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the device, timestamp, timezone in abbreviated
        format, and timezone in pytz format.
    '''
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': ['show sys clock']}
    if not validate_certs:
        extravars['validate_certs'] = 'no'

    playbook = f'{play_path}/f5_run_adhoc_command.yml'

    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    df_data = dict()
    df_data['device'] = list()
    df_data['timestamp'] = list()
    df_data['tz_abbreviation'] = list()
    df_data['tz_pytz'] = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']

            timestamp = event_data['res']['stdout_lines'][0][-1]

            df_data['device'].append(device)
            df_data['timestamp'].append(timestamp)
            df_data['tz_abbreviation'].append(timestamp.split()[-2])
            df_data['tz_pytz'].append(hp.tz_abbreviation_to_pytz(timestamp))

    df = pd.DataFrame(df_data)

    return df


def get_vip_availability(username: str,
                         password: str,
                         host_group: str,
                         play_path: str,
                         private_data_dir: str,
                         validate_certs: bool = True) -> pd.DataFrame:
    '''
    Gets VIP availability from F5 LTMs.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to devices.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        Path to the Ansible private data directory.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df_vips : pd.DataFrame
        The VIP availability and associated data.
    '''
    # Get the interface statuses
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = "no"

    # Execute the pre-checks
    playbook = f'{play_path}/f5_get_vip_availability_and_destination.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True,
                                quiet=True)

    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']
            # pools[device] = dict()

            output = event_data['res']['stdout_lines'][0]
            pos = 0
            for line in output:
                if 'Ltm::Virtual Server:' in line:
                    if '/' in line:
                        vip = line.split('/')[-1]
                        partition = line.split('/')[1].split('/')[-1]
                    else:
                        vip = line.split()[-1]
                        partition = 'Common'
                    counter = pos+1
                    while 'Ltm::Virtual Server:' not in output[counter]:
                        _ = output[counter]
                        if 'Availability' in _:
                            availability = _.split()[-1]
                        if 'State' in _:
                            state = _.split()[-1]
                        if 'Reason' in _:
                            reason = _.split(':')[-1].strip()
                        if 'Destination' in _:
                            destination = _.split()[-1].split(':')[0]
                            port = _.split()[-1].split(':')[-1]
                        counter += 1
                        if counter == len(output):
                            break
                    df_data.append([device,
                                    partition,
                                    vip,
                                    destination,
                                    port,
                                    availability,
                                    state,
                                    reason])
                pos += 1

    cols = ['device',
            'partition',
            'vip',
            'destination',
            'port',
            'availability',
            'state',
            'reason']

    df_vips = pd.DataFrame(data=df_data, columns=cols)

    return df_vips


def get_vip_destinations(db_path: str) -> pd.DataFrame:
    '''
    Creates a summary view of the VIP destinations on F5 LTMs. It pulls the
    data from the 'f5_get_vip_availability' table. The view can be queried
    just like a regular table.

    Parameters
    ----------
    db_path : str
        The path to the database.

    Returns
    -------
    result : pd.DataFrame
        A dataframe containing the view's data.
    '''
    # Connect to the database
    con = hp.connect_to_db(db_path)
    cur = con.cursor()

    # Create the view and return the results so the user can see that the
    # operation was successful
    cur.execute('''create view if not exists VIP_DESTINATIONS
                   as
                   select timestamp,
                          device,
                          partition,
                          vip,
                          destination,
                          port
                   from BIGIP_VIP_AVAILABILITY
                   ''')

    query = 'select * from BIGIP_VIP_AVAILABILITY'

    result = pd.read_sql(query, con)

    return result


def get_vip_summary(username: str,
                    password: str,
                    host_group: str,
                    play_path: str,
                    private_data_dir: str,
                    df_pools: pd.DataFrame,
                    validate_certs: bool = False) -> pd.DataFrame:
    '''
    Gets F5 summary.

    Args:
        username (str):         The username to login to devices.
        password (str):         The password to login to devices.
        host_group (str):       The inventory host group.
        play_path (str):        The path to the playbooks directory.
        private_data_dir (str): Path to the Ansible private data directory.
        df_pools (pd.DataFrame): A DataFrame containing a summary of the pools
                                 and members. This is created with the
                                 'f5_build_pool_table' function.
        validate_certs (bool):  Whether to validate SSL certificates. Defaults
                                to False.

    Returns:
        df_vips (pd.DataFrame): The F5 VIP summary.
    '''
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    # Execute the pre-checks
    playbook = f'{play_path}/f5_get_vip_summary.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True,
                                quiet=True)

    df_data = dict()
    df_data['device'] = list()
    df_data['partition'] = list()
    df_data['vip'] = list()
    df_data['destination'] = list()
    df_data['pool'] = list()
    df_data['member'] = list()
    df_data['address'] = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout_lines'][0]

            for line in output:
                if 'ltm virtual ' in line:
                    name = line.split()[-2]
                    if '/' in name:
                        partition = name.split('/')[1]
                        vip = name.split('/')[-1]
                    else:
                        partition = 'Common'
                        vip = name

                    destination = str()
                    pool = str()
                    member = str()
                    address = str()

                    pos = output.index(line)+1
                    if pos < len(output):
                        while 'ltm virtual ' not in output[pos]:
                            if output[pos].split()[0] == 'destination':
                                destination = output[pos].split('/')[-1]
                            if output[pos].split()[0] == 'pool':
                                pool = output[pos].split('/')[-1]
                            pos += 1
                            if pos == len(output):
                                break
                    if pool:

                        df_members = df_pools.loc[(df_pools['partition'] ==
                                                   partition) &
                                                  (df_pools['pool'] == pool)]
                        if len(df_members) > 0:
                            for idx, row in df_members.iterrows():
                                member = row['member']
                                address = row['address']
                                df_data['device'].append(device)
                                df_data['partition'].append(partition)
                                df_data['vip'].append(vip)
                                df_data['destination'].append(destination)
                                df_data['pool'].append(pool)
                                df_data['member'].append(member)
                                df_data['address'].append(address)
                    df_data['device'].append(device)
                    df_data['partition'].append(partition)
                    df_data['vip'].append(vip)
                    df_data['destination'].append(destination)
                    df_data['pool'].append(pool)
                    df_data['member'].append(member)
                    df_data['address'].append(address)

    df_vips = pd.DataFrame.from_dict(df_data)

    return df_vips


def get_vlan_db(username: str,
                password: str,
                host_group: str,
                play_path: str,
                private_data_dir: str,
                validate_certs: bool = True) -> pd.DataFrame:
    '''
    Gets the VLAN database on F5 LTMs.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to the device.
    host_group : str
        The inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    validate_certs : bool, optional
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df_vips : pd.DataFrame
        A Pandas DataFrame containing the VLAN database.
    '''
    # Get the interface statuses
    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    playbook = f'{play_path}/f5_get_vlan_database.yml'
    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    df_data = list()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']

            output = event_data['res']['stdout_lines'][0]

            pos = 0
            for line in output:
                if 'Net::Vlan:' in line:
                    if 'Interface Name' in output[pos+1]:
                        name = output[pos+1].split()[-1]
                    else:
                        name = str()
                    if output[pos+2].split()[0] == 'Tag':
                        tag = output[pos+2].split()[-1]
                    else:
                        tag = str()
                    # TODO: Add support for status and interfaces
                    df_data.append([device,
                                    tag,
                                    name,
                                    str(),
                                    str()])
                pos += 1

    cols = ['device',
            'id',
            'name',
            'status',
            'ports']
    df_vlans = pd.DataFrame(data=df_data, columns=cols)

    return df_vlans


def get_vlans(username: str,
              password: str,
              host_group: str,
              play_path: str,
              private_data_dir: str,
              validate_certs: bool = True) -> pd.DataFrame:
    '''
    Gets the VLANs on F5 LTMs.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to the device.
    host_group : str
        The Ansible inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    validate_certs : bool, optional:
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df : pd.DataFrame
        A Pandas DataFrame containing the VLANs.
    '''
    commands = [
        'list net vlan /*/*',
        'show net vlan /*/*'
    ]

    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'commands': commands}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    playbook = f'{play_path}/f5_run_adhoc_commands.yml'

    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Create a dictionary to store each self IP.
    data = dict()

    # Create a dictionary to store the data for `df`
    df_data = dict()

    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']
            device = event_data['remote_addr']
            data[device] = list()
            outputs = event_data['res']['stdout_lines']

            # Parse the output of 'list net vlan /*/*' and add it to df_data.
            output = outputs[0]

            counter = 0
            for line in output:
                if line[:8] == 'net vlan':
                    block = list()
                    pos = counter
                    while output[pos][0] != '}':
                        block.append(output[pos])
                        pos += 1
                    block.append('}')

                    # Convert the block to a dictionary then flatten it.
                    block = '\n'.join(block)
                    block = convert_tmsh_output_to_dict(block)

                    for key, value in block.items():
                        self_name = key.split()[-1]
                        value['name'] = self_name

                    # Add the device name to `value`, then add the contents of
                    # 'block' to 'df_data'.
                    value['device'] = device
                    data[self_name] = value
                    break

                counter += 1

    # Create `df`.
    df = pd.DataFrame.from_dict(df_data).astype(str)

    # Make `device` the first column, then return `df`.
    col_1 = df.pop('device')
    df.insert(0, 'device', col_1)

    return df


def inventory(username: str,
              password: str,
              host_group: str,
              play_path: str,
              private_data_dir: str,
              validate_certs: bool = True) -> pd.DataFrame:
    '''
    Gets a partial hardware inventory from F5 load balancers.

    Parameters
    ----------
    username : str
        The username to login to devices.
    password : str
        The password to login to the device.
    host_group : str
        The Ansible inventory host group.
    play_path : str
        The path to the playbooks directory.
    private_data_dir : str
        The path to the Ansible private data directory.
    validate_certs : bool, optional:
        Whether to validate SSL certificates. Defaults to True.

    Returns
    -------
    df : pd.DataFrame
        A Pandas DataFrame containing the VLANs.
    '''
    command = 'show sys hardware | grep -A 20 "Platform"'

    extravars = {'username': username,
                 'password': password,
                 'host_group': host_group,
                 'command': command}

    if not validate_certs:
        extravars['validate_certs'] = 'no'

    playbook = f'{play_path}/f5_run_adhoc_command.yml'

    runner = ansible_runner.run(private_data_dir=private_data_dir,
                                playbook=playbook,
                                extravars=extravars,
                                suppress_env_files=True)

    # Create a dictionary to store the data.
    df_data = dict()
    columns = ['device',
               'name',
               'ip',
               'bios_revision',
               'base_mac',
               'appliance_type',
               'appliance_serial',
               'part_number',
               'host_board_serial',
               'host_board_part_revision']
    for col in columns:
        df_data[col] = list()

    # Create a mapping of text in the data to the desired column names.
    mapping = {
        'Name': 'name',
        'BIOS Revision': 'bios_revision',
        'Base MAC': 'base_mac',
        'Type': 'appliance_type',
        'Appliance Serial': 'appliance_serial',
        'Part Number': 'part_number',
        'Host Board Serial': 'host_board_serial',
        'Host Board Part Revision': 'host_board_part_revision'
    }

    # Parse the output and add it to df_data.
    for event in runner.events:
        if event['event'] == 'runner_on_ok':
            event_data = event['event_data']

            device = event_data['remote_addr']
            df_data['device'].append(device)
            device_ip = hp.ansible_host_to_ip(device)
            df_data['ip'].append(device_ip)

            data = event_data['res']['stdout_lines'][0]

            for line in data:
                for key, value in mapping.items():
                    if key in line:
                        df_data[value].append(line.split(key)[1].strip())

    # Determine the maximum length of any list in df_data
    max_length = max(len(lst) for lst in df_data.values())

    # Ensure all lists in df_data are of the same length
    for key in df_data:
        while len(df_data[key]) < max_length:
            df_data[key].append('')  # Append an empty string or another placeholder

    # Create the dataframe and return it.
    df = pd.DataFrame(df_data)

    return df
