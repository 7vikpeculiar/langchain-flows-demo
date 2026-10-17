def ChatGptModel(**kwargs):
    return "ollama:llama3.1:8b"


def ChatGptModel2():
    from agno.models.ollama import Ollama

    return Ollama(id="llama3.1:8b")
