import streamlit as st
import datetime as dt
import os
from netmanage.run_collectors import collect
from netmanage.setup import select_hostgroups, select_collectors
from netmanage.setup import create_collectors_df

if st.session_state.get('collector_select') is None:
    st.session_state['collector_select'] = None

collector_select = st.session_state.get('collector_select')

col_checkboxes, hg_checkboxes = {}, {}

st.set_page_config(layout="wide")

st.title("Welcome to MN test")
st.header('Select Host Groups')
with st.spinner('Retrieving select_hostgroups data...'):
    hostgroup_select = select_hostgroups(
        os.path.expanduser(st.secrets.get('private_data_directory')))

for key in sorted(hostgroup_select.keys()):
    hg_checkboxes[key] = st.checkbox(key, True, key=f'hg_{key}')

selected_hg = bool(any(hg_checkboxes.values()))

if selected_hg:
    for key in list(hostgroup_select):
        hostgroup_select[key][0].value = hg_checkboxes[key]
    with st.spinner('Retrieving collector_select data...'):
        collector_select = select_collectors({}, hostgroup_select)

if collector_select:
    st.subheader('Select Collectors to run')
    for dev in list(collector_select):
        st.subheader(dev)
        cols = st.columns(len(collector_select[dev]))
        for idx, key in enumerate(collector_select[dev]):
            _index = f'{dev}_{key.description}'
            col_checkboxes[_index] = cols[idx].checkbox(_index, 1, key=_index)
            collector_select[dev][idx].value = col_checkboxes[_index]

if True in col_checkboxes.values():
    selected_cols = st.button('Run Selected Collectors', key='col_checkboxes')
else:
    selected_cols = False

if selected_cols:
    df_collectors = create_collectors_df(collector_select, hostgroup_select)

    # st.dataframe(df_collectors)

    for idx, row in df_collectors.iterrows():
        with st.spinner(f'Running Collector {row["collector"].upper()}...'):
            ansible_os = row['ansible_os']
            hostgroup = row['hostgroup']
            collector = row['collector']
            ts = dt.datetime.now()
            ts = ts.strftime('%Y-%m-%d_%H%M')
            result = collect(ansible_os,
                             collector,
                             hostgroup,
                             ts)

            st.write(
                f'\nRESULT: {ansible_os.upper()}'
                f' {collector.upper()} COLLECTOR\n'
            )
            st.write(result)
