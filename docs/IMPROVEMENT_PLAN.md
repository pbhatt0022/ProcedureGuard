# ProcedureGuard — State Assessment & Improvement Plan

> Written Week 4 (June 19). A grounded "as-built vs as-designed" comparison and a prioritized
> roadmap for what to build next. Companion to [ARCHITECTURE.md](ARCHITECTURE.md) (the design),
> [DECISIONS_AND_RATIONALE.md](DECISIONS_AND_RATIONALE.md) (why things are the way they are), and
> [UI_BUILD_PLAN.md](UI_BUILD_PLAN.md) (the frontend spec).

---

## 1. Executive summary

The pipeline **works end to end** for the demo: SOP PDF → tiered checklist → time-windowed
video analysis (OpenCV + GPT-4o Vision) → four-verdict reasoning → Streamlit dashboard, with a
Next.js frontend now in active development. 69/69 tests pass.

But the system as it runs today is **narrower than the documented 5-layer Azure architecture**.
Three of the five layers are partially "as-designed but not wired in": durable storage (Cosmos),
binary archival + real keyframes (Blob), and the Foundry Agent/MCP orchestration. And the single
most important *product* metric — deviation **recall** — sits at ~25% by deliberate design choice
(precision-first), which is the biggest gap between "it demos" and "it's useful."

This plan separates the work into four themes, ranked by leverage:

1. **Accuracy & recall** — the core value. Today the system rarely catches a real deviation.
2. **Durable evidence** — persistence + real keyframes, so a run is an auditable record, not an
   ephemeral JSON blob.
3. **Architecture fidelity** — a fork: either integrate the Foundry agents + MCP, or formally
   retire the stubs so the docs match reality.
4. **Product & frontend** — finish the Next.js app and wire it to live runs.

---

## 2. Current state (as-built, honest)

| Layer | Component | Status | Notes |
|---|---|---|---|
| 1 · Input | SOP PDF + video intake | ⚠️ Partial | Local file path + manual Blob **SAS URL**. No upload-to-Blob flow; `blob_client.upload_sop/upload_video` exist but are **never called**. |
| 2 · Extraction | Document Intelligence (`sop_extractor`) | ✅ Live | Layout v4.0, in the pipeline. |
| 2 · Extraction | Content Understanding | ✅ Removed (intentional) | Replaced by OpenCV duration probe + GPT-4o Vision Phase 2 (June 18). |
| 2 · Extraction | AI Search "Visual SOP Index" (`sop_indexer`) | ❌ Unwired | Real implementation exists; **never imported**. Diagrams/figures/symbols are not indexed; Agent 1 gets no visual SOP context. |
| 3 · Agents | Agent 1 SOP / Agent 2 Reasoning (`sop_agent`, `reasoning_agent`) | ❌ Unwired | Real wrappers exist (Owner: Person A/C) but **nothing imports them**. Pipeline calls `generate_checklist` / `reason_step` directly. |
| 3 · Agents | Agent 3 Q&A (`qa_agent`) | ⚠️ Live, simplified | Works, but stuffs the **entire** verdicts dict into one GPT-4o prompt. No **MCP tools**, no retrieval — won't scale past one run in context. |
| 4 · Storage | Cosmos DB (`cosmos_client`) | ❌ Unwired | Real client exists; **never called**. `run_pipeline()` just returns a dict. Runs are saved as local JSON by scripts, or held in Streamlit `session_state`. No run history, no cross-run queries. |
| 4 · Storage | Blob Storage (`blob_client`) | ❌ Unwired | Same. `keyframe_blob_path` is a **convention string** (`keyframes/{run}/{step}.jpg`) — **no image is ever extracted or uploaded**, so the evidence drawer has no real thumbnail. |
| 5 · Presentation | Streamlit dashboard | ✅ Live | Full six-tab review surface; the current demo deliverable. |
| 5 · Presentation | Next.js frontend | 🚧 In progress | Stack matches `UI_BUILD_PLAN.md` (Next 16 / React 19 / Radix / TanStack / Motion / Fluent). Shell + 6-tab run view (1280-line `runs/page.tsx`) + perimeter pages + `normalizer.ts`. Reads **static demo JSON**, not live runs. |

**Against the stated success criteria:**

| Criterion | Target | Actual | Verdict |
|---|---|---|---|
| SOP step extraction coverage | >90% | ~29/29 on STEMFIE demo | ✅ Met (on demo) |
| Compliance verdict accuracy | >80% agreement | Precision 100%, **Recall 25%** (TP=1/FP=0/FN=3, 4 clips) | ⚠️ Precision yes, recall no; eval set too small to claim either robustly |
| E2E latency | <5 min/video | ~10–14 vision calls/clip, sequential | ⚠️ Likely OK on 4–5 min clips; unmeasured/uncharted |
| Dashboard demo-ready | Week 4 | Streamlit live; Next.js in progress | ✅ Met |

---

## 3. The gaps that matter (and why)

