from langchain_core.tools import tool

@tool
def debug_code(code: str) -> str:
    """Analyze, debug, fix, and explain code. Use this tool when user asks to:
    - debug or fix code
    - explain what code does
    - find errors or bugs in code
    - improve or optimize code
    - review code quality
    Input should be the code snippet to analyze."""
    return f"ANALYZE THIS CODE:\n{code}"