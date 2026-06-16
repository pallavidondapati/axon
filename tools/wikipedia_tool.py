from langchain_core.tools import tool
import wikipedia
@tool
def wikipedia_search(query: str) -> str:
    """Search Wikipedia for information about any topic, person, place, or concept."""
    try:
        result = wikipedia.summary(query, sentences=3, auto_suggest=False)
        return result
    except wikipedia.DisambiguationError as e:
        return f"Be more specific. Options: {str(e.options[:3])}"
    except wikipedia.PageError:
        return f"No Wikipedia page found for '{query}'"
    except Exception as e:
        return f"Error: {str(e)}"