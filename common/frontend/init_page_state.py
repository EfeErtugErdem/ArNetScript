import streamlit as st

def init_page_state(page_name: str):
    if "page_states" not in st.session_state:
        st.session_state["page_states"] = {}
    if page_name not in st.session_state["page_states"]:
        st.session_state["page_states"][page_name] = {}
    page_state = st.session_state["page_states"][page_name]

    return page_state