"""
Dashboard Component — Chat Interface

Q&A panel routed to Agent 3 (qa_agent.py).
Allows the operator to ask questions about a specific run and receive
evidence-backed answers (verdict references, timestamps, SOP sections).

Owner: Person D (dashboard)
"""
import streamlit as st

from src.agents.qa_agent import answer_question


def render_chat(run_id: str) -> None:
    """Render the Q&A chat panel for a given run."""
    st.subheader("Ask about this run")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question about this verification run..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # TODO Week 4: wire to answer_question() once Agent 3 is implemented
            response = "Agent 3 not yet implemented."
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
