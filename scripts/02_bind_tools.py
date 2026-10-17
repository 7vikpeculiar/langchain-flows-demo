"""Step 2 — define a tool and bind it to the model."""

# How models with tools work: bind_tools → tool_calls, then create_agent runs them for you.

# from langchain.agents import create_agent
# from langchain.chat_models import init_chat_model
# from langchain.tools import tool

# from common import ChatGptModel


# @tool
# def multiply(a: int, b: int) -> int:
#     """Multiply two integers."""
#     return a * b


# question = "What is 6 times 7?"

# model = init_chat_model(ChatGptModel()).bind_tools([multiply])
# response = model.invoke(question)
# print("Calls are:", response.tool_calls)
# print("Content is:", response.content)

# agent = create_agent(init_chat_model(ChatGptModel()), tools=[multiply])
# result = agent.invoke({"messages": [("human", question)]})
# print("Answer is:", result["messages"][-1].content)


# # --- Uncomment below:

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool

from common import ChatGptModel

QUESTION = "What is 6 - 7?"
BAD_AT_MATH = [
    ("system", "You are bad at arithmetic. Always guess wrong for multiplication. Just give the wrong answer."),
    ("human", QUESTION),
]


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers."""
    return a * b

@tool
def subtract(a: int, b: int) -> int:
    """Multiply two integers."""
    return a * b


# bad_model = init_chat_model(ChatGptModel())
# print("Without tools:", bad_model.invoke(BAD_AT_MATH).content)

agent = create_agent(init_chat_model(ChatGptModel()), tools=[multiply, subtract])
result = agent.invoke({"messages": BAD_AT_MATH})
print("Agent with tools:", result["messages"][-1].content, result)
