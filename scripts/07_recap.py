"""Recap — node → chain → structured output → loop, in one graph.

Same support-ticket story as the earlier slides, composed.
"""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from common import SAMPLE_TICKET, banner, llm, show_json

MAX_TURNS = 2


class Ticket(BaseModel):
    order_id: str
    request: Literal["replace", "refund", "info", "other"]
    summary: str


class RecapState(TypedDict):
    raw: str
    ticket: dict
    draft: str
    status: str
    turn: int


class Verdict(BaseModel):
    status: Literal["PASS", "REVISE"]
    feedback: str = Field(default="")


def extract(state: RecapState) -> dict:
    """Single node + structured output."""
    ticket = llm().with_structured_output(Ticket).invoke(state["raw"])
    show_json("1. node extract", ticket)
    return {"ticket": ticket.model_dump()}


def draft(state: RecapState) -> dict:
    """Chain step: structured ticket → reply."""
    t = state["ticket"]
    text = llm().invoke(
        f"Write one sentence confirming a {t['request']} for order {t['order_id']}."
    ).content
    print(f"\n2. chain draft:\n{text}")
    return {"draft": text, "turn": state.get("turn", 0) + 1}


def critique(state: RecapState) -> dict:
    """Loop step: structured verdict."""
    v: Verdict = llm().with_structured_output(Verdict).invoke(
        "PASS if the draft names the order id, else REVISE.\n"
        f"Draft: {state['draft']}\nTicket: {state['ticket']}"
    )
    show_json("3. loop critique", v)
    return {"status": v.status}


def route(state: RecapState) -> Literal["draft", "done"]:
    if state["status"] == "PASS" or state["turn"] >= MAX_TURNS:
        return "done"
    return "draft"


def build_graph():
    g = StateGraph(RecapState)
    g.add_node("extract", extract)
    g.add_node("draft", draft)
    g.add_node("critique", critique)
    g.add_edge(START, "extract")
    g.add_edge("extract", "draft")
    g.add_edge("draft", "critique")
    g.add_conditional_edges("critique", route, {"draft": "draft", "done": END})
    return g.compile()


if __name__ == "__main__":
    banner("Recap: node → chain → structured output → loop")
    result = build_graph().invoke(
        {"raw": SAMPLE_TICKET, "draft": "", "status": "", "turn": 0}
    )
    print("\nDONE  status=", result["status"], "  draft=", result["draft"])
