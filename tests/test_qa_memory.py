from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.agents.qa_agent import QAAgent
from src.config import Config
from src.providers.conversation_state_store import ConversationStateStore
from src.providers.sqlite_data_store import SQLiteDataStore


class QAMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self._temp_dir.name) / "procedureguard-test.db"
        self.config = Config(sqlite_db_path=str(db_path))
        self.state_store = ConversationStateStore(use_redis=False, ttl_seconds=3600)
        self.agent = QAAgent(config=self.config, state_store=self.state_store)
        self.data_store = SQLiteDataStore(db_path=db_path)
        self.session_id = "unit-test-session"

    def tearDown(self) -> None:
        self._temp_dir.cleanup()

    def test_step_3_normalizes_to_step_03(self) -> None:
        resolution = self.agent.resolve_query_context(
            question="Tell me about step 3",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertEqual(resolution.step_id, "STEP-03")

    def test_step_03_uppercase_format_works(self) -> None:
        resolution = self.agent.resolve_query_context(
            question="Tell me about STEP-03",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertEqual(resolution.step_id, "STEP-03")

    def test_step_dash_03_format_works(self) -> None:
        resolution = self.agent.resolve_query_context(
            question="Tell me about step-03",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertEqual(resolution.step_id, "STEP-03")

    def test_third_step_normalizes_to_step_03(self) -> None:
        resolution = self.agent.resolve_query_context(
            question="Tell me about the third step",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertEqual(resolution.step_id, "STEP-03")

    def test_follow_up_flagged_question_uses_step_context(self) -> None:
        self._prime_step_three_context()
        resolution = self.agent.resolve_query_context(
            question="Why was it flagged?",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertEqual(resolution.step_id, "STEP-03")
        self.assertFalse(resolution.needs_clarification)

    def test_follow_up_show_evidence_uses_step_three_context(self) -> None:
        self._prime_step_three_context()
        resolution = self.agent.resolve_query_context(
            question="Show me the evidence",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertEqual(resolution.step_id, "STEP-03")
        self.assertEqual(resolution.evidence_ids, ["EV-1005", "EV-1006"])

    def test_follow_up_show_clip_uses_step_three_context(self) -> None:
        self._prime_step_three_context()
        resolution = self.agent.resolve_query_context(
            question="Show the clip",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertEqual(resolution.step_id, "STEP-03")
        self.assertEqual(resolution.intent, "clip_request")

    def test_follow_up_assignment_uses_ticket_context(self) -> None:
        self._prime_step_three_context()
        resolution = self.agent.resolve_query_context(
            question="Who is assigned?",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertEqual(resolution.ticket_id, "INC-2045")
        self.assertFalse(resolution.needs_clarification)

    def test_vague_flagged_question_without_context_asks_for_clarification(self) -> None:
        resolution = self.agent.resolve_query_context(
            question="Why was it flagged?",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertTrue(resolution.needs_clarification)
        self.assertEqual(resolution.clarification_prompt, "Which run, step, or ticket should I look up?")

    def test_serious_issues_maps_to_compliance_summary_with_severity_filters(self) -> None:
        resolution = self.agent.resolve_query_context(
            question="Any serious issues?",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertEqual(resolution.intent, "compliance_summary")
        self.assertEqual(resolution.severity_filters, ["High", "Critical"])

    def test_qa_review_first_maps_to_qa_review_summary(self) -> None:
        resolution = self.agent.resolve_query_context(
            question="What should QA review first?",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertEqual(resolution.intent, "qa_review_summary")

    def test_out_of_order_question_maps_to_sequence_query(self) -> None:
        resolution = self.agent.resolve_query_context(
            question="Was anything out of order?",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertEqual(resolution.intent, "sequence_query")

    def test_changed_after_review_uses_session_ticket_context(self) -> None:
        self._prime_step_three_context()
        resolution = self.agent.resolve_query_context(
            question="What changed after review?",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.assertEqual(resolution.intent, "reviewer_history")
        self.assertEqual(resolution.ticket_id, "INC-2045")
        self.assertFalse(resolution.needs_clarification)

    def test_redis_unavailable_falls_back_to_memory(self) -> None:
        fallback_store = ConversationStateStore(
            redis_url="redis://127.0.0.1:6399/0",
            ttl_seconds=3600,
            use_redis=True,
        )
        state = fallback_store.update(
            "fallback-session",
            current_run_id="RUN-102",
            current_step_id="STEP-03",
            last_intent="general",
        )
        loaded = fallback_store.load("fallback-session")
        self.assertEqual(fallback_store.backend_name, "memory")
        self.assertEqual(state.current_step_id, "STEP-03")
        self.assertEqual(loaded.current_run_id, "RUN-102")

    def test_sqlite_store_is_seeded_from_dummy_json(self) -> None:
        verdicts = self.data_store.query_verdicts(run_id="RUN-102", step_id="STEP-03")
        self.assertEqual(len(verdicts), 1)
        self.assertEqual(verdicts[0]["ticket_id"], "INC-2045")

    def test_last_answer_summary_is_stored(self) -> None:
        resolution = self.agent.resolve_query_context(
            question="Tell me about step 3",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        self.agent._persist_resolution_state(
            resolution,
            tool_outputs=[{"verdicts": self.data_store.query_verdicts(run_id="RUN-102", step_id="STEP-03")}],
            final_answer="STEP-03 was flagged because the torque sequence was incomplete.",
        )
        state = self.state_store.load(self.session_id)
        self.assertEqual(state.last_answer_summary, "STEP-03 was flagged because the torque sequence was incomplete.")

    def _prime_step_three_context(self) -> None:
        resolution = self.agent.resolve_query_context(
            question="Tell me about step 3",
            run_id="RUN-102",
            session_id=self.session_id,
        )
        tool_outputs = [
            {"verdicts": self.data_store.query_verdicts(run_id="RUN-102", step_id="STEP-03")},
            {"tickets": self.data_store.query_tickets(run_id="RUN-102", step_id="STEP-03")},
        ]
        self.agent._persist_resolution_state(resolution, tool_outputs=tool_outputs)


if __name__ == "__main__":
    unittest.main()
