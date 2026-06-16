from langchain_core.tools import tool
import requests
import os

@tool
def get_news(topic: str) -> str:
    """Get latest news articles about any topic, person, company, or event."""
    try:
        api_key = os.getenv("NEWS_API_KEY")
        url = f"https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&pageSize=5&apiKey={api_key}"
        response = requests.get(url)
        data = response.json()
        if data.get('status') != 'ok':
            return f"Could not fetch news for {topic}"
        articles = data.get('articles', [])
        if not articles:
            return f"No news found for {topic}"
        result = f"Latest news about {topic}:\n\n"
        for i, article in enumerate(articles[:5], 1):
            result += f"{i}. {article['title']}\n"
            result += f"   Source: {article['source']['name']}\n"
            result += f"   {article['description']}\n\n"
        return result
    except Exception as e:
        return f"Error fetching news: {str(e)}"
    