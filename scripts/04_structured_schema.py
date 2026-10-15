"""Structured JSON slide 2 — define a schema, get validated JSON.

Adapted from:
  Agentic-AI-Systems/02_frameworks/1_openai/code/09_outputs/models.py
  Agentic-AI-Systems/03_system_design/RAGs/code/07_agentic_rag.py (with_structured_output)
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

from common import SAMPLE_TICKET, banner, llm, show_json


class Person(BaseModel):
    name: str
    company: Optional[str] = None


class SupportTicket(BaseModel):
    """What the next node (and any tool) is allowed to see."""

    customer: Person
    order_id: str = Field(description="Order identifier, e.g. 4821")
    issue: str
    request: Literal["replace", "refund", "info", "other"]
    deadline: Optional[str] = Field(default=None, description="Customer-stated deadline")


if __name__ == "__main__":
    banner("Schema: Pydantic model → guaranteed JSON")
    ticket: SupportTicket = llm().with_structured_output(SupportTicket).invoke(
        f"Extract a support ticket from:\n\n{SAMPLE_TICKET}"
    )
    print("Python object :", type(ticket).__name__)
    print("typed fields  :", ticket.request, ticket.order_id)
    show_json("resulting JSON", ticket)
    print("\nJSON schema the model is constrained to:")
    show_json("schema", SupportTicket.model_json_schema())
