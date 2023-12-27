import pandas as pd
from netmanage.helpers import helpers as hp


def get_device_name_from_serial(df: pd.DataFrame, db_path: str) -> pd.DataFrame:
    """
    Queries the PANOS_PANORAMA_MANAGED_DEVICES table to get the device names for
    the serial numbers in 'df', then adds them to 'df'. It also renames the 'device'
    column to 'panorama_device'.

    Parameters
    ----------
    df : pd.DataFrame
        A Pandas dataframe containing the serial numbers in a column named 'serial'.
    db_path : str
        The full path to the database containing PANOS_PANORAMA_MANAGED_DEVICES.

    Returns
    -------
    df : pd.DataFrame
        An updated DataFrame with the 'device' column populated with the managed
        device names (the original device column is renamed to 'panorama_device').
    """
    conn = hp.connect_to_db(db_path)
    query = "select distinct hostname, serial from PANOS_PANORAMA_MANAGED_DEVICES"
    df_managed = pd.read_sql(query, conn)

    # Rename 'device' to 'panorama_device', then add the device names to the 'device'
    # column.
    df.rename(columns={"device": "panorama_device"}, inplace=True)
    df = pd.merge(df, df_managed[["serial", "hostname"]], on="serial", how="left")
    df = df[["hostname"] + [col for col in df.columns if col != "hostname"]]
    df.rename(columns={"hostname": "device"}, inplace=True)

    return df


def get_serial_from_device_name(
    df: pd.DataFrame,
    db_path: str,
    device_col: str = "device",
    serial_col: str = "serial",
) -> pd.DataFrame:
    """
    Queries the PANOS_PANORAMA_MANAGED_DEVICES table to get the serial numbers for
    the device names in 'df', then adds them to 'df'. This function is necessary because
    some Ansible modules return the serial number as
    VALUE_SPECIFIED_IN_NO_LOG_PARAMETER.

    Parameters
    ----------
    df : pd.DataFrame
        A Pandas dataframe containing the device names and serial numbers in two
        columns.
    db_path : str
        The full path to the database containing PANOS_PANORAMA_MANAGED_DEVICES.
    device_col : str, optional
        The name of the column that contains the devices (defaults to 'device').
    serial_col : str, optional;
        The name of the column that contains the serial numbers (defaults to 'serial').

    Returns
    -------
    df : pd.DataFrame
        An updated DataFrame with the serial_col updated with the serial numbers,
        assuming they are in the PANOS_PANORAMA_MANAGED_DEVICES table. If they are not
        in that table then they will be set to "Unknown". (Serial numbers that are
        already in 'df' will not be changed, even if they are not in the
        PANOS_PANORAMA_MANAGED_DEVICES table.)
    """
    conn = hp.connect_to_db(db_path)
    query = (
        "SELECT DISTINCT hostname AS device, serial FROM PANOS_PANORAMA_MANAGED_DEVICES"
    )
    try:
        df_managed = pd.read_sql(query, conn)
        # Convert to string for consistency
        df[serial_col] = df[serial_col].astype(str)
        df_managed["serial"] = df_managed["serial"].astype(str)

        # Create a dictionary for lookup
        serial_dict = pd.Series(df_managed.serial.values,
                                index=df_managed.device).to_dict()

        # Update df using apply
        def update_serial(row):
            if row[serial_col] == "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER":
                return serial_dict.get(row[device_col], "Unknown")
            else:
                return row[serial_col]

        df[serial_col] = df.apply(update_serial, axis=1)
    except Exception as e:
        if 'DatabaseError' in str(e) and 'PANOS_PANORAMA_MANAGED_DEVICES' in str(e):
            pass

    return df
