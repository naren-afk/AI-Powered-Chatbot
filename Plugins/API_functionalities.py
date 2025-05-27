import os
import datetime
from dotenv import load_dotenv
from newsapi import NewsApiClient
import re
import requests
from wolframalpha import Client

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '..', 'Data', '.env')
load_dotenv(env_path)

# API Keys
NEWS = os.getenv('NEWS_API')
WOLFRAMALPHA = os.getenv('WOLFRAMALPHA_API')
OPENWEATHERMAP = os.getenv('OPENWEATHERMAP_API')

# Initialize News API
news = NewsApiClient(api_key=NEWS)

# Initialize Wolfram Alpha Client
wolfram_client = Client(WOLFRAMALPHA)

def get_ip(_return=False):
    """Fetch public IP address and location details."""
    try:
        response = requests.get('http://ip-api.com/json/').json()
        result = f'Your IP address is {response["query"]}'
        print(result)
        return response if _return else result
    except KeyboardInterrupt:
        return None
    except requests.exceptions.RequestException:
        return None

def get_joke():
    """Fetch a random joke from JokeAPI."""
    try:
        joke = requests.get('https://v2.jokeapi.dev/joke/Any?format=txt').text
        print(f"Joke: {joke}")
        return joke
    except KeyboardInterrupt:
        return None
    except requests.exceptions.RequestException:
        return None

def get_news():
    """Fetch top 10 news headlines."""
    try:
        top_news = ""
        top_headlines = news.get_top_headlines(language="en", country="in")
        for i in range(10):
            headline = re.sub(r'[|-] [A-Za-z0-9 |:.]*', '', top_headlines['articles'][i]['title']).replace("’", "'")
            top_news += headline + '\n'
        
        print("\nTop News Headlines:\n" + top_news)
        return top_news
    except KeyboardInterrupt:
        return None
    except requests.exceptions.RequestException:
        return None

def get_weather(city=''):
    """Fetch current weather for a given city or user's location."""
    try:
        if city:
            print(f"Fetching weather for city: {city}")
            response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHERMAP}&units=metric').json()
        else:
            ip_location = get_ip(True)
            print(f"Fetching weather for IP location: {ip_location['city']}")
            response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={ip_location["city"]}&appid={OPENWEATHERMAP}&units=metric').json()

        # Check if city is found in the API response
        if response.get("cod") != 200:
            return f"Sorry, I couldn't find weather data for {city}."

        weather = f'It\'s {response["main"]["temp"]}° Celsius and {response["weather"][0]["main"]}\n'\
                  f'Feels like {response["main"]["feels_like"]}° Celsius\n'\
                  f'Wind is blowing at {round(response["wind"]["speed"] * 3.6, 2)} km/h\n'\
                  f'Visibility is {int(response["visibility"] / 1000)} km'
        return weather

    except requests.exceptions.RequestException:
        return "Sorry, I couldn't connect to the weather service."
    except KeyboardInterrupt:
        return None


def get_general_response(query):
    """Fetch response from Wolfram Alpha."""
    try:
        response = wolfram_client.query(query)
        result = next(response.results).text
        print(f"\nWolfram Alpha Response: {result}")
        return result
    except (StopIteration, AttributeError):
        print("\nNo result found on Wolfram Alpha.")
        return None
    except KeyboardInterrupt:
        return None

def solve_math_or_convert_units(query):
    """Solve mathematical expressions or convert units using Wolfram Alpha."""
    try:
        response = wolfram_client.query(query)
        result = next(response.results).text
        print(f"\nWolfram Alpha Response: {result}")
        return result
    except (StopIteration, AttributeError):
        print("\nNo result found on Wolfram Alpha.")
        return "I couldn't solve that. Please try rephrasing."
    except Exception as e:
        print(f"Error: {e}")
        return "There was an error processing your request."
