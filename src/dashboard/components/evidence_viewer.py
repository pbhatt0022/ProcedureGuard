"""
Dashboard Component — Evidence Viewer

Side-by-side view of:
  - Left: keyframe thumbnail from the video at the relevant timestamp
  - Right: corresponding SOP step text and compliance criterion

Allows the QA manager to inspect the raw evidence behind each verdict.

Owner: Person D (dashboard)
"""
import streamlit as st


def render_evidence_viewer(run_id: str) -> None:
    """Render the evidence viewer for a given run."""
    # TODO Week 4: fetch verdicts, load keyframes from Blob, render side-by-side
    st.subheader("Evidence Viewer")
    st.info("Evidence viewer not yet implemented.")
