#!/usr/bin/env python3

'''
Define Cisco DNAC collectors.
'''

import dnacentersdk
import pandas as pd


def create_dnac_api_object(base_url: str,
                           username: str,
                           password: str,
                           verify: bool = True) -> \
                            dnacentersdk.api.DNACenterAPI:
    """
    Create the object for making API calls to Cisco DNAC appliances.

    Args:
    ----
    base_url (str):
        The URL for the DNAC appliance.
    username (str):
        The username used to authenticate to the DNAC appliance.
    password (str):
        The password user to authenticate to the DNAC appliance.
    verify (bool, optional):
        Whether to verify SSL certificates. Defaults to True.

    Returns:
    ----
    dnac (dnacentersdk.api.DNACenterAPI):
        The object used for API calls.

    Examples:
    ----
    >>> from dnacentersdk import api
    >>> dnac = create_dnac_api_object('https://sandboxdnac.cisco.com/',
                                      username='devnetuser',
                                      password='Cisco123!',
                                      verify=False)
    >>> print(type(dnac))
    <class 'dnacentersdk.api.DNACenterAPI'>
    """
    dnac = dnacentersdk.api.DNACenterAPI(base_url=base_url,
                                         username=username,
                                         password=password,
                                         verify=verify)
    return dnac


def get_devices(base_url: str,
                username: str,
                password: str,
                verify: bool = True) -> pd.DataFrame:
    """
    Get the list of devices from Cisco DNAC.

    Args:
    ----
    base_url (str):
        The URL for the DNAC appliance.
    username (str):
        The username used to authenticate to the DNAC appliance.
    password (str):
        The password user to authenticate to the DNAC appliance.
    verify (bool, optional):
        Whether to verify SSL certificates. Defaults to True.

    Returns:
    ----
    df (pd.DataFrame):
        A dataframe containing the device list.
    """
    dnac = create_dnac_api_object(base_url=base_url,
                                  username=username,
                                  password=password,
                                  verify=verify)
    devices = dnac.devices.get_device_list()

    # Create a dictionary called 'df_data', and add all of the keys from
    # 'devices' to it. The value of each key will be a list.
    df_data = dict()
    for item in devices['response']:
        for key in item:
            df_data[key] = list()

    # Populate 'df_data' with the values from 'devices'.
    for item in devices['response']:
        for key, value in item.items():
            df_data[key].append(value)

    # Create the DataFrame and return it.
    df = pd.DataFrame.from_dict(df_data)
    return df
