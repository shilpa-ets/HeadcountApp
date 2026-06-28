import streamlit as st
import my_requests

def show():

    # st.title("Headcount Planning Workspace")

    st.markdown(
        """
        Create, review, and route headcount requests. Managers can use the
        existing structured form or try a new conversational HR AI experience
        to generate a job description.
        """
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div style="
            border:1px solid #E5E7EB;
            border-radius:12px;
            padding:20px;
            background-color:white;
            box-shadow:0 1px 4px rgba(0,0,0,0.08);
            min-height:180px;
        ">
            <h4>📄 My Open Reqs</h4>
            <h1 style="margin-bottom:0;">3</h1>
            <p style="color:#6B7280;">1 awaiting revision</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="
            border:1px solid #E5E7EB;
            border-radius:12px;
            padding:20px;
            background-color:white;
            box-shadow:0 1px 4px rgba(0,0,0,0.08);
            min-height:180px;
        ">
            <h4>⏳ Pending Review</h4>
            <h1 style="margin-bottom:0;">7</h1>
            <p style="color:#6B7280;">Next review: June 9</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="
            border:1px solid #E5E7EB;
            border-radius:12px;
            padding:20px;
            background-color:white;
            box-shadow:0 1px 4px rgba(0,0,0,0.08);
            min-height:180px;
        ">
            <h4>✅ Approved This Quarter</h4>
            <h1 style="margin-bottom:0;">14</h1>
            <p style="color:#16A34A;">+3 vs last quarter</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div style="
            border:1px solid #E5E7EB;
            border-radius:12px;
            padding:20px;
            background-color:white;
            box-shadow:0 1px 4px rgba(0,0,0,0.08);
            min-height:180px;
        ">
            <h4>🎯 Avg Screening Score</h4>
            <h1 style="margin-bottom:0;">84</h1>
            <p style="color:#6B7280;">Out of 100</p>
        </div>
        """, unsafe_allow_html=True)

    my_requests.show()