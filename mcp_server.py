from mcp.server.fastmcp import FastMCP
import requests
import os
import wikipedia
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("AgentX Tools")

@mcp.tool()
def get_weather(city: str) -> str:
    """Get current weather for any city"""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()
    if data.get('cod') != 200:
        return f"Weather not found for {city}"
    return f"Temperature: {data['main']['temp']}°C, Condition: {data['weather'][0]['description']}, Humidity: {data['main']['humidity']}%"

@mcp.tool()
def get_stock_price(symbol: str) -> str:
    """Get current stock price for any symbol"""
    stock = yf.Ticker(symbol)
    hist = stock.history(period="1d")
    price = hist['Close'].iloc[-1]
    return f"{symbol}: ${price:.2f}"

@mcp.tool()
def wikipedia_search(query: str) -> str:
    """Search Wikipedia for any topic"""
    try:
        return wikipedia.summary(query, sentences=3, auto_suggest=False)
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def calculator(expression: str) -> str:
    """Evaluate mathematical expressions"""
    import math
    allowed = {k: getattr(math, k) for k in dir(math) if not k.startswith('_')}
    allowed['abs'] = abs
    allowed['round'] = round
    result = eval(expression, {"__builtins__": {}}, allowed)
    return f"{expression} = {result}"

@mcp.tool()
def convert_currency(amount_and_currencies: str) -> str:
    """Convert currency. Format: '100 USD to INR'"""
    parts = amount_and_currencies.upper().split()
    amount = float(parts[0])
    from_curr = parts[1]
    to_curr = parts[3]
    url = f"https://api.exchangerate-api.com/v4/latest/{from_curr}"
    data = requests.get(url).json()
    rate = data['rates'].get(to_curr)
    return f"{amount} {from_curr} = {amount * rate:.2f} {to_curr}"

@mcp.tool()
def get_news(topic: str) -> str:
    """Get latest news about any topic"""
    api_key = os.getenv("NEWS_API_KEY")
    url = f"https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&pageSize=3&apiKey={api_key}"
    data = requests.get(url).json()
    articles = data.get('articles', [])
    result = ""
    for i, a in enumerate(articles[:3], 1):
        result += f"{i}. {a['title']} - {a['source']['name']}\n"
    return result

if __name__ == "__main__":
    mcp.run()