### Gap 1 — Deviation recall is the product's weak point
The whole pitch is "catch deviations paper sampling misses." Today the system catches ~1 in 4.
Root causes, all documented in DECISIONS_AND_RATIONALE:
- **Vocabulary mismatch.** Phase 2 describes parts generically ("pink connector", "gray rod");
  SOP criteria use functional names ("pulley", "front chassis", "bracket screw"). Absence
  inference can only fire when a curated `key_objects` token is known to appear in Phase 2 output
  — so it's gated off for almost every step (see the check-025 pulley decision).
- **Resolution ceiling.** 1 fps / 512–768 px overhead video genuinely can't resolve torque,
  seating, orientation — those are honestly routed to *Requires Inspection*. That's correct, but
  it means a large fraction of every SOP is never video-verified.
- **Precision-first stance.** `apply_absence_inference` is deliberately conservative (3 guards).
  Right call for trust; but recall was never the optimization target.

### Gap 2 — Runs aren't durable records
A "verification record keyed by `run_id`" that an auditor can retrieve is the core promise. Today
the record lives in a returned dict + a hand-saved JSON file. No Cosmos = no run history, no
cross-run dashboard, no reviewer decisions that persist, no archival guarantee.

### Gap 3 — Evidence has no actual image
`keyframe_blob_path` points at a blob that was never written. The evidence drawer's most
trust-building element — *the frame that proves the verdict* — is a dead path. This is a small
code gap with outsized product impact.

### Gap 4 — The architecture story diverges from the code
Three named Azure services (Cosmos, Blob, AI Search) and the 3-agent Foundry design are in every
diagram but not in the running path. For a supervised academic project this is a defensibility
risk: a reviewer who opens the code sees direct function calls, not the agent mesh. Either close
the gap (integrate) or close it the other way (retire + re-document).

---

## 4. Improvement opportunities, by theme

### Theme A — Accuracy & recall (highest leverage)

| Idea | What it is | Impact | Effort |
|---|---|---|---|
| **A1. Checklist-aware Phase 2** | Instead of "describe what you see," ask GPT-4o Vision targeted yes/no questions per checklist item ("Is a pulley mounted on the rear axle in this window?"). Named in the decision log as *the real fix* for the pulley case. | High — directly lifts recall without the vocabulary-matching gamble | Med |
| **A2. Vocabulary bridge** | Add a synonym/alias map between SOP functional terms and likely Phase 2 descriptors (pulley↔"pink connector"), or have Agent 1 emit expected visual descriptors per `key_object`. Makes absence inference usable on more steps. | High | Low–Med |
| **A3. Wire the Visual SOP Index (AI Search)** | Actually call `sop_indexer`; let Agent 1 retrieve diagram/figure context when generating `observable_action` and `key_objects`. Better checklist → better matching. | Med–High | Med–High |
| **A4. Selective high-res / cropped frames** | For borderline fine-detail steps, pull a few full-res cropped frames around the action region instead of blanket-routing to *Requires Inspection*. Recovers some currently-abstained steps. | Med | Med |
| **A5. Expand the eval harness** | Upload the pending clips (`17_assy_1_5`, `18_assy_2_5`), resolve the UNRESOLVED GT mappings, grow beyond 4 clips. Make precision/recall claims statistically meaningful — and turn every A1–A4 change into a measured delta. | High (de-risks everything else) | Low–Med |

> Sequencing note: **do A5 first or alongside A1.** Without a bigger eval set, you can't tell
> whether checklist-aware Phase 2 actually helped or just moved errors around — the exact failure
> mode the harness was built to prevent.

### Theme B — Durable evidence (persistence)

| Idea | What it is | Impact | Effort |
|---|---|---|---|
| **B1. Real keyframe extraction + upload** | In `compliance_engine`/`pipeline`, grab the evidence-window frame via OpenCV (already open in Phase 2), write it through `blob_client.write_keyframe`, store the real returned path. Lights up the evidence drawer thumbnail. | High (product feel) | Low |
| **B2. Wire Cosmos persistence** | Call `cosmos_client.write_*` at the end of `run_pipeline`; have the dashboard read from Cosmos. Unlocks run history + cross-run dashboard + the "retrieve an old record" audit story. | High | Med |
| **B3. Blob intake flow** | Replace manual SAS URLs with an upload step (`upload_sop`/`upload_video`) so a user can drop a PDF + MP4 and get a run, with originals archived. | Med | Med |
| **B4. Persist reviewer decisions** | When a reviewer confirms/overrides a verdict, write it back (Cosmos) so disposition survives reload and feeds the audit trail. Today review state is UI-only. | Med | Med |

### Theme C — Architecture fidelity (a decision, not just work)

**The fork:** integrate vs. retire.

- **C1. Integrate** — route the pipeline through `sop_agent`/`reasoning_agent`, and rebuild
  `qa_agent` on **MCP tools** (Cosmos + Blob as tools) instead of prompt-stuffing. Highest
  architecture-story fidelity; matches every diagram; best "defensible to supervisor" outcome.
  Cost: real Foundry Agent Service + MCP endpoint work, and the agents only add value once B2
  (Cosmos) is wired (they read/write it).
