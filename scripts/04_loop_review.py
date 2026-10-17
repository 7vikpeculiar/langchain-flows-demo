"""Step 4 — add a loop: the reply is reviewed and redrafted until it passes.

    START ──▶ triage ──▶ draft_reply ──▶ review ──┬─ approved / max attempts ──▶ END
                             ▲                    │
                             └──── needs fixes ───┘
"""

import json
from pathlib import Path
from typing import Literal, TypedDict

from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

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

MAX_ATTEMPTS = 3

DRAFTER_SYSTEM = (
    "You are a support agent drafting short emails. "
    "You often forget to include the order number even when the ticket mentions one."
)

model = init_chat_model(ChatGptModel())


class Triage(BaseModel):
    category: Literal["billing", "shipping", "defect", "other"]
    priority: Literal["low", "medium", "high"]


triage_model = model.with_structured_output(Triage)


class State(TypedDict):
    ticket: str
    triage: dict
    reply: str
    feedback: str   # reviewer's critique; empty on the first pass
    attempts: int   # incremented by draft_reply
    approved: bool  # set by review


def triage(state: State) -> dict:
    graph_log("\n── node: triage ──")
    result = triage_model.invoke(
        f"Customer ticket:\n{state['ticket']}\n\n"
        "Classify category and priority for this support ticket."
    )
    triage_data = result.model_dump()
    graph_log("out: triage =", triage_data)
    return {"triage": triage_data}


def draft_reply(state: State) -> dict:
    attempt = state["attempts"] + 1
    graph_log(f"\n── node: draft_reply (attempt {attempt}) ──")

    prompt = (
        f"Customer ticket:\n{state['ticket']}\n\n"
        f"Triage:\n{json.dumps(state['triage'])}\n\n"
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
        f"Customer ticket:\n{state['ticket']}\n\n"
        f"Draft reply:\n{state['reply']}\n\n"
        "Check the draft against this list:\n"
        "1. Mentions the order number.\n"
        "3. Does not promise anything the ticket doesn't support.\n\n"
        "If everything passes, reply with exactly: APPROVED\n"
        "Otherwise reply with: FIX: <what to change, one line>"
    )
    verdict = response.content.strip()
    # Small models often add prose before a final "APPROVED" line.
    if verdict.upper().startswith("FIX:"):
        approved = False
    else:
        last_line = verdict.splitlines()[-1].strip().upper()
        approved = last_line == "APPROVED" or last_line.startswith("APPROVED")
    graph_log("out: verdict =", verdict)
    return {"approved": approved, "feedback": "" if approved else verdict}


def route(state: State) -> str:
    """Conditional edge after review: loop back or finish."""
    if state["approved"] or state["attempts"] >= MAX_ATTEMPTS:
        return END
    return "draft_reply"


graph = StateGraph(State)
graph.add_node("triage", triage)
graph.add_node("draft_reply", draft_reply)
graph.add_node("review", review)

graph.add_edge(START, "triage")
graph.add_edge("triage", "draft_reply")
graph.add_edge("draft_reply", "review")
graph.add_conditional_edges("review", route, ["draft_reply", END])

app = graph.compile()

# GRAPH_PNG = Path(__file__).resolve().parent / "output" / "loop_review.png"


def save_loop_graph_png() -> None:
    GRAPH_PNG.parent.mkdir(parents=True, exist_ok=True)
    GRAPH_PNG.write_bytes(app.get_graph().draw_mermaid_png())
    print("Saved graph:", GRAPH_PNG)


if __name__ == "__main__":
    # save_loop_graph_png()

    initial = {
        "ticket": TICKET,
        "triage": {},
        "reply": "",
        "feedback": "",
        "attempts": 0,
        "approved": False,
    }

    result = app.invoke(initial)

    print("\n══ Final ══")
    print("Triage:", json.dumps(result["triage"]))
    print("Attempts:", result["attempts"], "| Approved:", result["approved"])
    print("Reply:\n", result["reply"])

    # To watch the loop step by step instead (set LOG_GRAPH = True):
    # for step in app.stream(initial, stream_mode="updates"):
    #     graph_log("graph update:", step)
