import streamlit as st
import datetime as dt
import os
from netmanage.run_collectors import collect
from netmanage.setup import create_collectors_df
from netmanage.setup import select_collectors
from netmanage.setup import select_hostgroups

if st.session_state.get("collector_select") is None:
    st.session_state["collector_select"] = None

collector_select = st.session_state.get("collector_select")

col_checkboxes, hg_checkboxes = {}, {}

st.set_page_config(layout="wide")

st.title("Net-Manage Run Collectors")
st.header("Select Host Groups")
with st.spinner("Retrieving select_hostgroups data..."):
    hostgroup_select = select_hostgroups(
        {}, {}, os.path.expanduser(st.secrets.get("private_data_directory"))
    )

for key in sorted(hostgroup_select.keys()):
    hg_checkboxes[key] = st.checkbox(key, True, key=f"hg_{key}")

selected_hg = bool(any(hg_checkboxes.values()))

if selected_hg:
    for key in list(hostgroup_select):
        hostgroup_select[key][0].value = hg_checkboxes[key]
    with st.spinner("Retrieving collector_select data..."):
        collector_select = select_collectors({}, hostgroup_select)

if collector_select:
    st.subheader("Select Collectors to run")
    for dev in list(collector_select):
        st.subheader(dev)

        current_col = 0
        cols = st.columns(3)  # Create the first 3 columns

        for idx, key in enumerate(collector_select[dev]):
            if (
                idx % 3 == 0 and idx != 0
            ):  # If we've filled 3 columns, create a new row
                cols = st.columns(3)
                current_col = 0

            col_checkboxes[f"{dev}_{key.description}"] = cols[
                current_col
            ].checkbox(
                f"{key.description}", True, key=f"{dev}_{key.description}"
            )
            collector_select[dev][idx].value = col_checkboxes[
                f"{dev}_{key.description}"
            ]

            current_col += 1

if True in col_checkboxes.values():
    selected_cols = st.button("Run Selected Collectors", key="col_checkboxes")
else:
    selected_cols = False

if selected_cols:
    df_collectors = create_collectors_df(collector_select, hostgroup_select)

    for idx, row in df_collectors.iterrows():
        with st.spinner(f'Running Collector {row["collector"].upper()}...'):
            ansible_os = row["ansible_os"]
            hostgroup = row["hostgroup"]
            collector = row["collector"]
            ts = dt.datetime.now()
            ts = ts.strftime("%Y-%m-%d_%H%M")
            result = collect(ansible_os, collector, hostgroup, ts)

            st.write(
                f"\nRESULT: {ansible_os.upper()} "
                f"{collector.upper()} COLLECTOR\n"
            )
            st.write(result)
