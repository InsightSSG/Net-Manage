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
                          group_name: str) -> list:
    """
    Retrieves the names of all the devices within an Orion NPM group.

    Args:
    server (str): The hostname or IP address of the Orion database server.
    username (str): The username used to authenticate with the Orion API.
    password (str): The password used to authenticate with the Orion API.
    group_name (str): The name of the group whose devices should be retrieved.

    Returns:
    list: A list of device names.

    Raises:
    IndexError: If the specified group name is not found in the Orion NPM
    database.
    Exception: If there is an issue connecting to the Orion NPM API.

    Example usage:
    >>> server = 'myserver.mycompany.com'
    >>> username = 'myusername'
    >>> password = 'mypassword'
    >>> group_name = 'Switches'
    >>> members = get_npm_group_members(server, username, password, group_name)
    >>> print(members)
    ['Switch1', 'Switch2', 'Switch3']
    """
    swis = SwisClient(server, username, password)

    # Get the group ID for the specified group name
    g_id = get_npm_group_id(server, username, password, group_name)

    # Retrieve the devices inside the group
    results = swis.query(
        f"SELECT Name FROM Orion.ContainerMembers WHERE ContainerID='{g_id}'"
    )
    return [result["Name"] for result in results["results"]]


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
