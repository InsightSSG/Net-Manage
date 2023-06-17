#!/usr/bin/env python3

"""A collection of collectors to gather data from Netbox, using pynetbox.

"""

import pandas as pd
import pynetbox


def create_netbox_handler(nb_path: str,
                          token: str) -> pynetbox.core.api.Api:
    """Creates the handler for connecting to Netbox using pynetbox.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
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


def netbox_get_ipam_prefixes(nb_path: str,
                             token: str) -> pd.DataFrame:
    """Gets all prefixes from a Netbox instance.

    Parameters
    ----------
    nb_path : str
        The path to the Netbox instance. Can be either an IP or a URL.
        Must be preceded by 'http://' or 'https://'.
    token : str
        The API token to use for authentication.

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
    top-level dictionary. Because of that, the keys in the nested
    dictionaries are prefixed with the key(s) in the level(s) above it,
    followed by an underscore.

    For example, a key named 'id' that is nested under 'tenant' would be
    added as a column named 'tenant_id'.

    Examples
    ----------
    >>> df = netbox_get_ipam_prefixes(nb_path, token)
    print(type(df))
    >>> <class 'pandas.core.frame.DataFrame'>
    """
    # Create the netbox handler
    nb = create_netbox_handler(nb_path, token)

    # Query the Netbox API for all IPAM prefixes
    result = nb.ipam.prefixes.all()

    # Iterate over the prefixes, adding each one as a row for 'df'.
    df = pd.DataFrame()
    for _ in result:
        _ = dict(_)
        df = pd.concat([df, pd.DataFrame.from_dict(_, orient='index').T]).\
            reset_index(drop=True)
    return df
