'''
A library of generic helper functions for dynamic runbooks.
'''

import os
import sys
from datetime import datetime as dt
from getpass import getpass


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


def get_hostgroup():
    '''
    Gets the Ansible hostgroup

    Args:
        None

    Returns:
        hostgroup (str): The Ansible hostgroup
    '''
    host_group = input('Enter the name of the host group in the hosts file: ')
    return host_group


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


def set_filepath(filepath=None):
    '''
    Creates a filename with the date and time added to a path the user
    provides. The function assumes the last "." in a filename is the extension.

    Args:
        filepath (str):     (Optional): The base filepath. If it is not
                            specified, then it will prompt the user to enter
                            it. This is done for the convenience of those who
                            call this function from a Jupyter notebook and do
                            not want to re-enter the filepath every time they
                            re-run a cell that generates a file.

    Returns:
        filepath (str):     The full path to the modified filename.
    '''
    # Get the full path to the file, including the filename
    if not filepath:
        filepath = input('Enter the full file path, including the filename')
    # Convert '~' to the user's home folder
    if '~' in filepath:
        filepath = filepath.replace('~', os.path.expanduser('~'))
    # Set the prefix in YYYY-MM-DD_HHmm format
    prefix = dt.now().strftime("%Y-%m-%d_%H%M")
    # Extract the base path to the filename
    filepath = filepath.split('/')
    filename = filepath[-1]
    if len(filepath) > 2:
        filepath = '/'.join(filepath[:-1])
    else:
        filepath = filepath[0]
    # Extract the filename and extension from 'filepath'
    filename = filename.split('.')
    extension = filename[-1]
    if len(filename) > 2:
        filename = '.'.join(filename[:-1])
    else:
        filename = filename[0]
    # Return the modified filename
    filepath = f'{filepath}/{prefix}_{filename}.{extension}'
    return filepath


def get_net_manage_path():
    '''
    Set the absolute path to the Net-Manage repository.

    Args:
        None

    Returns:
        nm_path (str):  The absolute path to the Net-Manage repository.
    '''
    nm_path = input("Enter the absolute path to the Net-Manage repository: ")
    if '~' in nm_path:
        nm_path = os.path.expanduser(nm_path)
    return nm_path