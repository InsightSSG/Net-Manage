#!/usr/bin/env python3

import requests
from getpass import getpass
from pprint import pprint
from time import sleep


def main():
    # Get required variables
    username = input('Enter your username: ')
    password = getpass('Enter your password: ')
    device = input('Enter the name or IP of the device to connect to: ')
    device = f'https://{device}'

    # Since this is a test environment, I disabled SSL cert verification and
    # suppressed warnings. These variables should be commented out in a
    # production environment unless you are using self-signed certificates.
    verify = False
    requests.urllib3.disable_warnings()

    # Get an F5 token to use for future API calls
    url = f'{device}/mgmt/shared/authn/login'
    content = {'username': username,
               'password': password,
               'loginProviderName': 'tmos'}
    response = requests.post(url, json=content, verify=False)
    token = response.json()['token']['token']
    
    # Create the header to use for future API calls
    header = {'X-F5-Auth-Token': token}

    # There is a bug in some versions of F5 code that cause API calls to fail
    # if the token is used within 1 second of requesting it.
    # See: https://cdn.f5.com/product/bugtracker/ID1108181.html
    sleep(1.5)

    # Get a list of collections (node, pool, VIP, etc) within the LTM module
    url = f'{device}/mgmt/tm/ltm'
    response = requests.get(url, headers=header, verify=False)
    pprint(response.json())

    # Get a list of all nodes within the all partitions LTM module
    url = f'{device}/mgmt/tm/ltm/node'
    response = requests.get(url, headers=header, verify=False)
    # pprint(response.json())

    # Get a list of all nodes within the /Common partition
    url = f'{device}/mgmt/tm/ltm/node?$filter=partition eq Common'
    response = requests.get(url, headers=header, verify=False)
    # pprint(response.json())

    # The same format applies to VIPs, pools, SNAT, and any other collectors
    # within the LTM module. Here are two more examples. The first collects the
    # pools and the second collects the VIPs.
    url = f'{device}/mgmt/tm/ltm/pool'
    response = requests.get(url, headers=header, verify=False)
    # pprint(response.json())

    url = f'{device}/mgmt/tm/ltm/virtual'
    response = requests.get(url, headers=header, verify=False)
    # pprint(response.json())

if __name__ == '__main__':
    main()
