#!/usr/bin/env python3


def map_machine_type_to_ansible_os(machine_type: str) -> str:
    """
    Maps a machine type to its corresponding Ansible OS.

    Parameters
    ----------
    machine_type : str
        The machine type as collected from Solarwinds.

    Returns
    -------
    ansible_os : str
        The Ansible OS.
    """
    m_types = {'Cisco Catalyst 38xx stack': 'cisco.ios.ios',
               'Cisco 1921/K9': 'cisco.ios.ios',
               'BIG-IP i4600': 'bigip',
               'Cisco Nexus N77c7706': 'cisco.nxos.nxos',
               'Cisco Catalyst 94010R Switch': 'cisco.ios.ios',
               'Cisco Catalyst 2960X-24TS-LL Switch': 'cisco.ios.ios',
               'Catalyst 2960': 'cisco.ios.ios',
               'net-snmp - Linux': '',
               'Cisco ASR1002-X': 'cisco.ios.ios',
               'Cisco Catalyst 2960L-48TS-LL Switch': 'cisco.ios.ios',
               'Cisco Catalyst 295024': 'cisco.ios.ios',
               'Cisco 2901K9': 'cisco.ios.ios',
               'Cisco ASR 1001-X Router': 'cisco.ios.ios',
               'Nexus 5696Q': 'cisco.nxos.nxos',
               'Cisco Nexus 5596 UP': 'cisco.nxos.nxos',
               'Cisco 3925K9': 'cisco.ios.ios',
               'PA-VM': 'paloaltonetworks.panos',
               'Unknown': '',
               'Cisco ASA 5555-X': 'cisco.asa.asa',
               'OpenGear': '',
               'Cisco C9200L': 'cisco.ios.ios',
               'ASR1002-HX': 'cisco.ios.ios',
               'Cisco FirePower 1120': '',
               'Palo Alto PA-5200': 'paloaltonetworks.panos',
               'PA-5050': 'paloaltonetworks.panos',
               'Panorama Server': 'paloaltonetworks.panos',
               '9800 Wireless Controller': 'cisco.ios.ios',
               'Cisco Catalyst 9300 Series Switch': 'cisco.ios.ios',
               'netUX2000': '',
               'Cisco Catalyst 2960L-24TS-LL Switch': 'cisco.ios.ios',
               'Catalyst 2960L-24PS-LL': 'cisco.ios.ios',
               'PA-5200': 'paloaltonetworks.panos',
               'Secure Network Server 3615': '',
               'Red Hat': '',
               'BIG-IP 4200': 'bigip',
               'F5 Networks BIG-IP i4600': 'bigip',
               'Cisco Catalyst C8500-12X': 'cisco.ios.ios',
               'Cisco Nexus 93180YC-FX': 'cisco.nxos.nxos',
               'Meraki MX64': 'meraki',
               'Meraki MX84': 'meraki',
               'Meraki MX65': 'meraki',
               'Catalyst 9500-48Y4C': 'cisco.ios.ios',
               'C9300L': 'cisco.ios.ios',
               'Meraki Networks Cloud Orchestrator': 'meraki'}
    return m_types.get(machine_type)
