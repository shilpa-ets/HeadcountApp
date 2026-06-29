import streamlit as st

def show_process_flow(current_step=1):

    steps = [
        "Generate\nJD",
        "Submit\nRequest",
        "BU SLT\nReview & Approval",
        "People\nProcess\nReview",
        "HRBP Review",
        "Division\nFinance\nReview",
        "HRTA\nReview",
        "Senior\nLeadership\nReview"
    ]

    cols = st.columns(len(steps) * 2 - 1)

    for i in range(len(steps)):

        # Circle
        circle_col = cols[i * 2]

        color = "#28A745" if i + 1 <= current_step else "#BDBDBD"

        circle_col.markdown(
            f"""
            <div style="text-align:center;">
                <div style="
                    width:45px;
                    height:45px;
                    border-radius:50%;
                    background:{color};
                    color:white;
                    font-weight:bold;
                    line-height:45px;
                    margin:auto;">
                    {i+1}
                </div>
                <div style="
                    font-size:11px;
                    margin-top:8px;
                    text-align:center;">
                    {steps[i].replace(chr(10), '<br>')}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Connector line
        if i < len(steps) - 1:

            line_col = cols[i * 2 + 1]

            line_color = "#28A745" if i + 1 < current_step else "#D3D3D3"

            line_col.markdown(
                f"""
                <div style="
                    margin-top:22px;
                    height:4px;
                    background:{line_color};
                    width:100%;">
                </div>
                """,
                unsafe_allow_html=True
            )
