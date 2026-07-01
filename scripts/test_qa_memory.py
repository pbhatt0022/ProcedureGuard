from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.qa_agent import QAAgent
from src.config import get_config
from src.providers.conversation_state_store import ConversationStateStore
from src.providers.sqlite_data_store import SQLiteDataStore


def main() -> None:
    config = get_config()
    state_store = ConversationStateStore(use_redis=False, ttl_seconds=config.session_ttl_seconds)
    agent = QAAgent(config=config, state_store=state_store)
    data_store = SQLiteDataStore(db_path=config.sqlite_db_path)
    session_id = "memory-smoke"

    verdicts = data_store.query_verdicts(run_id="RUN-102", step_id="STEP-03")
    resolution = agent.resolve_query_context(
        question="Tell me about step 3",
        run_id="RUN-102",
        session_id=session_id,
    )
    agent._persist_resolution_state(resolution, tool_outputs=[{"verdicts": verdicts}])

    follow_up_questions = [
        "Why was it flagged?",
        "Show me the evidence",
        "Who is assigned?",
    ]

    print("Session memory smoke test")
    print("-" * 80)
    print(f"Initial resolution: run={resolution.run_id}, step={resolution.step_id}, intent={resolution.intent}")
    print("-" * 80)

    for question in follow_up_questions:
        follow_up = agent.resolve_query_context(
            question=question,
            run_id="RUN-102",
            session_id=session_id,
        )
        print(f"Question: {question}")
        print(
            "Resolved context: "
            f"run={follow_up.run_id}, step={follow_up.step_id}, ticket={follow_up.ticket_id}, "
            f"incident={follow_up.incident_id}, intent={follow_up.intent}, "
            f"needs_clarification={follow_up.needs_clarification}"
        )
        print("-" * 80)


if __name__ == "__main__":
    main()
