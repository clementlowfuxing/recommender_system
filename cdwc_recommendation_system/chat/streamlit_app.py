"""
Streamlit chat UI for the CDWC Talent Recommendation Engine.

Run:  streamlit run chat/streamlit_app.py
"""

import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
from chat.orchestrator import Orchestrator

st.set_page_config(page_title="CDWC Talent Search", page_icon="🔍")
st.title("🔍 CDWC Talent Recommendation Chat")
st.caption(
    "Ask in plain English — e.g. "
    '"I need a senior Python developer with ML experience, 5+ years"'
)

# Initialise session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "orch" not in st.session_state:
    st.session_state.orch = Orchestrator()

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Describe the talent you need..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Searching talent pool..."):
            reply = st.session_state.orch.handle(prompt)
        st.markdown(f"```\n{reply}\n```")

    st.session_state.messages.append({"role": "assistant", "content": reply})
