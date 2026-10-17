"""Step 2 — define a tool and bind it to the model."""

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.messages import ToolMessage

from common import ChatGptModel


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    return a * b


tools = [multiply]
tools_by_name = {t.name: t for t in tools}

question = "What is 6 times 7?"
model = init_chat_model(ChatGptModel()).bind_tools(tools)

response = model.invoke(question)
print("Calls are:", response.tool_calls)

for call in response.tool_calls:
    tool_fn = tools_by_name[call["name"]]
    result = tool_fn.invoke(call["args"])
    response = model.invoke(
        [
            ("human", question),
            response,
            ToolMessage(content=str(result), tool_call_id=call["id"]),
        ]
    )

print("Answer is:", response.content)
