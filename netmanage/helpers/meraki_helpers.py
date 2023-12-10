import ast
import pandas as pd
import sqlite3 as sl


def meraki_check_api_enablement(db_path: str, org: str) -> bool:
    """
    Queries the database to find if API access is enabled.

    Parameters
    ----------
    db_path : str
        The path to the database to store results.
    org : str
        The organization to check API access for.

    Returns
    -------
    enabled : bool
        A boolean indicating whether API access is enabled for the user's API
        key.
    """
    # enabled = False

    query = [
        "SELECT timestamp, api from MERAKI_ORGANIZATIONS",
        f'WHERE id = "{org}"',
        "ORDER BY timestamp DESC",
        "limit 1",
    ]
    query = " ".join(query)

    con = sl.connect(db_path)
    result = pd.read_sql(query, con)
    con.close()
    return ast.literal_eval(result.iloc[0]["api"])["enabled"]
