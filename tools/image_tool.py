from langchain_core.tools import tool
import requests
import os

@tool
def generate_image(prompt: str) -> str:
    """Use this tool whenever user asks to generate, create, or draw any image or picture."""
    import requests, os
    response = requests.post(
        "https://clipdrop-api.co/text-to-image/v1",
        files={"prompt": (None, prompt, "text/plain")},
        headers={"x-api-key": os.getenv("CLIPDROP_API_KEY")}
    )
    if response.ok:
        with open("generated_image.png", "wb") as f:
            f.write(response.content)
        return "IMAGE_FILE:generated_image.png"
    return f"Failed: {response.text}"