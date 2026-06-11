"""
Dashboard Component — Deviation Timeline

Displays a chronological timeline of deviation events, each with:
  - Video timestamp
  - SOP step reference
  - Keyframe thumbnail
  - Verdict and confidence score

Owner: Person D (dashboard)
"""
import streamlit as st


def render_deviation_timeline(run_id: str) -> None:
    """Render the deviation timeline for a given run."""
    # TODO Week 4: fetch deviation verdicts, load keyframes from Blob, render timeline
    st.subheader("Deviation Timeline")
    st.info("Deviation timeline not yet implemented.")