- **C2. Retire** — delete the unwired agent/storage/indexer stubs, and re-document the
  architecture as the honest "direct-call MVP." Lowest effort; matches the project's stated
  honesty principle; loses the multi-agent narrative.

**Recommendation:** a middle path. Do **B2 + B1** first (storage is the prerequisite for agents
to do anything), then **C1 for Agent 3 only** (MCP Q&A is the most visible, most defensible agent
and the one already half-live). Leave Agents 1–2 as documented "thin wrappers, integration
deferred" rather than deleting teammate-owned code — but stop drawing them as load-bearing in the
primary diagram until they are.

### Theme D — Product & frontend

| Idea | What it is | Impact | Effort |
|---|---|---|---|
| **D1. Wire Next.js to live data** | Replace static `src/data/*.json` import with an API route reading the run store (Cosmos via B2, or the saved JSON in the interim). | High | Med |
| **D2. Finish the evidence drawer** | Ensure the hero interaction (row → keyframe + SOP excerpt + reasoning + video seek, with `j/k` retarget) is fully built; depends on B1 for real thumbnails. | High | Med |
| **D3. Report export (PDF/CSV)** | Today only JSON export exists. The "formal, defensible record" needs PDF + CSV with the limitations statement and audit timeline. | Med | Med |
| **D4. Decide primary surface** | Streamlit and Next.js now overlap. Pick one as the demo surface; keep the other only if it earns its maintenance. | Med (focus) | Low |

---

## 5. Recommended roadmap

Phased by dependency and leverage. Each phase ends in a demoable, measurable state.

### Now (this week)
- **A5** expand eval harness + upload pending clips → trustworthy accuracy numbers.
- **B1** real keyframe extraction + upload → evidence drawer shows a real frame.
- **A2** vocabulary bridge (low-effort recall win, measured against A5).

### Next (Week 3 work, per the original plan)
- **B2** Cosmos persistence → run history + durable records.
- **A1** checklist-aware Phase 2 → the main recall lift, validated on the expanded eval set.
- **D1 + D2** wire the Next.js frontend to live data and finish the evidence drawer.

### Later (post-MVP / stretch)
- **C1 (Agent 3 via MCP)** → defensible agent story on top of the now-real Cosmos/Blob.
- **A3** Visual SOP Index (AI Search) → richer checklists.
- **A4** selective high-res frames; **B3** Blob intake; **B4** reviewer persistence; **D3** PDF/CSV export.
- **C decision** finalized: integrate Agents 1–2 or formally retire and re-document.

### Effort × impact quick map
```
IMPACT ↑
 high │ A1  A5        B1
      │ A2  B2  D1 D2
  med │ A3  A4  B3 B4  D3  C1
      │                 D4
  low │
      └──────────────────────────→ EFFORT
        low      med        high
```

---

## 6. Decisions needed from you

1. **Architecture fork (Theme C):** integrate the Foundry agents + MCP, or retire the stubs and
   re-document as a direct-call MVP? (Recommendation: MCP for Agent 3 only; defer/keep 1–2.)
2. **Primary demo surface (D4):** Streamlit, Next.js, or both? Drives where finishing effort goes.
3. **Recall vs. precision posture:** is precision-first still the rule, or do we accept a few
   false positives to raise recall now that the eval harness can measure the trade?
4. **Scope realism:** this is an internship MVP — which of "Now/Next" is in scope before the
   final demo, and which is explicitly "future work" in the writeup?

---

## 7. Cleanup completed in this pass

- Repaired `scripts/run_industreal_demo.py` — it read the deleted `demo_results_correct_v3.json`;
  now reads the verbatim checklist from `demo_results_industreal_23_assy_0_1_baseline.json`.
- Fixed the stale Content-Understanding reference in `schemas/video_observations.json` `_note`.
- Removed 57 stale/corrupted `__pycache__` bytecode files (incl. Windows hot-reload `.pyc.NNNN`
  temp artifacts). All regenerable; tests still 69/69 green.
- Verified: no unused imports in `src/`; no lingering references to removed CU symbols
  (`analyze_video`, `parse_observations`, `COMPLIANCE_FIELD_SCHEMA`, `coverage_note`) in code.

### Flagged, not deleted (need your call)
- `scripts/regenerate_demo_windowed.py` — a one-shot v2→v3 windowing migration whose `_v2.json`
  inputs no longer exist. Genuinely dead (can't run), but **untracked** (deleting is
  irreversible). Recommend deletion; left in place pending your confirmation.
- The unwired Layer 3/4 modules (`sop_agent`, `reasoning_agent`, `cosmos_client`, `blob_client`,
  `sop_indexer`) are real, teammate-owned, documented-as-deferred scaffolding — **not** accidental
  dead code. Their fate is the Theme C decision above, not a cleanup.
