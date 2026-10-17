"""Step 3 — model chaining: triage, then draft a reply."""

from langchain.chat_models import init_chat_model

from common import ChatGptModel

TICKET = (
    "Hi, this is Sathvik from Acme. Order #4821 arrived yesterday but the "
    "keyboard is missing two keys. Can I get a replacement shipped to "
    "91 Market Street by Friday? Thanks."
)

model = init_chat_model(ChatGptModel())

triage = model.invoke(
    f"Customer ticket:\n{TICKET}\n\n"
    "Reply with one line: category (billing/shipping/defect/other) and priority (low/medium/high)."
)
print("Triage:", triage.content)

reply = model.invoke(
    f"Customer ticket:\n{TICKET}\n\n"
    f"Triage:\n{triage.content}\n\n"
    "Draft a short, friendly support email. Mention the order number"
)
print("Reply:", reply.content)
