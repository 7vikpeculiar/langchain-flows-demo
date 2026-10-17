"""Step 3 — same chain as 03_model_chaining_inefficient.py, as a LangGraph.

    START ──▶ triage ──▶ reply ──▶ END
"""

from typing import TypedDict

from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph

from common import ChatGptModel

LOG_GRAPH = True  # True → per-node trace while the graph runs


def graph_log(*args, **kwargs) -> None:
    if LOG_GRAPH:
        print(*args, **kwargs)


TICKET = (
    "Hi, this is Sathvik from Acme. Order #4821 arrived yesterday but the "
    "keyboard is missing two keys. Can I get a replacement shipped to "
    "91 Market Street by Friday? Thanks."
)
TICKET2 = ("Also, the payment for order #3411 is not refunded yet. Can you check?")

model = init_chat_model(ChatGptModel())


class State(TypedDict):
    ticket: str
    triage: str
    reply: str


def triage(state: State) -> dict:
    graph_log("\n── node: triage ──")
    graph_log("in : ticket =", state["ticket"][:60], "...")
    response = model.invoke(
        f"Customer ticket:\n{state['ticket']}\n\n"
        "Reply with one line: category (billing/shipping/defect/other) "
        "and priority (low/medium/high)."
    )
    graph_log("out: triage =", response.content)
    return {"triage": response.content}


def draft_reply(state: State) -> dict:
    graph_log("\n── node: reply ──")
    graph_log("in : triage =", state["triage"])
    response = model.invoke(
        f"Customer ticket:\n{state['ticket']}\n\n"
        f"Triage:\n{state['triage']}\n\n"
        "Draft a short, friendly support email. Mention the order number."
    )
    graph_log("out: reply =", response.content[:80], "...")
    return {"reply": response.content}


graph = StateGraph(State)
graph.add_node("triage", triage)
graph.add_node("reply", draft_reply)
graph.add_edge(START, "triage")
graph.add_edge("triage", "reply")
graph.add_edge("reply", END)
app = graph.compile()

if __name__ == "__main__":
    initial = {"ticket": TICKET, "triage": "", "reply": ""}

    result = app.invoke(initial)
    graph_log("\nTriage:", result["triage"])
    print("Reply:", result["reply"], result)

    # stream — same graph; one update dict per node (set LOG_GRAPH = True)
    graph_log("\nRunning graph (each step = one node)...\n")
    for step in app.stream(initial, stream_mode="updates"):
        graph_log("graph update:", step)
