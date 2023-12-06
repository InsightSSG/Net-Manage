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
