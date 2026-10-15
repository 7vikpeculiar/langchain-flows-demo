"""Structured JSON slide 3 — JSON between nodes, and as tool arguments.

Extract a typed ticket; the next node indexes fields (no prose parsing).
A separate call shows the same fields as schema-valid tool arguments.

Adapted from:
  Agentic-AI-Systems/03_system_design/RAGs/code/07_agentic_rag.py
  Agentic-AI-Systems/02_frameworks/3_langgraph/code/advanced_workflow.py
"""

from typing import Literal, Optional, TypedDict

from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from common import SAMPLE_TICKET, banner, llm, show_json


class SupportTicket(BaseModel):
    customer_name: str
    order_id: str
    request: Literal["replace", "refund", "info", "other"]
    city: Optional[str] = None


class GraphState(TypedDict, total=False):
    raw: str
    ticket: dict
    warehouse: str
    reply: str


@tool
def lookup_order(order_id: str) -> str:
    """Look up warehouse status for an order id."""
    catalog = {
        "4821": "Order 4821: keyboard, shipped, 1 of 2 items delivered.",
        "1001": "Order 1001: laptop stand, in transit.",
    }
    return catalog.get(order_id, f"Order {order_id}: not found.")


def extract(state: GraphState) -> dict:
    """Node 1: LLM → Pydantic. Downstream nodes never parse prose."""
    ticket = llm().with_structured_output(SupportTicket).invoke(
        f"Extract fields from this message:\n{state['raw']}"
    )
    show_json("node extract → SupportTicket (contract for the next node)", ticket)
    return {"ticket": ticket.model_dump()}


def fulfill(state: GraphState) -> dict:
    """Node 2: consume JSON fields, not the original email."""
    order_id = state["ticket"]["order_id"]
    warehouse = lookup_order.invoke({"order_id": order_id})
    print(f"\nnode fulfill indexed ticket['order_id']={order_id!r}")
    print("warehouse:", warehouse)
    return {"warehouse": warehouse}


def reply(state: GraphState) -> dict:
    t = state["ticket"]
    text = llm().invoke(
        f"One sentence: {t['customer_name']} asked to {t['request']} "
        f"order {t['order_id']}. Warehouse says: {state['warehouse']}"
    ).content
    return {"reply": text}


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("extract", extract)
    graph.add_node("fulfill", fulfill)
    graph.add_node("reply", reply)
    graph.add_edge(START, "extract")
    graph.add_edge("extract", "fulfill")
    graph.add_edge("fulfill", "reply")
    graph.add_edge("reply", END)
    return graph.compile()


def demo_tool_schema() -> None:
    """Same order_id, now as a tool-call argument the model must fill."""
    banner("Same schema on a tool call")
    model = llm().bind_tools([lookup_order])
    msg = model.invoke(
        "Look up warehouse status for order 4821. You must call lookup_order."
    )
    print("tool_calls:")
    show_json("model.tool_calls", msg.tool_calls or [])


if __name__ == "__main__":
    banner("Structured output between nodes")
    result = build_graph().invoke({"raw": SAMPLE_TICKET})
    print("\nfinal reply:\n", result["reply"])
    demo_tool_schema()
