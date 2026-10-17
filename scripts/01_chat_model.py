"""Step 1 — call a chat model."""

from langchain.chat_models import init_chat_model
from common import ChatGptModel

model = init_chat_model(ChatGptModel())
response = model.invoke("Why do parrots have colorful feathers? Explain in a few sentences.")
print(response.content)
