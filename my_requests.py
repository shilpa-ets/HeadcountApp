import streamlit as st
import pandas as pd


def show():
    st.title("My Requests")

    # Read request data from Excel
    df = pd.read_excel("Data.xlsx", sheet_name="Request")
    wf_df = pd.read_excel("Data.xlsx", sheet_name="Workflow")

    
    df = df.merge(
    wf_df,
    left_on="WorkFlowLevel",
    right_on="WorkFlowLevel",
    how="left"
)

    # Filter for Shilpa's requests
    shilpa_df = df[df["RequesterName"] == "Shilpa"].copy()
    display_cols = [
    "Request ID",
    "Department",
    "Req_JobTitle",
    "Business Unit",
    "WorkFlowLevel_Description",
    ]
    st.dataframe(shilpa_df[display_cols], use_container_width=True)


    st.subheader("Actions")
    
    shilpa_df_edit = shilpa_df[shilpa_df["WorkFlowLevel"] == 2].copy()

    for _, row in shilpa_df_edit.iterrows():
        c1, c2 = st.columns([5, 1])

        with c1:
            st.write(
                f"{row['Request ID']} | {row['Req_JobTitle']} | WF Level {row['WorkFlowLevel']}"
            )

        with c2:
            if st.button("Edit", key=f"edit_{row['Request ID']}"):
                st.session_state.selected_req = row['Request ID']
                # st.switch_page("jd_edit.py")
                # st.session_state.current_page = "jd_edit"
                # st.rerun()