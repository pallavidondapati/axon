@tool
def generate_image(prompt: str) -> str:
    """Use this tool whenever user asks to generate, create, or draw any image or picture."""
    import urllib.parse
    import time
    time.sleep(2)  # avoid rate limit
    clean_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{clean_prompt}?seed={int(time.time())}"
    return f"\nIMAGE:{url}\n"