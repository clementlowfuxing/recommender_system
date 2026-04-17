"""
CLI chat interface for the CDWC Talent Recommendation Engine.

Run:  python chat/cli.py
"""

import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from chat.orchestrator import Orchestrator


def main() -> None:
    orch = Orchestrator()
    print("╔══════════════════════════════════════════════╗")
    print("║  CDWC Talent Recommendation Chat             ║")
    print("║  Type your request in plain English.         ║")
    print("║  Type 'quit' or 'exit' to leave.             ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        reply = orch.handle(user_input)
        print(f"\nAssistant:\n{reply}\n")


if __name__ == "__main__":
    main()
