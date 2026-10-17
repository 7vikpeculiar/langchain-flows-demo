"""Step 5 — persistent memory: the same ticket thread survives restarts.

    START ──▶ triage ──▶ draft_reply ──▶ review ──┬─ approved / max attempts ──▶ remember ──▶ END
                             ▲                    │
                             └──── needs fixes ───┘

Run in two separate processes:

    python scripts/05_memory.py first
    python scripts/05_memory.py followup
    python scripts/05_memory.py reset   # delete checkpoint DB and start over
"""

import operator
import sqlite3
import sys
from pathlib import Path
from typing import Annotated, TypedDict

from langchain.chat_models import init_chat_model
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from common import ChatGptModel

LOG_GRAPH = True  # True → per-node trace while the graph runs


def graph_log(*args, **kwargs) -> None:
    if LOG_GRAPH:
        print(*args, **kwargs)


TICKET = (
    "Hi, this is Sathvik from Acme. My order #4321 arrived yesterday but the "
    "keyboard is missing two keys. Can I get a replacement shipped to "
    "91 Market Street by Friday? Thanks."
)
FOLLOWUP = "Any update on the replacement for order?"

MAX_ATTEMPTS = 3

DRAFTER_SYSTEM = (
    "You are a support agent drafting short emails. "
)

model = init_chat_model(ChatGptModel())


class State(TypedDict):
    ticket: str
    history: Annotated[list[str], operator.add]
    triage: str
    reply: str
    feedback: str
    attempts: int
    approved: bool


def history_text(state: State) -> str:
    past = state.get("history", [])
    if not past:
        return ""
    return "Previous conversation:\n" + "\n---\n".join(past) + "\n\n"


def triage(state: State) -> dict:
    response = model.invoke(
        f"{history_text(state)}"
        f"Customer ticket:\n{state['ticket']}\n\n"
        "Reply with one line: category (billing/shipping/defect/other) "
        "and priority (low/medium/high)."
    )
    return {"triage": response.content}


def draft_reply(state: State) -> dict:
    attempt = state["attempts"] + 1
    graph_log(f"\n── node: draft_reply (attempt {attempt}) ──")

    prompt = (
        f"{history_text(state)}"
        f"Customer ticket:\n{state['ticket']}\n\n"
        f"Triage:\n{state['triage']}\n\n"
        "Draft a short, friendly support email."
    )
    if state["feedback"]:
        prompt += (
            f"\n\nPrevious draft:\n{state['reply']}\n\n"
            f"A reviewer found these issues. Fix them:\n{state['feedback']}"
        )

    messages = [("human", prompt)]
    if not state["feedback"]:
        messages.insert(0, ("system", DRAFTER_SYSTEM))

    response = model.invoke(messages)
    graph_log("out: reply =", response.content[:80].replace("\n", " "), "...")
    return {"reply": response.content, "attempts": attempt}


def review(state: State) -> dict:
    graph_log("\n── node: review ──")
    response = model.invoke(
        f"{history_text(state)}"
        f"Customer ticket:\n{state['ticket']}\n\n"
        f"Draft reply:\n{state['reply']}\n\n"
        "Check the draft against this list:\n"
        "1. Mentions the order number.\n"
        "2. Consistent with the previous conversation, if any.\n"
        "3. Does not promise anything the ticket doesn't support.\n\n"
        "If everything passes, reply with exactly: APPROVED\n"
        "Otherwise reply with: FIX: <what to change, one line>"
    )
    verdict = response.content.strip()
    if verdict.upper().startswith("FIX:"):
        approved = False
    else:
        last_line = verdict.splitlines()[-1].strip().upper()
        approved = last_line == "APPROVED" or last_line.startswith("APPROVED")
    graph_log("out: verdict =", verdict)
    return {"approved": approved, "feedback": "" if approved else verdict}


def remember(state: State) -> dict:
    graph_log("\n── node: remember ──")
    turn = f"Customer: {state['ticket']}\nSupport: {state['reply']}"
    graph_log("out: saved turn to checkpoint history")
    return {"history": [turn]}


def route(state: State) -> str:
    """Conditional edge after review: loop back or save to memory."""
    if state["approved"] or state["attempts"] >= MAX_ATTEMPTS:
        return "remember"
    return "draft_reply"


graph = StateGraph(State)
graph.add_node("triage", triage)
graph.add_node("draft_reply", draft_reply)
graph.add_node("review", review)
graph.add_node("remember", remember)

graph.add_edge(START, "triage")
graph.add_edge("triage", "draft_reply")
graph.add_edge("draft_reply", "review")
graph.add_conditional_edges("review", route, ["draft_reply", "remember"])
graph.add_edge("remember", END)

DB_PATH = Path(__file__).resolve().parent.parent / "tickets.db"


def make_app():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return graph.compile(checkpointer=SqliteSaver(conn))


def reset_checkpoint() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("Deleted checkpoint DB:", DB_PATH)
    else:
        print("Nothing to reset (no DB at", DB_PATH, ")")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "first"
    if cmd == "reset":
        reset_checkpoint()
        raise SystemExit(0)

    if cmd not in ("first", "followup"):
        raise SystemExit("Usage: python 05_memory.py [first|followup|reset]")

    app = make_app()

    which = cmd
    ticket = TICKET if which == "first" else FOLLOWUP
    config = {"configurable": {"thread_id": "ticket-4321"}}

    # Reset per-turn fields; history is restored from the checkpoint and grows.
    initial = {
        "ticket": ticket,
        "triage": "",
        "reply": "",
        "feedback": "",
        "attempts": 0,
        "approved": False,
    }

    result = app.invoke(initial, config)

    print("\n══ Final ══")
    print("Turns in history:", len(result["history"]))
    print("Attempts:", result["attempts"], "| Approved:", result["approved"])
    print("Reply:\n", result["reply"])

    # Peek at persisted memory:
    # print(app.get_state(config).values["history"])

    # To watch step by step (set LOG_GRAPH = True):
    # for step in app.stream(initial, config, stream_mode="updates"):
    #     graph_log("graph update:", step)
