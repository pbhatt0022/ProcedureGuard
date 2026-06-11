"""
Layer 5 — Streamlit Dashboard

Entry point for the ProcedureGuard quality verification dashboard.
Run with: streamlit run src/dashboard/app.py

Views:
  1. Upload — SOP PDF + video upload, triggers Flow 1 pipeline
  2. Report — compliance summary, adherence score, deviation timeline
  3. Evidence — side-by-side video keyframes + SOP reference per step
  4. Chat — Q&A interface routed to Agent 3

Owner: Person D (dashboard)
"""
import streamlit as st

from src.dashboard.components.chat import render_chat
from src.dashboard.components.deviation_timeline import render_deviation_timeline
from src.dashboard.components.evidence_viewer import render_evidence_viewer
from src.dashboard.components.summary import render_summary

st.set_page_config(
    page_title="ProcedureGuard",
    page_icon="🔍",
    layout="wide",
)

st.title("ProcedureGuard")
st.caption("Manufacturing Procedure Verification — Azure AI Foundry")

# ── Sidebar: upload + run selection ─────────────────────────────────────────
with st.sidebar:
    st.header("New Verification Run")
    sop_file = st.file_uploader("SOP Document (PDF)", type=["pdf"])
    video_file = st.file_uploader("Manufacturing Video (MP4)", type=["mp4", "mov", "avi"])

    if st.button("Run Pipeline", disabled=not (sop_file and video_file)):
        # TODO Week 4: call pipeline.run_pipeline(), show spinner
        st.info("Pipeline not yet implemented.")

    st.divider()
    st.header("Past Runs")
    # TODO Week 4: list run_ids from Cosmos DB for selection
    run_id = st.selectbox("Select run", options=[], placeholder="No runs yet")

# ── Main area: tabbed report ─────────────────────────────────────────────────
if run_id:
    tab_summary, tab_evidence, tab_chat = st.tabs(["Summary", "Evidence", "Chat"])

    with tab_summary:
        render_summary(run_id)

    with tab_evidence:
        render_evidence_viewer(run_id)

    with tab_chat:
        render_chat(run_id)
else:
    st.info("Upload an SOP and video, or select a past run from the sidebar.")
