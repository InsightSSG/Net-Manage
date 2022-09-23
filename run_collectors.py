#!/usr/bin/env python3

'''
Define collectors and map them to the correct function in colletors.py.
'''

import argparse
import collectors as cl
import datetime as dt
import helpers as hp
import os
import readline

from tabulate import tabulate

# Protect creds by not writing history to .python_history
readline.write_history_file = lambda *args: None


def define_collectors():
    '''
    Creates a list of collectors.

    Args:
        None

    Returns:
        collectors (list):  A list of collectors.
    '''
    collectors = [
                  'arp_table',
                  'cam_table',
                  'f5_pool_availability',
                  'f5_pool_member_availability',
                  'f5_vip_availability',
                  'f5_vip_destinations',
                  'interface_description',
                  'interface_status',
                  'port_channel_data',
                  'vlan_database',
                  'vpc_state',
                  ]
    return collectors


def collect(ansible_os,
            collector,
            username,
            password,
            hostgroup,
            play_path,
            private_data_dir,
            nm_path,
            ansible_timeout='300',
            validate_certs=True):
    '''
    This function calls the test that the user requested.

    Args:
        os (str):               The ansible_network_os variable
        collector (str):        The name of the test that the user requested
        username (str):         The username to login to devices
        password (str):         The password to login to devices
        host_group (str):       The inventory host group
        play_path (str):        The path to the playbooks directory
        private_data_dir (str): The path to the Ansible private data directory
        nm_path (str):          The path to the Net-Manage repository
        interface (str):        The interface (defaults to all interfaces)
        validate_certs (bool):  Whether to validate SSL certs (used for F5s)
    '''
    if collector == 'cam_table':
        if ansible_os == 'cisco.ios.ios':
            result = cl.ios_get_cam_table(username,
                                          password,
                                          hostgroup,
                                          play_path,
                                          private_data_dir,
                                          nm_path)

        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_cam_table(username,
                                           password,
                                           hostgroup,
                                           play_path,
                                           private_data_dir,
                                           nm_path)

    if collector == 'arp_table':
        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_arp_table(username,
                                           password,
                                           hostgroup,
                                           nm_path,
                                           play_path,
                                           private_data_dir)

        if ansible_os == 'bigip':
            result = cl.f5_get_arp_table(username,
                                         password,
                                         hostgroup,
                                         nm_path,
                                         play_path,
                                         private_data_dir,
                                         validate_certs=False)

        if ansible_os == 'paloaltonetworks.panos':
            result = cl.panos_get_arp_table(username,
                                            password,
                                            hostgroup,
                                            play_path,
                                            private_data_dir)

    if collector == 'f5_pool_availability':
        if ansible_os == 'bigip':
            result = cl.f5_get_pool_availability(username,
                                                 password,
                                                 hostgroup,
                                                 play_path,
                                                 private_data_dir,
                                                 validate_certs=False)

    if collector == 'f5_pool_member_availability':
        if ansible_os == 'bigip':
            result = cl.f5_get_pool_member_availability(username,
                                                        password,
                                                        hostgroup,
                                                        play_path,
                                                        private_data_dir,
                                                        validate_certs=False)

    if collector == 'f5_vip_availability':
        if ansible_os == 'bigip':
            result = cl.f5_get_vip_availability(username,
                                                password,
                                                hostgroup,
                                                play_path,
                                                private_data_dir,
                                                validate_certs=False)

    if collector == 'f5_vip_destinations':
        if ansible_os == 'bigip':
            result = cl.f5_get_vip_destinations(username,
                                                password,
                                                hostgroup,
                                                play_path,
                                                private_data_dir,
                                                validate_certs=False)

    if collector == 'interface_description':
        if ansible_os == 'cisco.ios.ios':
            result = cl.ios_get_interface_descriptions(username,
                                                       password,
                                                       hostgroup,
                                                       play_path,
                                                       private_data_dir)

        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_interface_descriptions(username,
                                                        password,
                                                        hostgroup,
                                                        play_path,
                                                        private_data_dir)

        if ansible_os == 'bigip':
            result = cl.f5_get_interface_descriptions(username,
                                                      password,
                                                      hostgroup,
                                                      nm_path,
                                                      play_path,
                                                      private_data_dir,
                                                      reverse_dns=False,
                                                      validate_certs=False)

    if collector == 'interface_status':
        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_interface_status(username,
                                                  password,
                                                  hostgroup,
                                                  play_path,
                                                  private_data_dir)

        if ansible_os == 'bigip':
            result = cl.f5_get_interface_status(username,
                                                password,
                                                hostgroup,
                                                play_path,
                                                private_data_dir,
                                                validate_certs=False)

    if collector == 'find_uplink_by_ip':
        if ansible_os == 'cisco.ios.ios':
            result = cl.ios_find_uplink_by_ip(username,
                                              password,
                                              hostgroup,
                                              play_path,
                                              private_data_dir)

    if collector == 'port_channel_data':
        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_port_channel_data(username,
                                                   password,
                                                   hostgroup,
                                                   play_path,
                                                   private_data_dir)

    if collector == 'vpc_state':
        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_vpc_state(username,
                                           password,
                                           hostgroup,
                                           play_path,
                                           private_data_dir)

    if collector == 'vlan_database':
        if ansible_os == 'cisco.nxos.nxos':
            result = cl.nxos_get_vlan_db(username,
                                         password,
                                         hostgroup,
                                         play_path,
                                         private_data_dir)

        if ansible_os == 'bigip':
            result = cl.f5_get_vlan_db(username,
                                       password,
                                       hostgroup,
                                       play_path,
                                       private_data_dir,
                                       validate_certs=False)

    return result


