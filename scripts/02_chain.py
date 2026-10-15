"""Step 2 — a chain: node A → node B.

Code slide for: the output of one node is the input of the next.
Adapted from Agentic-AI-Systems/02_frameworks/3_langgraph/code/basic_workflow.py
"""

from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from common import SAMPLE_TICKET, banner, llm


class ChainState(TypedDict):
    ticket: str
    key_points: str
    summary: str


researcher_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Extract 3 short bullet key points from the support ticket."),
        ("human", "{ticket}"),
    ]
)
summarizer_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "Turn these key points into one sentence a support lead can scan."),
        ("human", "{key_points}"),
    ]
)


def research(state: ChainState) -> dict:
    text = (researcher_prompt | llm()).invoke({"ticket": state["ticket"]}).content
    return {"key_points": text}


def summarize(state: ChainState) -> dict:
    text = (summarizer_prompt | llm()).invoke(
        {"key_points": state["key_points"]}
    ).content
    return {"summary": text}


def build_graph():
    graph = StateGraph(ChainState)
    graph.add_node("research", research)
    graph.add_node("summarize", summarize)
    graph.add_edge(START, "research")
    graph.add_edge("research", "summarize")  # the chain
    graph.add_edge("summarize", END)
    return graph.compile()


if __name__ == "__main__":
    banner("Step 2: Chain  (research → summarize)")
    print("ticket → researcher → summarizer → one-line brief\n")
    result = build_graph().invoke(
        {"ticket": SAMPLE_TICKET, "key_points": "", "summary": ""}
    )
    print("KEY POINTS\n", result["key_points"])
    print("\nSUMMARY\n", result["summary"])
