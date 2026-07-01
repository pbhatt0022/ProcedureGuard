from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agents.qa_agent import QAAgent
from src.config import get_config

SESSION_ID = "demo-session"


def _ask_once(agent: QAAgent, question: str, run_id: str = "RUN-102") -> None:
    print(f"Question: {question}")
    print(agent.answer(question, run_id=run_id, session_id=SESSION_ID))
    print("-" * 80)


def _interactive_loop(agent: QAAgent, run_id: str = "RUN-102") -> None:
    print("Agent 4 interactive mode. Type a question and press Enter.")
    print("Type 'exit' or 'quit' to stop.")
    print("-" * 80)

    while True:
        try:
            question = input("You> ").strip()
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break

        print("Agent 4>")
        print(agent.answer(question, run_id=run_id, session_id=SESSION_ID))
        print("-" * 80)


def main() -> None:
    config = get_config()
    if not config.gpt_settings_configured():
        print("Azure OpenAI credentials not configured. Skipping GPT Agent test.")
        return

    agent = QAAgent(config=config)
    if len(sys.argv) > 1:
        _ask_once(agent, question=" ".join(sys.argv[1:]), run_id="RUN-102")
        return

    _interactive_loop(agent, run_id="RUN-102")


if __name__ == "__main__":
    main()
