#!/usr/bin/env python3

"""
Contains the schema and creates the views for sqlite3 databases.
"""

from netmanage.helpers import helpers as hp


def create_db_view(db_path: str, view_name: str):
    """
    Creates the view for the specified name.

    Parameters
    ----------
    view_name : str
        The name of the view to create (case-sensitive).
    db_path : str
        The full path to the database.

    Returns
    -------
    None
    """
    con = hp.connect_to_db(db_path)
    cur = con.cursor()
    if view_name == 'meraki_neighbors':
        cur.execute('''CREATE VIEW meraki_neighbors AS
        SELECT
            d.orgId,
            d.networkId,
            d.name,
            d.serial,
            d.model,
            n.sourceMac AS mac,
            COALESCE(n.lldp_sourcePort, n.cdp_sourcePort) AS sourcePort,
            COALESCE(n.lldpSystemName, n.cdpDeviceId) AS neighborName,
            COALESCE(n.lldpManagementAddress, n.cdpAddress) AS neighborIp,
            COALESCE(n.lldpPortId, n.cdpPortId) AS remotePort
        FROM
            MERAKI_CDP_LLDP_NEIGHBORS n
        JOIN
            MERAKI_ORG_DEVICES d
        ON
            n.sourceMac = d.mac''')
    con.commit()
    con.close()
