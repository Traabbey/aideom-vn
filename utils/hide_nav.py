import streamlit as st

def hide_auto_nav():
    """Hides the default Streamlit sidebar page navigation container using CSS."""
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
