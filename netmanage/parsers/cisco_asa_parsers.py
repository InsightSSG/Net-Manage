#!/usr/bin/env python3

import pandas as pd


def asa_parse_inventory(runner: dict) -> pd.DataFrame:
    """
    Parses the inventory for Cisco ASA devices.

    Parameters
    ----------
    runner : dict
        An Ansible runner generator.

    Returns
    -------
    df : pd.DataFrame
        A DataFrame containing the inventory data.
    """
    if runner is None or runner.events is None:
        raise ValueError("The input is None or empty")

    # Create a dictionary to store the inventory data.
    columns = ['device',
               'name',
               'description',
               'pid',
               'vid',
               'serial']
    df_data = dict()
    for col in columns:
        df_data[col] = list()

    # Parse the output and add it to 'df_data'
    for event in runner.events:
        if event["event"] == "runner_on_ok":
            event_data = event["event_data"]

            device = event_data["remote_addr"]

            data = event_data["res"]["stdout"][0].split("\n")

            # Iterate through data (each hardware entry has 3 lines).
            for i in range(0, len(data), 3):
                df_data['device'].append(device)
                # Split the first line to extract name and description
                name_desc = data[i].split(", DESCR: ")
                df_data['name'].append(
                    name_desc[0].replace('NAME: "', '').
                    replace('"', '').strip())
                df_data['description'].append(
                    name_desc[1].replace('"', '').strip())

                # Split the second line to extract PID, VID and SN
                pid_vid_sn = data[i+1].split(", ")
                df_data['pid'].append(
                    pid_vid_sn[0].replace('PID: ', '').strip())
                df_data['vid'].append(
                    pid_vid_sn[1].replace('VID: ', '').strip())

                # If SN value is "SN:", replace with an empty string.
                sn_value = pid_vid_sn[2].replace('SN: ', '').strip()
                if sn_value == "SN:":
                    sn_value = ""
                df_data['serial'].append(sn_value)

    # Create the DataFrame and return it.
    df = pd.DataFrame(df_data)

    return df
