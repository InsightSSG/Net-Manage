#!/usr/bin/env python3

# flake8: noqa

import ansible_runner
import datetime as dt
import importlib
import ipywidgets as widgets
import jupyterlab_widgets
import nest_asyncio
import os
import pandas as pd
import readline
from netmanage import run_collectors as rc
from netmanage import validators as vl

from netmanage.helpers import helpers as hp
from IPython.display import clear_output
from IPython.display import display

# Reload helper modules after changes. Mostly used for development.
importlib.reload(hp)
importlib.reload(rc)
importlib.reload(vl)

# Do not write history to .python_history to protect credentials
readline.write_history_file = lambda *args: None

# Defining these variables now allows the user to update selections later
collector_select = dict()
hostgroup_select = dict()

# Set Pandas display settings
pd.set_option('display.max_rows', 50)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.colheader_justify', 'center')
pd.set_option('display.precision', 3)

# Pre-define some global variables
macs = list()
orgs = list()
networks = list()
per_page = 10
timespan = '86400'
total_pages = 'all'
validate_certs = True

# Define several functions that need to be run within Jupyter
def create_collectors_df(collector_select: dict,
                         hostgroup_select: dict) -> pd.DataFrame:
    '''
    Creates a dataframe of collectors to execute. Each row contains the
    ansible_os, hostgroup, and collector.

    Parameters
    ----------
    collector_select : dict
        A dictionary of selected collectors.
    hostgroup_select : dict
        A dictionary of selected hostgroups.

    Returns
    -------
    df_collectors : pd.DataFrame
        A dataframe of collectors to run.
    '''
    df_data = dict()
    df_data['ansible_os'] = list()
    df_data['hostgroup'] = list()
    df_data['collector'] = list()

    # Iterate through the hostgroups the user selected. Each key will be an
    # ansible_os. Its value will be the parameters for a checkbox
    for key, value in hostgroup_select.items():
        # Create an empty list to store hostgroups the user selected
        to_run = list()
        # Iterate over the parameters for each checkbox
        for _ in value:
            # If the user selected the checkbox, define the ansible_os and
            # hostgroup variables
            if _.value == True:
                ansible_os = key
                hostgroup = _.description
                # Get the checkboxes for the ansible_os from 'collector_select'
                for collector in collector_select.get(key):
                    # If the user selected the collector, append it to
                    # 'to_run'
                    description = collector.description
                    if collector.value == True and description not in to_run:
                        to_run.append(collector.description)
                # Pass the list of selected collectors to hp.set_dependencies.
                # It will add any missing dependencies and return the list.
                to_run = hp.set_dependencies(to_run)
                
                # Add the complete list of collectors that the user selected
                # for this ansible_os and hostgroup to 'df_data'
                for item in to_run:
                    for collector in collector_select.get(key):
                        if collector.description == item:
                            df_data['ansible_os'].append(ansible_os)
                            df_data['hostgroup'].append(hostgroup)
                            df_data['collector'].append(collector.description)

    df_collectors = pd.DataFrame.from_dict(df_data)
    return df_collectors


def select_collectors(collector_select, hostgroup_select):
    '''
    Selects the collectors for the selected hostgroups.

    Args:
        collector_select (dict): The collectors the user selected. The first
                                 time this is run, it will be an empty
                                 dictionary. Passing it to the function
                                 allows the user to select additional
                                 hostgroups later without losing their
                                 selected collectors.
        hostgroup_select (dict): The hostgroups the user selected

    Returns:
        collector_select (dict): A dictionary of collectors to select
    '''
    for key, value in hostgroup_select.items():
        for item in value:
            if item.value == True:
                if not collector_select.get(key):
                    available = hp.define_collectors(key)
                    collector_select[key] = [widgets.Checkbox(value=False,
                                                              description=c,
                                                              disabled=False,
                                                              indent=False) for c in available]
    # Delete any hostgroups that do not have available selectors
    to_delete = list()
    for key, value in collector_select.items():
        if not value:
            to_delete.append(key)
    for item in to_delete:
        del collector_select[item]
                    
    # Delete any hostgroups that the user has de-selected
    for key, value in hostgroup_select.items():
        if collector_select.get(key):
            to_delete = True
            for item in hostgroup_select[key]:
                if item.value == True:
                    to_delete = False
            if to_delete:
                del collector_select[key]
    return collector_select

def select_hostgroups(collector_select: dict,
                      hostgroup_select: dict,
                      private_data_dir: str) -> dict:
    '''
    Selects the collectors for the selected hostgroups.

    Parameters
    ----------
    collector_select : dict
        The collectors the user selected. The first time this is run, it will
        be an empty dictionary. Passing it to the function allows the user to
        select additional hostgroups later without losing their selected
        collectors.
    hostgroup_select : dict
        The hostgroups the user selected.
    private_data_dir : str
        The path to the Ansible private data directory.

    Returns
    -------
    collector_select : dict
        A dictionary of collectors to select.
    '''
    # Define and select hostgroups
    groups = hp.ansible_group_hostgroups_by_os(private_data_dir)    
    for key, value in groups.items():
        if not hostgroup_select.get(key):
            hostgroup_select[key] = [widgets.Checkbox(value=False,
                                                      description=h,
                                                      disabled=False,
                                                      indent=False) for h in value]
    return hostgroup_select