#!/usr/bin/env python3

'''
Define Cisco DNAC collectors.
'''

import dnacentersdk
import pandas as pd
import sys


def create_api_object(base_url: str,
                      username: str,
                      password: str,
                      verify: bool = True) -> \
                      dnacentersdk.api.DNACenterAPI:
    """
    Create the object for making API calls to Cisco DNAC appliances.

    Parameters
    ----------
    base_url : str
        The URL for the DNAC appliance.
    username : str
        The username used to authenticate to the DNAC appliance.
    password : str
        The password user to authenticate to the DNAC appliance.
    verify : bool, optional
        Whether to verify SSL certificates. Defaults to True.

    Returns
    -------
    dnac : dnacentersdk.api.DNACenterAPI
        The object used for API calls.

    Examples
    --------
    >>> from dnacentersdk import api
    >>> dnac = create_dnac_api_object('https://sandboxdnac.cisco.com/',
                                      username='devnetuser',
                                      password='Cisco123!',
                                      verify=False)
    >>> print(type(dnac))
    <class 'dnacentersdk.api.DNACenterAPI'>
    """
    try:
        dnac = dnacentersdk.api.DNACenterAPI(base_url=base_url,
                                             username=username,
                                             password=password,
                                             verify=verify)
        return dnac
    except dnacentersdk.exceptions.ApiError as e:
        print(str(e))
        sys.exit()
    except Exception as e:
        print(str(e))
        sys.exit()


def devices_inventory(base_url: str,
                      username: str,
                      password: str,
                      platform_ids: list = [],
                      verify: bool = True) -> pd.DataFrame:
    """
    Get the list of devices from Cisco DNAC.

    Parameters
    ----------
    base_url : str
        The URL for the DNAC appliance.
    username : str
        The username used to authenticate to the DNAC appliance.
    password : str
        The password user to authenticate to the DNAC appliance.
    platform_ids : list, optional
        A list of platform_ids. If not specified then all devices will be
        returned.
    verify : bool, optional
        Whether to verify SSL certificates. Defaults to True.

    Returns
    -------
    df (pd.DataFrame):
        A dataframe containing the device list.
    """
    dnac = create_api_object(base_url, username, password, verify=verify)
    if platform_ids:
        devices = dnac.devices.get_device_list(platform_id=platform_ids)
    else:
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


def devices_modules(base_url: str,
                    username: str,
                    password: str,
                    platform_ids: list = [],
                    allow_partial_match: bool = False,
                    verify: bool = True) -> pd.DataFrame:
    """
    Gets the module details for devices in DNAC.

    Parameters
    ----------
    base_url : str
        The URL for the DNAC appliance.
    username : str
        The username used to authenticate to the DNAC appliance.
    password : str
        The password user to authenticate to the DNAC appliance.
    platform_ids (list, optional):
        A list of platform_ids. If not specified then all devices will be
        returned.
    allow_partial_match : bool, optional
        If True, then partial matches inside of 'platform_ids' will be
        returned.
    verify : bool, optional
        Whether to verify SSL certificates. Defaults to True.

    Returns
    -------
    df (pd.DataFrame):
        A dataframe containing the details for the device modules.

    Notes
    -----
    If the 'platform_ids' arg is not passed to the function, then the modules
    for all devices in the DNAC inventory will be returned.

    Even if 'platform_ids' is not empty, this function gets all of the devices,
    then filters them based on the elements in 'platform_ids'. This might cause
    performance issues with very large inventories. If so, we can modify the
    function to only query devices with the listed elements in 'platform_ids'.
    """
    # If 'platform_ids' is empty then get all devices from DNAC.
    df_devices = devices_inventory(base_url, username, password, verify=verify)

    if platform_ids and not allow_partial_match:
        df_devices = df_devices[df_devices['platformId'].isin(platform_ids)]
    if platform_ids and allow_partial_match:
        df_devices = df_devices[df_devices['platformId'].
                                str.contains('|'.join(platform_ids))]

    # Create two lists. 'data' holds the modules for each device. 'df_data'
    # will contain the formatted data that is used to create the DataFrame.
    # It is not ideal to iterate over the responses twice, but it is necessary
    # since the DNAC API does not always return the same keys for each module
    # in its response.
    data = list()
    df_data = dict()

    # Iterate over the devices, getting the module details for each one.
    dnac = create_api_object(base_url, username, password, verify=verify)
    for idx, row in df_devices.iterrows():
        hostname = row['hostname']
        platform_id = row['platformId']
        _id = row['id']
        response = dnac.devices.get_modules(_id)['response']
        for module in response:
            # Store the module along with the associated hostname and deviceId
            # in 'data'.
            module['platformId'] = platform_id
            module['hostname'] = hostname
            module['deviceId'] = _id
            data.append(module)

            # Iterate over the keys in 'module'. If the key does not exist in
            # 'df_data' then add it.
            for key in module:
                if not df_data.get(key):
                    df_data[key] = list()

    # Iterate over the list of modules inside 'data', adding them to 'df_data'.
    for module in data:
        for key in df_data:
            df_data[key].append(module.get(key))

    # Create the DataFrame, then move the 'hostname' and 'deviceId' columns to
    # the beginning of the DataFrame.
    df = pd.DataFrame.from_dict(df_data)
    if len(df) > 0:
        to_move = ['platformId', 'hostname', 'deviceId']
        columns = df.columns.to_list()
        for column in to_move:
            columns.remove(column)
        new_column_order = to_move + columns
        df = df[new_column_order]

    return df
