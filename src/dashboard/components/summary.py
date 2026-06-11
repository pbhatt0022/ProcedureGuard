"""
Dashboard Component — Compliance Summary

Displays:
  - Overall adherence score (0–100%)
  - Step-by-step verdict table (Compliant / Deviation / Unable to Verify)
  - Deviation count + Unable to Verify count

Owner: Person D (dashboard)
"""
import streamlit as st


def render_summary(run_id: str) -> None:
    """Render the compliance summary view for a given run."""
    # TODO Week 4: fetch verdicts from Cosmos DB, compute score, render table
    st.subheader("Compliance Summary")
    st.caption(f"run_id: {run_id}")
    st.info("Summary not yet implemented.")
