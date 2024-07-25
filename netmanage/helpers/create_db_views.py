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
    if view_name == "meraki_neighbors":
        cur.execute(
            """CREATE VIEW meraki_neighbors AS
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
            n.sourceMac = d.mac"""
        )
        con.commit()

    if view_name == "device_models":
        cur.execute(
            """CREATE VIEW device_models AS
        -- BIGIP_HARDWARE_INVENTORY segment
        SELECT
            'BIGIP_HARDWARE_INVENTORY' AS source,
            device,
            name AS model,
            appliance_serial AS serial
        FROM BIGIP_HARDWARE_INVENTORY

        UNION ALL

        -- NXOS_HARDWARE_INVENTORY segment with the "Chassis" condition
        SELECT
            'NXOS_HARDWARE_INVENTORY' AS source,
            device,
            productid AS model,
            serialnum AS serial
        FROM NXOS_HARDWARE_INVENTORY
        WHERE LOWER(name) LIKE '%chassis%'

        UNION ALL

        -- IOS_HARDWARE_INVENTORY segment with necessary conditions
        SELECT
            'IOS_HARDWARE_INVENTORY' AS source,
            device,
            pid AS model,
            serial
        FROM IOS_HARDWARE_INVENTORY
        WHERE
        (
            (LOWER(description) LIKE '%chassis%')
            OR (name = '1' AND pid = description)
        )
        AND
        (
            LOWER(name) NOT LIKE '%fan%'
        )

        UNION ALL

        -- ASA_HARDWARE_INVENTORY segment with the "Chassis" condition
        SELECT
            'ASA_HARDWARE_INVENTORY' AS source,
            device,
            pid AS model,
            serial
        FROM ASA_HARDWARE_INVENTORY
        WHERE LOWER(name) LIKE '%chassis%'

        UNION ALL

        -- PANOS_HARDWARE_INVENTORY segment
        SELECT
            'PANOS_HARDWARE_INVENTORY' AS source,
            device,
            model,
            serial
        FROM PANOS_HARDWARE_INVENTORY

         UNION ALL

        -- CISCO_ACI_GET_SITE_fabric_nodes segment
        SELECT
            'CISCO_ACI_GET_SITE_fabric_nodes' AS source,
            name as device,
            model,
            serial
        FROM CISCO_ACI_GET_SITE_fabric_nodes;
        """
        )
        con.commit()
    if view_name == "combined_bgp_neighbors":
        # Create required tables and views.
        cur.execute(
            """
            -- Table for IOS_BGP_NEIGHBORS
            CREATE TABLE IF NOT EXISTS IOS_BGP_NEIGHBORS (
                timestamp TEXT,
                device TEXT,
                local_host TEXT,
                bgp_neighbor TEXT,
                vrf TEXT,
                neighbor_id TEXT,
                remote_as TEXT,
                bgp_state TEXT,
                table_id INTEGER PRIMARY KEY AUTOINCREMENT
            );
            """
        )
        con.commit()
        con.close()
        con = hp.connect_to_db(db_path)
        cur = con.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS PANOS_BGP_NEIGHBORS (
                timestamp TEXT,
                device TEXT,
                "local-address" TEXT,
                "peer-address" TEXT,
                "@vr" TEXT,
                "peer-router-id" TEXT,
                "remote-as" TEXT,
                status TEXT,
                table_id INTEGER PRIMARY KEY AUTOINCREMENT
            );
            """
        )
        con.commit()
        con.close()
        con = hp.connect_to_db(db_path)
        cur = con.cursor()

        # Create view.
        cur.execute(
            """CREATE VIEW combined_bgp_neighbors AS
        -- Query for IOS_BGP_NEIGHBORS
        SELECT
            REPLACE(IOS.device, '.mmi.local', '') AS device,
            CASE
                WHEN (LENGTH(IOS.local_host) - LENGTH(REPLACE(
                        IOS.local_host, ':', ''))) > 1 THEN
                    IOS.local_host
                WHEN INSTR(IOS.local_host, ':') > 0 THEN
                    SUBSTR(IOS.local_host, 1, INSTR(IOS.local_host, ':') - 1)
                ELSE
                    IOS.local_host
            END AS local_host,
            REPLACE((SELECT DISTINCT device FROM interface_ips WHERE ip =
                  IOS.bgp_neighbor), '.mmi.local', '') AS bgp_neighbor,
            IOS.vrf,
            IOS.neighbor_id,
            IOS.remote_as,
            IOS.bgp_state,
            (SELECT DISTINCT interface_name FROM interface_ips WHERE device =
                  IOS.device AND ip = IOS.local_host) AS local_interface,
            (SELECT DISTINCT interface_name FROM interface_ips WHERE ip =
              IOS.bgp_neighbor) AS remote_interface,
            REPLACE((SELECT DISTINCT vrf FROM interface_ips WHERE ip =
              IOS.bgp_neighbor), 'vr:', '') AS remote_vrf
        FROM IOS_BGP_NEIGHBORS AS IOS

        UNION

        -- Query for PANOS_BGP_NEIGHBORS
        SELECT
            REPLACE(PANOS.device, '.mmi.local', '') AS device,
            CASE
                WHEN (LENGTH(PANOS."local-address") - LENGTH(
                        REPLACE(PANOS."local-address", ':', ''))) > 1 THEN
                    PANOS."local-address"
                WHEN INSTR(PANOS."local-address", ':') > 0 THEN
                    SUBSTR(PANOS."local-address", 1, INSTR(
                        PANOS."local-address", ':') - 1)
                ELSE
                    PANOS."local-address"
            END AS local_host,
            REPLACE((SELECT DISTINCT device FROM interface_ips WHERE ip =
              SUBSTR(PANOS."peer-address", 1, INSTR(PANOS."peer-address", ':')
                - 1)), '.mmi.local', '') AS bgp_neighbor,
            PANOS."@vr" AS vrf,
            PANOS."peer-router-id" AS neighbor_id,
            PANOS."remote-as" AS remote_as,
            PANOS.status AS bgp_state,
            (SELECT DISTINCT interface_name FROM interface_ips WHERE device =
              PANOS.device AND ip = PANOS."local-address") AS local_interface,
            (SELECT DISTINCT interface_name FROM interface_ips WHERE ip =
              SUBSTR(PANOS."peer-address", 1, INSTR(PANOS."peer-address", ':')
                - 1)) AS remote_interface,
            REPLACE((SELECT DISTINCT vrf FROM interface_ips WHERE ip =
              SUBSTR(PANOS."peer-address", 1, INSTR(PANOS."peer-address", ':')
                - 1)), 'vr:', '') AS remote_vrf
        FROM PANOS_BGP_NEIGHBORS AS PANOS;"""
        )
        con.commit()
    
    if view_name == "combined_arp_tables":
        # Create required tables and views.
        con = hp.connect_to_db(db_path)
        cur = con.cursor()
        cur.execute(
            """
            CREATE VIEW IF NOT EXISTS combined_arp_tables AS
            -- IOS_ARP_TABLE segment
            SELECT DISTINCT
            arp.device,
            arp.address,
            arp.mac,
            int.cidr,
            NULL AS description,
            vendor,
            'IOS_ARP_TABLE' AS source
            FROM IOS_ARP_TABLE arp
            LEFT JOIN IOS_INTERFACE_IP_ADDRESSES int ON arp.interface = int.interface
            UNION ALL
            -- NXOS_ARP_TABLE segment
            SELECT DISTINCT
            arp.device,
            arp.ip_address as address,
            arp.mac_address as mac,
            int.cidr,
            NULL AS description,
            vendor,
            'NXOS_ARP_TABLE' AS source
            FROM NXOS_ARP_TABLE arp
            LEFT JOIN NXOS_INTERFACE_IP_ADDRESSES int ON arp.interface = int.interface
            UNION ALL
            -- PANOS_ARP_TABLE segment
            SELECT DISTINCT
            arp.device,
            arp.ip as address,
            arp.mac,
            int.cidr,
            NULL AS description,
            vendor,
            'PANOS_ARP_TABLE' AS source
            FROM PANOS_ARP_TABLE arp
            LEFT JOIN PANOS_INTERFACE_IP_ADDRESSES int ON arp.interface = int.name
            UNION ALL
            -- MERAKI_NETWORK_CLIENTS segment
            SELECT DISTINCT 
            mnc.recentDeviceName,
            mnc.ip,
            mnc.mac,
            mnv.cidr,
            mnc.description,
            manufacturer AS vendor,
            'MERAKI_NETWORK_CLIENTS' AS source
            FROM MERAKI_NETWORK_CLIENTS mnc
            JOIN MERAKI_NETWORK_APPLIANCE_VLANS mnv ON mnc.vlan = mnv.id
            UNION ALL
            SELECT DISTINCT
            bat.device AS device,
            bat.Address AS address,
            bat.HWaddress AS mac,
            bsi.cidr AS cidr,
            NULL AS description,
            vendor,
            'BIGIP_ARP_TABLE' AS source
            FROM BIGIP_ARP_TABLE bat
            LEFT JOIN BIGIP_SELF_IPS bsi 
            ON REPLACE(bat.Vlan, '/Common/', '') = bsi.vlan;
            """)

    if view_name == "interface_ips":
        con = hp.connect_to_db(db_path)
        cur = con.cursor()

        cur.execute(
            """
            CREATE VIEW IF NOT EXISTS interface_ips AS
            SELECT 
                device, interface, ip, cidr,
                nameif AS description, NULL AS vrf, 
                subnet, network_ip, broadcast_ip
            FROM ASA_INTERFACE_IP_ADDRESSES
            UNION ALL
            SELECT 
                device, name AS interface, address AS ip,
                cidr, vlan AS description, NULL AS vrf,
                subnet, network_ip, broadcast_ip
            FROM BIGIP_SELF_IPS
            UNION ALL
            SELECT 
            device, interface, ip, cidr, description, vrf,
            subnet, network_ip, broadcast_ip
            FROM IOS_INTERFACE_IP_ADDRESSES
            UNION ALL
            SELECT device, interface, ip, cidr, NULL AS description,
            vrf, subnet, network_ip, broadcast_ip
            FROM NXOS_INTERFACE_IP_ADDRESSES
            /* interface_ips(device,interface,ip,cidr,description,vrf,
            subnet,network_ip,broadcast_ip) */;
            """
        )
        con.commit()
    con.close()
