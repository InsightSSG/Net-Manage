#!/usr/bin/env python3

'''
This report gets the modules for device in a Cisco DNAC inventory. It gets all
modules by default, but it can be filtered by a list of platform_ids--e.g.,
['C9407R', 'N9K-C93180YC-FX'].
'''

import datetime as dt
import os
import sys
import streamlit as st


def get_search_params() -> list:
    '''
    Allows the user to provide a list of platform IDs to filter by.

    Parameters
    ----------
    None

    Returns
    -------
    allow_partial_match : bool
        Whether to allow partial matches within the list of platform IDs.
    dnac_platform_ids : list
        A list of platform IDs to filter by.
    '''
    with st.form(key='my_form'):
        # Get the list of platform IDs.
        msg = 'Comma-delimited list of platform ID to filter by (optional): '
        dnac_platform_ids = st.text_input(msg)
        dnac_platform_ids = dnac_platform_ids.split(',')
        dnac_platform_ids = list(filter(None, dnac_platform_ids))
        dnac_platform_ids = [_.strip() for _ in dnac_platform_ids]

        # Determine whether to allow partial matches.
        allow_partial_match = st.checkbox('Allow partial matches?')

        st.form_submit_button('Apply')

    return allow_partial_match, dnac_platform_ids


def main():
    st.write('# Cisco DNAC Device Module Report')

    # Change to the Net-Manage path and import DNAC collectors.
    nm_path = os.path.expanduser(st.secrets['netmanage_path'])
    os.chdir(nm_path)
    sys.path.append('.')
    from collectors import dnac_collectors as dnc

    # Set the variables for connecting to DNAC.
    dnac_url = st.secrets['dnac_url']
    dnac_username = st.secrets['dnac_username']
    dnac_password = st.secrets['dnac_password']
    dnac_platform_ids = st.secrets['dnac_platform_ids']
    validate_certs = st.secrets['validate_certs']

    # Allow the user to search by platform IDs
    allow_partial_match, dnac_platform_ids = get_search_params()

    # Get the list of device modules and add them to a DataFrame.
    with st.spinner('Retrieving data...'):
        df = dnc.devices_modules(dnac_url,
                                 dnac_username,
                                 dnac_password,
                                 dnac_platform_ids,
                                 allow_partial_match=allow_partial_match,
                                 verify=validate_certs)

    # Filter the DataFrame by the requested columns then display it.
    columns = ['platformId',
               'hostname',
               'name',
               'description',
               'partNumber',
               'serialNumber',
               'vendorEquipmentType']
    df = df[columns]

    # Export the report to a CSV file.
    now = dt.datetime.now()
    out_file = f"dnac_device_module_report_{now.strftime('%Y-%m-%d_%H%M')}"

    # Provide an option for the user to download the DataFrame to a CSV file.
    # The filename is 'dnac_device_module_report_YYYY-MM-DD_hhmm', where 'YYYY'
    # is the 4-digit year, 'MM' is the 2-digit month, 'DD' is the 2-digit day,
    # 'hh' is the 2-digit hour in 24-hour format, and 'mm' is the 2-digit
    # minute.
    st.download_button('save to file',
                       df.to_csv(index=False).encode('utf-8'),
                       out_file,
                       'text.csv',
                       key='download-csv')

    st.dataframe(df)


if __name__ == '__main__':
    main()
