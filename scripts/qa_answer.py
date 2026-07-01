#!/usr/bin/env python3
"""Thin bridge: JSON arg → QAAgent.answer() → stdout JSON.

Called by the Next.js chat route:
    python scripts/qa_answer.py '{"question":"...","run_id":"...","session_id":"..."}'
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.agents.qa_agent import QAAgent

def main() -> None:
    payload = json.loads(sys.argv[1])
    agent = QAAgent()
    answer = agent.answer(
        payload["question"],
        run_id=payload.get("run_id", "RUN-102"),
        session_id=payload.get("session_id", "default"),
    )
    print(json.dumps({"answer": answer}))

if __name__ == "__main__":
    main()
