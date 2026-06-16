from langchain_core.tools import tool
import requests
import os
@tool
def get_weather(city: str) -> str:
    """Get current weather for any city."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()
    if data.get('cod') != 200:
        # try without country
        url2 = f"http://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={api_key}&units=metric"
        response = requests.get(url2)
        data = response.json()
    if data.get('cod') != 200:
        return f"Weather not found for {city}. Try a nearby major city like Visakhapatnam or Hyderabad."
    return f"""
    City: {data['name']}, {data['sys']['country']}
    Temperature: {data['main']['temp']}°C
    Feels like: {data['main']['feels_like']}°C
    Condition: {data['weather'][0]['description']}
    Humidity: {data['main']['humidity']}%
    Wind: {data['wind']['speed']} m/s
    """