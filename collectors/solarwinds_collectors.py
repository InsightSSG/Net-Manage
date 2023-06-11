#!/usr/bin/env python3

import pandas as pd
from orionsdk import SwisClient


def get_npm_group_id(server: str,
                     username: str,
                     password: str,
                     group_name: str) -> str:
    """
    Retrieves the Orion NPM group ID for a given group name.

    Args:
    server (str):
        The hostname or IP address of the Orion database server.
    username (str):
        The username used to authenticate with the Orion API.
    password (str):
        The password used to authenticate with the Orion API.
    group_name (str):
        The name of the group to retrieve the ID for.

    Returns:
    str:
        The group ID of the specified group name.

    Raises:
    IndexError:
        If the group name is not found in the Orion NPM database.

    Example usage:
    >>> server = "your.server.com"
    >>> username = "your_username"
    >>> password = "your_password"
    >>> group_name = "your_group_name"
    >>> group_id = get_npm_group_id(server, username, password, group_name)
    >>> print(group_id)
    """
    swis = SwisClient(server, username, password)

    # Get the group ID for the specified group name
    results = swis.query(
        f"SELECT ContainerID FROM Orion.Container WHERE Name='{group_name}'"
    )
    g_id = results["results"][0]["ContainerID"]

    return g_id


def get_npm_group_members(server: str,
                          username: str,
                          password: str,
                          group_name: str = 'all') -> pd.DataFrame:
    """
    Retrieves the names of all the devices within an Orion NPM group.

    Args:
    server (str):
        The hostname or IP address of the Orion database server.
    username (str):
        The username used to authenticate with the Orion API.
    password (str):
        The password used to authenticate with the Orion API.
    group_name (str, optional):
        The name of the group whose devices should be retrieved.

    Returns:
    list:
        A list of device names.

    Raises:
    IndexError:
        If the specified group name is not found in the Orion NPM database.
    Exception:
        If there is an issue connecting to the Orion NPM API.

    Example usage:
    >>> server = 'myserver.mycompany.com'
    >>> username = 'myusername'
    >>> password = 'mypassword'
    >>> group_name = 'Switches'
    >>> members = get_npm_group_members(server, username, password, group_name)
    >>> print(members)
    <class 'pandas.core.frame.DataFrame'>
    RangeIndex: 23 entries, 0 to 22
    Data columns (total 1 columns):
    #   Column   Non-Null Count  Dtype
    ---  ------   --------------  -----
    0   devices  23 non-null     object
    dtypes: object(1)
    memory usage: 312.0+ bytes
    None
    """
    swis = SwisClient(server, username, password)

    results = list()

    # Retrieve the devices inside the group(s)
    if group_name != 'all':
        # Get the group ID for the specified group name
        g_id = get_npm_group_id(server, username, password, group_name)
        # Get the group members
        members = swis.query(
            f"""SELECT Name FROM Orion.ContainerMembers
                WHERE ContainerID='{g_id}'"""
        )
        members = [result["Name"] for result in members["results"]]
        for member in members:
            row = [group_name, g_id, member]
            results.append(row)
    else:
        # Get all of the group names.
        group_names = get_npm_group_names(server, username, password)
        group_names = group_names['group_name'].to_list()
        # Iterate through the groups, adding the members to 'results'.
        for group in group_names:
            # Get the group ID for the specified group name
            g_id = get_npm_group_id(server, username, password, group)
            members = swis.query(
                f"""SELECT Name FROM Orion.ContainerMembers
                    WHERE ContainerID='{g_id}'"""
            )
            members = [result["Name"] for result in members["results"]]
            for member in members:
                row = [group, g_id, member]
                results.append(row)

    # Convert to a DataFrame and return the results
    columns = ['group_name', 'group_id', 'member']
    df = pd.DataFrame(data=results, columns=columns)

    return df


def get_npm_group_names(server: str,
                        username: str,
                        password: str) -> pd.DataFrame:
    """
    Retrieves a list of the names of all the Orion NPM groups.

    Args:
    server (str): The hostname or IP address of the Orion database server.
    username (str): The username used to authenticate with the Orion API.
    password (str): The password used to authenticate with the Orion API.

    Returns:
    pd.DataFrame:
        A DataFrame of all the group names available in the Orion NPM database.

    Raises:
    Exception: If there is an issue connecting to the Orion NPM API.

    Example usage:
    >>> server = 'your.server.com'
    >>> username = 'your_username'
    >>> password = 'your_password'
    >>> group_names = get_npm_group_names(server, username, password)
    >>> print(group_names)
    ['Switches', 'Routers', 'Servers', ...]
    """
    swis = SwisClient(server, username, password)

    results = swis.query("SELECT Name FROM Orion.Container")

    group_names = [result["Name"] for result in results["results"]]

    df = pd.DataFrame(data=group_names, columns=['group_name'])

    return df
