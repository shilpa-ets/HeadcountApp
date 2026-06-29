import streamlit as st
from process_flow import show_process_flow

def hide_streamlit_toolbar():
    st.markdown("""
    <style>

    /* Hide Deploy / Toolbar */
    [data-testid="stToolbar"] {
        display: none;
    }

    /* Hide hamburger menu */
    #MainMenu {
        visibility: hidden;
    }

    /* Hide footer */
    footer {
        visibility: hidden;
    }

    /* Optional: Hide header */
    header {
        visibility: hidden;
    }

    </style>
    """, unsafe_allow_html=True)            

import streamlit as st

def maximize_page_space():
    st.markdown("""
    <style>

    /* Hide Streamlit toolbar */
    [data-testid="stToolbar"] {
        display: none;
    }

    /* Hide menu */
    #MainMenu {
        visibility: hidden;
    }

    /* Hide footer */
    footer {
        visibility: hidden;
    }

    /* Hide header */
    header {
        display: none;
    }

    /* Reduce top whitespace */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    </style>
    """, unsafe_allow_html=True)

st.set_page_config(layout="wide")

hide_streamlit_toolbar()
maximize_page_space()

# Initialize page
if "page" not in st.session_state:
    st.session_state.page = "Home"

# Header
col1, col2 = st.columns([8, 1])

# with col1:
#     st.image("ETS_Digital_RGB_Ink.jpeg", width=100)

with col1:
    st.markdown(
        """
        <h1 style='margin-top:10px;color:#0078D4;'>
        Headcount Planning Workspace
        </h2>
        """,
        unsafe_allow_html=True
    )

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

if "selected_req" not in st.session_state:
    st.session_state.selected_req = None

# st.divider()

# Sidebar Menu
with st.sidebar:

    st.set_page_config(
        initial_sidebar_state="expanded"
    )

    # st.image("ETS_Digital_RGB_Ink.jpeg", width=100)

    st.markdown("### Navigation")

    pages = {
        "🏠 Home": "Home",
        "📝 Submit a Request": "Submit",
        "👥 BU Review": "SLT Review",
        "📖 People Process Review": "People Process Review",
        "📖 HRBP Review": "HRBP Review",
        "📖 Division Finance Review": "Comp Review",
        "📖 HRTA Review": "HRTA Review",
        "📖 Senior Leadership Review": "Senior Leadership Review",
        "📊 Session Analytics": "Session Analytics",
        "⚙️ BU Settings": "BU Settings",
    }

    # =====================================================
    # Sidebar navigation with active page highlight
    # =====================================================
    #0078D4
    st.markdown("""
    <style>
    .active-nav-item {
        background-color: #D0D7DE;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        border: 2px solid #D0D0D0;
        width: 100%;
        box-sizing: border-box;
        min-height: 42px;
        margin-bottom: 12px;
    }

    .inactive-nav-item {
        padding: 10px;
        border-radius: 10px;
        border: 2px solid transparent;
        width: 100%;
        box-sizing: border-box;
        min-height: 42px;
        margin-bottom: 12px;
    }

    .inactive-nav-space {
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

    for label, page in pages.items():

        # If this is the currently selected page, show highlighted block
        if st.session_state.page == page:
            st.markdown(
                f"""
                <div class="active-nav-item">
                    {label}
                </div>
                """,
                unsafe_allow_html=True
            )

        # Otherwise show normal clickable button
        else:
            if st.button(
                label,
                use_container_width=True,
                key=f"nav_{page}"
            ):
                st.session_state.page = page
                st.session_state.current_page = "home"
                st.rerun()

            # st.markdown(
            #     """
            #     <div class="inactive-nav-space"></div>
            #     """,
            #     unsafe_allow_html=True
            # )

    # for label, page in pages.items():
    #     if st.button(label, use_container_width=True):
    #         st.session_state.page = page

# Main Content
page = st.session_state.page

if st.session_state.current_page == "jd_edit":
    import jd_edit
    jd_edit.show()

if page == "Home":
    # st.header("Home")
    import home_page
    home_page.show()

elif page == "Submit":
    import jd2
    jd2.show()

elif page == "SLT Review":
    show_process_flow(current_step=3)
    st.header("SLT Review")

elif page == "People Process Review":
    show_process_flow(current_step=4)
    st.header("People Process Review")

elif page == "HRBP Review":
    show_process_flow(current_step=5)
    st.header("HRBP Review")

elif page == "Division Finance Review":
    show_process_flow(current_step=6)
    st.header("Division Finance Review")

elif page == "HRTA Review":
    show_process_flow(current_step=7)
    st.header("HRTA Review")

elif page == "Senior Leadership Review":
    show_process_flow(current_step=8)
    st.header("Senior Leadership Review")

elif page == "Session Analytics":
    import session_analytics
    session_analytics.show()

elif page == "BU Settings":
    st.header("BU Settings")
