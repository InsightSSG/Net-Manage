#!/usr/bin/env python3

"""A collection of collectors to gather data from Netbox, using pynetbox.

"""

import pandas as pd
import pynetbox


def create_netbox_handler(nb_path, token):
    """Creates the handler for connecting to Netbox using pynetbox.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL. Must be
        preceded by 'http://' or 'https://'
    token : str
        The API token to use for authentication.

    Returns
    ----------
    nb : pynetbox.core.api.Api
        An object used to connect to the Netbox API.

    Examples
    ----------
    >>> nb = create_netbox_handler(nb_path, token)
    >>> print(nb)
    <pynetbox.core.api.Api object at 0x7fb3576a4c1990>
    """
    nb = pynetbox.api(nb_path, token)
    return nb


def netbox_get_ipam_prefixes(nb):
    '''Gets all prefixes from a Netbox instance.

    Parameters
    ----------
    nb : pynetbox.core.api.Api
        An object used to connect to the Netbox API.

    Returns
    ----------
    df : pandas.core.frame.DataFrame
        A Pandas dataframe containing the IPAM prefixes.

    See Also
    ----------
    create_netbox_handler : A function to create 'nb'

    Notes
    ----------
    The Netbox API returns the prefixes in the form of a nested dictionary.
    Some items in the nested dictionaries have keys that overlap with the
    top-level dictionary. Because of that, the keys in the nested dictionaries
    are prefixed with the key(s) in the level(s) above it, followed by an
    underscore.

    For example, a key named 'id' that is nested under 'tenant' would be added
    as a column named 'tenant_id'.

    Examples
    ----------
    >>> df = netbox_get_ipam_prefixes(nb)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    '''
    result = nb.ipam.prefixes.all()

    # A dictionary to store each prefix.
    data = dict()

    # Iterate over 'result'. Convert the dictionary for each prefix into a
    # flattened dictionary, then add it to 'data'. The key for each flattened
    # dictionary will be its prefix id, prefixed by '_'.
    for _ in result:
        _ = dict(_)
        flat_dict = dict()
        for key, value in _.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    new_key = f'{key}_{k}'
                    flat_dict[new_key] = v
            else:
                flat_dict[key] = value
        # Rename 'id' to '_id', so it will not conflict with Python and
        # database reserved words.
        data[_['id']] = flat_dict

    # Iterate over the prefixes in 'data', to collect all of the possible
    # dictionary keys. These will be used to create the dataframe columns.
    columns = list()
    for prefix in data:
        for key in data[prefix]:
            if key not in columns:
                columns.append(key)

    # Create the DataFrame
    df = pd.DataFrame(data=list(), columns=columns)
    for prefix in data:
        row = list()
        for col in columns:
            row.append(data[prefix].get(col))
        df.loc[len(df.index)] = row

    return df
