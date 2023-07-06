#!/usr/bin/env python3

'''
Helpers specifically for running reports scripts.
'''

import datetime
import pandas as pd


def export_dataframe_to_csv(dataframe: pd.DataFrame,
                            file_path: str,
                            report_name: str) -> None:
    """
    Export a Pandas DataFrame to a CSV file.

    Args:
    ----
    dataframe (pd.DataFrame):
        The DataFrame to be exported.
    file_path (str):
        The path to the CSV file where the DataFrame will be saved.
    report_name (str):
        The name of the report--I.e., 'dnac_device_modules'.

    Returns:
    ----
    full_path (str):
        The full path to the file (including the file name).

    Raises:
    ----
        OSError:
            If the specified file path's directory does not exist.
        Exception:
            If there is any other error.
    """
    try:
        # Set the file name
        ts = datetime.datetime.now().strftime('%Y-%m-%d_%H%M')
        fname = f'{ts}_{report_name}.csv'
        full_path = f'{file_path}/{fname}'

        try:
            # Export the DataFrame to a CSV file
            dataframe.to_csv(full_path, index=False)
        except OSError as e:
            _ = file_path
            if str(e) == \
                    f"Cannot save file into a non-existent directory: '{_}'":
                print(e)
        except Exception as e:
            print(type(e), str(e))

    except FileNotFoundError as e:
        raise e

    except Exception as e:
        raise Exception(f"Error exporting DataFrame to CSV: {str(e)}")

    return full_path
