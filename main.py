import os
import sys
import logging
import pyttsx3
import speech_recognition as sr
import ollama  # Using LLaMA 3.2 for AI responses


from Plugins.datetime import *
from Plugins.database import get_latest_session_id,store_chat_buffered,create_new_session
from Plugins.gmail import compose_and_send_email
from Plugins.API_functionalities import *
from Plugins.system_operations import *
from Plugins.browsing_functionalities import youtube,googleSearch,get_map,open_specified_website


# Initialize session memory
session_memory = []


# Initialize text-to-speech (TTS)
engine = pyttsx3.init()
engine.setProperty('rate', 185)

def speak(text):
    """Speaks the given text and ensures the loop stops after execution."""
    print("AI:", text)
    try:
        engine.say(text)
        engine.runAndWait()  # Speak the text
        engine.stop()  # Ensure the engine stops after speaking
    except RuntimeError as e:
        if "run loop already started" in str(e):
            pass  # Ignore loop error
        else:
            print(f"Error in speak(): {e}")  # Logs other errors


def listen_audio():
    recognizer = sr.Recognizer()
    with sr.Microphone() as mic:
        recognizer.adjust_for_ambient_noise(mic)
        print("Listening for input... (say something)")
        try:
            audio = recognizer.listen(mic, timeout=5)  # Add timeout
            print("Audio captured, processing...")
            query = recognizer.recognize_google(audio).lower()
            print("User said:", query)
            return query
        except sr.UnknownValueError:
            print("DEBUG: Couldn't recognize speech.")
            speak("Sorry, I couldn't understand.")
            return None
        except sr.RequestError:
            print("DEBUG: Speech recognition service is down.")
            speak("Speech service is unavailable.")
            return None
        except sr.WaitTimeoutError:
            print("DEBUG: No input detected.")
            return None  # Avoids infinite waiting

def stream_ai_response(query):
    """Streams AI-generated response in real-time using local LLaMA 3.2 model"""
    response_stream = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": query}], stream=True)
    
    ai_response = ""
    for chunk in response_stream:
        text_part = chunk['message']['content']
        ai_response += text_part

    print("\n")  # Ensure a newline after response
    speak(ai_response)
    return(ai_response)

def process_user_input(user_input):
    ai_response = stream_ai_response(user_input)  # AI's response logic
    store_chat_buffered(user_input, ai_response)  # Log the chat
    speak(ai_response)  # Optional TTS response
    return ai_response  # Send response back to frontend

def main(query):
    """Process user query and execute appropriate actions."""
    if query:
        if "exit" in query:
            speak("Goodbye!")
            return "exit"
        elif "search" in query or "google" in query:
            speak("Searching on Google...")
            return googleSearch(query)
        elif "youtube" in query:
            speak("Searching on YouTube...")
            return youtube(query)
        elif "send an email" in query:
            speak("Composing an email...")
            return compose_and_send_email(query)
        elif "open" in query or "launch" in query:
            speak("Opening application...")
            return open_app(query)
        elif "distance" in query or "map" in query:
            get_map(query)
            return
        elif "news" in query:
            news = get_news()
            if news:
                speak(news)
                done = True
        elif "weather" in query:
            speak("Fetching latest updates...")
            city_match = re.search(r"(?:in|of|for) ([a-zA-Z\s]+)", query)
            city = city_match[1].strip() if city_match else None
            weather = get_weather(city) if city else get_weather()
            speak(weather if weather else "Sorry, I couldn't fetch the weather at this time.")
            return weather
        elif "solve" in query or "convert" in query:
            speak("Solving your request...")
            return solve_math_or_convert_units(query)
        elif "set a reminder" in query or "remind me" in query:
            speak("Setting a reminder...")
            return set_reminder(query)
        elif "what's the date" in query or "what's the time" in query or "what day is it" in query:
            return get_date_time(query)
        elif "system info" in query:
            speak("Fetching system information...")
            return systemInfo()
        elif "system stats" in query:
            speak("Fetching system stats...")
            return system_stats()
        elif "screenshot" in query:
            speak("Taking a screenshot...")
            return WindowOpt().Screen_Shot()
        elif "take a note" in query:
            speak("Taking a note...")
            return take_note(query)
        elif "generate text" in query:
            speak("Generating content...")
            return generate_text(query)
        elif "generate and save" in query:
            speak("Generating and saving the note...")
            return generate_and_save_note(query)
        elif "open" in query or "launch" in query:
            speak("Opening application or website...")
            result = open_app(query) or open_specified_website(query)
            return result

        else:
            response = stream_ai_response(query)
        speak(response)
        return response
    
if __name__ == "__main__":
    while True:
        query = listen_audio()
        if query == "exit":
            break
        main(query)