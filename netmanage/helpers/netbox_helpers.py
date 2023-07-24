#!/usr/bin/env python3

"""A collection of helper functions for Netbox operations.

"""

import pandas as pd
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