def create_parser():
    '''
    Create command line arguments.

    Args:
        None

    Returns:
        args:   Parsed command line arguments
    '''
    # Create the parser for command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database',
                        help='''The database name. Defaults to
                                YYYY-MM-DD.db.''',
                        default=f'{str(dt.datetime.now()).split()[0]}.db',
                        action='store'
                        )
    parser.add_argument('-o', '--out_dir',
                        help='''The directory to save output to (the filename
                                will be auto-generated). The database will also
                                be saved here.''',
                        default=os.path.expanduser('~/output'),
                        action='store'
                        )
    parser.add_argument('-u', '--username',
                        help='''The username for connecting to the devices. If
                                missing, script will prompt for it.''',
                        action='store'
                        )
    parser.add_argument('-P', '--password',
                        help='''The password for connecting to the devices.
                                This is included for external automation, but I
                                do not recommend using it when running the
                                script manually. If you do, then your password
                                could show up in the command history.''',
                        action='store'
                        )
    requiredNamed = parser.add_argument_group('required named arguments')
    requiredNamed.add_argument('-c', '--collectors',
                               help='''A comma-delimited list of collectors to
                                       run.''',
                               required=True,
                               action='store'
                               )
    requiredNamed.add_argument('-H', '--hostgroups',
                               help='A comma-delimited list of hostgroups',
                               required=True,
                               action='store'
                               )
    requiredNamed.add_argument('-n', '--nm_path',
                               help='The path to the Net-Manage repository',
                               required=True,
                               action='store'
                               )
    requiredNamed.add_argument('-p', '--private_data_dir',
                               help='''The path to the Ansible private data
                                       directory (I.e., the directory
                                       containing the 'inventory' and 'env'
                                       folders).''',
                               required=True,
                               action='store'
                               )
    args = parser.parse_args()
    return args


def arg_parser(args):
    '''
    Extract system args and assign variable names.

    Args:
        args (args):        Parsed command line arguments

    Returns:
        vars_dict (dict):   A dictionary containing arg variables
    '''
    # Set the collectors
    collectors = [c.strip() for c in args.collectors.split(',')]

    # Set the hostgroups
    hostgroups = [h.strip() for h in args.hostgroups.split(',')]

    # Set the nm_path, out_dir and private_data_dir
    nm_path = os.path.expanduser(args.nm_path)
    out_dir = os.path.expanduser(args.out_dir)
    private_data_dir = os.path.expanduser(args.private_data_dir)

    # Set the user credentials
    # TODO: Add support for using different credentials for each device or
    #       hostgroup. That is a common scenario.
    if args.username:
        username = args.username
    else:
        username = hp.get_username()
    if args.password:
        password = args.password
    else:
        password = hp.get_password()

    # Set the database path
    db = f'{out_dir}/{args.database}'

    return collectors, db, hostgroups, nm_path, out_dir, username, password,\
        private_data_dir


def main():
    args = create_parser()
    # Parse the command line arguments and set other variables
    collectors, db, hostgroups, nm_path, out_dir, username, password,\
        private_data_dir = arg_parser(args)
    play_path = f'{nm_path}/playbooks'

    # Ensure that any pre-requisite collectors are set
    collectors = hp.set_dependencies(collectors)

    df_collectors = hp.ansible_create_collectors_df(hostgroups,
                                                    collectors)

    df_vars = hp.ansible_create_vars_df(hostgroups, private_data_dir)

    print('COLLECTORS:')
    print(tabulate(df_collectors,
                   headers='keys',
                   tablefmt='psql'))

    print('COLLECTOR VARIABLES')
    print(tabulate(df_vars,
                   headers='keys',
                   tablefmt='psql'))

    # Set the timestamp. This is for database queries. Setting it a single time
    # at the start of the script will allow all collectors to have the same
    # timestamp.
    ts = dt.datetime.now()
    ts = ts.strftime('%Y-%m-%d_%H%M')

    # Execute collectors and store the output in a SQLite database.
    # Collectors are executed by column. If column_1 is 'interface_status' and
    # column_2 is 'interface_description', the interface statuses for all
    # hostgroups will be gathered, then the interface descriptions for all
    # hostgroups, and so on.
    for idx, row in df_collectors.iterrows():
        collector = idx
        hostgroups = row['hostgroups'].split(',')
        for group in hostgroups:
            ansible_os = df_vars.loc[[group]]['ansible_network_os'].values[0]

            result = collect(ansible_os,
                             collector,
                             username,
                             password,
                             group,
                             play_path,
                             private_data_dir,
                             nm_path)
            # Set the timestamp as the index
            new_idx = list()
            for i in range(0, len(result)):
                new_idx.append(ts)

            # Display the output to the console
            result['timestamp'] = new_idx
            result = result.set_index('timestamp')
            # print(tabulate(result, headers='keys', tablefmt='psql'))

            # Add the output to the database
            con = hp.connect_to_db(db)

            # Add the dataframe to the database
            table = collector.upper()
            result.to_sql(table, con, if_exists='append')
            con.commit()
            con.close()


if __name__ == '__main__':
    main()
