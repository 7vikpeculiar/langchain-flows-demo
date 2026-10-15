"""Step 3 — a loop: generate → evaluate → generate until PASS (or max turns).

Adapted from Agentic-AI-Systems/03_system_design/design-patterns/code/evaluator_optimizer.ipynb
rewritten as a LangGraph conditional edge.
"""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from common import SAMPLE_TICKET, banner, llm, show_json

MAX_TURNS = 3


class DraftState(TypedDict):
    ticket: str
    draft: str
    feedback: str
    turn: int
    status: str


class Verdict(BaseModel):
    status: Literal["PASS", "REVISE"]
    feedback: str = Field(description="What to change if REVISE; empty if PASS")


def generate(state: DraftState) -> dict:
    extra = f"\nPrevious feedback: {state['feedback']}" if state["feedback"] else ""
    draft = llm().invoke(
        "Write a 2-sentence support reply. Mention the order id if present. "
        "Do not promise a refund unless the customer asked for one.\n\n"
        f"Ticket:\n{state['ticket']}{extra}"
    ).content
    turn = state.get("turn", 0) + 1
    print(f"\n--- generate (turn {turn}) ---\n{draft}")
    return {"draft": draft, "turn": turn}


def evaluate(state: DraftState) -> dict:
    verdict: Verdict = llm().with_structured_output(Verdict).invoke(
        "Grade the reply. PASS only if it is two sentences, names the order, "
        "and does not invent a policy.\n\n"
        f"Ticket: {state['ticket']}\nReply: {state['draft']}"
    )
    show_json("evaluate", verdict)
    return {"status": verdict.status, "feedback": verdict.feedback}


def should_continue(state: DraftState) -> Literal["generate", "done"]:
    if state["status"] == "PASS" or state["turn"] >= MAX_TURNS:
        return "done"
    return "generate"


def build_graph():
    graph = StateGraph(DraftState)
    graph.add_node("generate", generate)
    graph.add_node("evaluate", evaluate)
    graph.add_edge(START, "generate")
    graph.add_edge("generate", "evaluate")
    graph.add_conditional_edges(
        "evaluate",
        should_continue,
        {"generate": "generate", "done": END},
    )
    return graph.compile()


if __name__ == "__main__":
    banner("Step 3: Loop  (generate ⇄ evaluate)")
    print("generate → evaluate → (REVISE? loop : stop)\n")
    result = build_graph().invoke(
        {
            "ticket": SAMPLE_TICKET,
            "draft": "",
            "feedback": "",
            "turn": 0,
            "status": "",
        }
    )
    print("\nFINAL STATUS:", result["status"], f"(turns={result['turn']})")
    print("FINAL DRAFT:\n", result["draft"])
