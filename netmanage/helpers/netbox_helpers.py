#!/usr/bin/env python3

"""A collection of helper functions for Netbox operations.

"""

import pandas as pd
import re
from netmanage.collectors import netbox_collectors as nbc


def get_prefix_custom_field_states(nb_path: str,
                                   token: str,
                                   f_name: str) -> pd.DataFrame:
    '''
    Gets the values of a single custom field for all prefixes.

    Queries the API to get the value of a custom field for all prefixes.
    The original purpose of this function was to get the Infoblox Object
    Reference number for networks that had been synchronized from Infoblox
    to Netbox. However, it has many other potential uses.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.
    f_name : str
        The name of the custom field to query.

    Returns
    -------
    df : pd.DataFrame
        A Pandas DataFrame containing the object reference number for each
        prefix ID.

    See Also
    --------
    netbox_collectors.netbox_get_ipam_prefixes : A function to get all
                                                 prefixes from a Netbox
                                                 instance.

    Examples
    --------
    >>> df = get_prefix_custom_field_states(nb_path, token, f_name)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    '''
    # Get the IPAM prefixes from Netbox
    result = nbc.netbox_get_ipam_prefixes(nb_path, token)

    # Create a dataframe containing the prefix IDs and 'f_name' values
    df = result[['id', f'custom_fields_{f_name}']].copy()

    return df


def make_nb_url_compliant(string: str):
    """
    Replaces all characters except letters, numbers, underscores,
    and hyphens with hyphens.

    Parameters
    ----------
    string : str
        string to make URL compliant for NB
    """
    return re.sub(r"[^\w\-]", "-", string)


def get_table_prefix_to_device_mfg():
    return {
        'ASA': 'CISCO',
        'BIGIP': 'F5 Networks',
        'IOS': 'CISCO',
        'MERAKI': 'MERAKI',
        'NXOS': 'CISCO',
        'PANOS': 'PALO ALTO',
    }


def get_device_types():
    return {
        'MERAKI': {
            'MS120-48FP': {
                'u_height': 1,
                'is_full_depth': False,
                'airflow': 'front-to-rear',
                'weight': '10.8',
                'weight_unit': 'lb',
                'slug': 'ms120-48fp'
            },
            'MS120-48LP': {
                'u_height': 1,
                'is_full_depth': False,
                'airflow': 'front-to-rear',
                'weight': '10.8',
                'weight_unit': 'lb',
                'slug': 'ms120-48lp'
            },
            "MR33": {
                "u_height": 1,
                "is_full_depth": False,
                "airflow": "front-to-rear",
                "weight": "2.7",
                "weight_unit": "lb",
                "slug": "mr33",
            },
            "MR42": {
                "u_height": 1,
                "is_full_depth": False,
                "airflow": "front-to-rear",
                "weight": "2.7",
                "weight_unit": "lb",
                "slug": "mr42",
            },
            "MX450": {
                "u_height": 1,
                "is_full_depth": True,
                "airflow": "front-to-rear",
                "weight": "20.9",
                "weight_unit": "lb",
                "slug": "mx450",
            },
            "MX64": {
                "u_height": 1,
                "is_full_depth": True,
                "airflow": "front-to-rear",
                "weight": "20.9",
                "weight_unit": "lb",
                "slug": "mx64",
            },
            "MX65": {
                "u_height": 1,
                "is_full_depth": True,
                "airflow": "front-to-rear",
                "weight": "20.9",
                "weight_unit": "lb",
                "slug": "mx65",
            },
            "MX84": {
                "u_height": 1,
                "is_full_depth": True,
                "airflow": "front-to-rear",
                "weight": "20.9",
                "weight_unit": "lb",
                "slug": "mx84",
            },
        },
        'CISCO': {
            'FPR-1120': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 8,
                'weight_unit': 'lb'
            },
            'ASR1002-X': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 17.36,
                'weight_unit': 'lb'
            },
            'ASR1002-HX': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 39.05,
                'weight_unit': 'lb'
            },
            'N2K-C2248TP-E-1GE': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 12.7,
                'weight_unit': 'lb'
            },
            'N9K-C93180YC-FX': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 47.5,
                'weight_unit': 'lb'
            },
            'WS-C2960X-24TS-LL': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 10.8,
                'weight_unit': 'lb'
            },
            'CISCO1921/K9': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 2.9,
                'weight_unit': 'lb'
            },
            'WS-C2960L-24PS-LL': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 11.2,
                'weight_unit': 'lb'
            },
            'C9410R': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 33.1,
                'weight_unit': 'lb'
            },
            'C8500-12X': {
                'u_height': 12,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 152,
                'weight_unit': 'lb'
            },
            'WS-C2960-24TT-L': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 10.8,
                'weight_unit': 'lb'
            },
            'ASR1001-X': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 6.6,
                'weight_unit': 'lb'
            },
            'WS-C2960L-48TS-LL': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 12.7,
                'weight_unit': 'lb'
            },
            'C9500-48Y4C': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 37.8,
                'weight_unit': 'lb'
            },
            'N5K-C5696Q': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '47.5',
                'weight_unit': 'lb',
                'slug': 'n5k-c5696q'
            },
            'N77-C7706': {
                'u_height': 9,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '300',
                'weight_unit': 'lb',
                'slug': 'n77-c7706'
            },
            'N2K-C2348UPQ-10GE': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '10.8',
                'weight_unit': 'lb',
                'slug': 'n2k-c2348upq-10ge'
            },
            'N5K-C5596UP': {
                'u_height': 2,
                'is_full_depth': False,
                'airflow': 'front-to-rear',
                'weight': '47.5',
                'weight_unit': 'lb',
                'slug': 'n5k-c5596up'
            },
            'CISCO2901/K9': {
                'u_height': 1,
                'airflow': 'front-to-rear',
                'is_full_depth': False,
                'weight': 9.5,
                'weight_unit': 'lb',
            },
            'ASA5555': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 25,
                'weight_unit': 'lb',
                'slug': 'asa5555'
            },
            'WS-C2960L-24TS': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 6.04,
                'weight_unit': 'lb',
                'slug': 'ws-c2960l-24ts'
            },
            'WS-C2960L-24TS-LL': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '11.2',
                'weight_unit': 'lb'
            },
            'N2K-C2348TQ-10G-E': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '12.7',
                'weight_unit': 'lb',
                'slug': 'n2k-c2348tq-10g-e'
            },
        },
        'F5 NETWORKS': {
            'BIG-IP i4600': {
                'u_height': 1,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': 82,
                'weight_unit': 'lb',
                'slug': 'i4600'
            }
        },
        'PALO ALTO': {
            'PA-5250': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '28.6',
                'weight_unit': 'lb'
            },
            'PA-VM': {
                'u_height': 0,
                'is_full_depth': False,
                'airflow': 'front-to-rear',
                'weight': '0',
                'weight_unit': 'lb'
            },
            'PA-5220': {
                'u_height': 2,
                'is_full_depth': True,
                'airflow': 'front-to-rear',
                'weight': '28.6',
                'weight_unit': 'lb'
            },
        }
    }
