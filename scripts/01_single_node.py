"""Step 1 — a graph with one node.

Code slide for: a node is a function that takes state and returns state.
Adapted from Agentic-AI-Systems/02_frameworks/3_langgraph/code/0_hello_world_graph.py
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from common import banner


class TicketState(TypedDict):
    message: str
    greeting: str


def greet(state: TicketState) -> TicketState:
    """One node: read state, write state. No branching yet."""
    inbound = state["message"]
    return {"message": inbound, "greeting": f"Got it. Working on: {inbound[:48]}..."}


def build_graph():
    graph = StateGraph(TicketState)
    graph.add_node("greet", greet)
    graph.add_edge(START, "greet")
    graph.add_edge("greet", END)
    return graph.compile()


if __name__ == "__main__":
    banner("Step 1: Single node")
    app = build_graph()
    result = app.invoke({"message": "Need a replacement keyboard for order 4821"})
    print("input :", result["message"])
    print("output:", result["greeting"])
