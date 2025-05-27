import webbrowser
import re
import speedtest
from Plugins import websites
import yt_dlp

def googleSearch(query):
    query = query.lower()
    is_image_search = 'image' in query or 'images' in query
    query = re.sub(r'\b(images?|search|show|google|for|on chrome)\b', '', query, flags=re.IGNORECASE).strip()
    url = f"https://www.google.com/search?q={query}"
    if is_image_search:
        url += "&tbm=isch"
    webbrowser.open(url)
    return "Here you go..."

def youtube(query):
    """Search for a YouTube video and play the first result."""
    query = re.sub(r'\b(play|on youtube|youtube)\b', '', query, flags=re.IGNORECASE).strip()
    
    if not query:
        return "What would you like to search for on YouTube?"

    search_query = f"ytsearch:{query}"  # Search YouTube
    ydl_opts = {"quiet": True, "extract_flat": True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            if "entries" in info and info["entries"]:
                video_url = info["entries"][0]["url"]
                webbrowser.open(video_url)  # Open in browser
                return f"Playing '{info['entries'][0]['title']}' on YouTube..."
            else:
                return "No results found."
    except Exception as e:
        return f"Error: {str(e)}"

def open_specified_website(query):
    website = query.replace("open ", "").strip()
    if website in websites.websites_dict:
        url = websites.websites_dict[website]
        webbrowser.open(url)
        return f"Opening {website}..."
    else:
        webbrowser.open(f"https://www.google.com/search?q={website}")
        return f"Couldn't find {website} in saved websites. Searching on Google instead..."

def get_speedtest():
    try:
        internet = speedtest.Speedtest()
        speed = f"Your network's Download Speed is {round(internet.download() / 8388608, 2)}MBps\n" \
               f"Your network's Upload Speed is {round(internet.upload() / 8388608, 2)}MBps"
        return speed
    except (speedtest.SpeedtestException, KeyboardInterrupt):
        return "Speed test failed."

def get_map(query):
    query = query.replace("show me a map of", "").strip()
    webbrowser.open(f'https://www.google.com/maps/search/{query}')
    return f"Showing map for {query}..."

def search_amazon(query):
    query = query.replace("search amazon for", "").strip()
    webbrowser.open(f"https://www.amazon.com/s?k={query}")
    return f"Searching for {query} on Amazon..."

def search_wikipedia(query):
    try:
        topic = query.replace("search wikipedia for", "").strip()
        from wikipedia import summary, exceptions
        result = summary(topic, sentences=2)
        return result
    except exceptions.DisambiguationError:
        return f"There are multiple results for {topic}. Please be more specific."
    except exceptions.PageError:
        return "No information found on Wikipedia."

def search_stackoverflow(query):
    query = query.replace("search stackoverflow for", "").strip()
    webbrowser.open(f"https://stackoverflow.com/search?q={query}")
    return f"Searching for {query} on Stack Overflow..."
