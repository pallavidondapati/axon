from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """Use this tool to evaluate any mathematical expression or calculation. 
    Input should be a valid math expression like '2+2', '15% of 5000', 'sqrt(144)'"""
    try:
        import math
        # allow safe math functions
        allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith('_')}
        allowed['abs'] = abs
        allowed['round'] = round
        result = eval(expression, {"__builtins__": {}}, allowed)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Could not calculate '{expression}': {str(e)}"