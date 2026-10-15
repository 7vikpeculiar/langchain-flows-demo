"""Structured JSON slide 1 — why structured output matters.

Live contrast: the same ticket as free text vs. JSON.
"""

from common import SAMPLE_TICKET, banner, llm, show_json


FREE_TEXT_PROMPT = (
    "Read this support message and tell me what the customer wants:\n\n{ticket}"
)
JSON_PROMPT = (
    "Read this support message. Reply with JSON only, keys: "
    "customer, order_id, issue, request.\n\n{ticket}"
)


if __name__ == "__main__":
    banner("Why structured output  —  free text vs JSON")
    print("TICKET\n", SAMPLE_TICKET)

    model = llm()
    free = model.invoke(FREE_TEXT_PROMPT.format(ticket=SAMPLE_TICKET)).content
    json_text = model.invoke(JSON_PROMPT.format(ticket=SAMPLE_TICKET)).content

    print("\n--- FREE TEXT (hard for the next node to consume) ---\n")
    print(free)
    print("\n--- ASKED FOR JSON (parseable, but not guaranteed) ---\n")
    print(json_text)
    print(
        "\nPrompting for JSON is better than prose, but the model can still "
        "wrap it in markdown, miss a key, or invent a type. Next slide: a schema."
    )
    show_json("raw model string (not yet validated)", {"raw": json_text})
