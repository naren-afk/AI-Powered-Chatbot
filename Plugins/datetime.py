import re
import subprocess
import os
from datetime import datetime, timedelta

# Function to process date, time, and day queries
def get_date_time(query):
    today = datetime.today()
    
    # Handling requests for the current date
   # Handling requests for today's date
    if "what's the date" in query or "today's date" in query or "date today" in query or "current date" in query or "tell me the date" in query:
        return today.strftime("%A, %B %d, %Y")

# Handling requests for the current time
    elif "what's the time" in query or "current time" in query or "time now" in query or "tell me the time" in query or "what is the time" in query or "what time is it" in query:
        return today.strftime("%I:%M %p")

# Handling requests for the current day
    elif "what day is it" in query or "today's day" in query or "what's the day" in query or "current day" in query or "which day is it today" in query or "what is today" in query:
        return today.strftime("%A")


    # Handling relative date queries (e.g., "what is the date next Saturday?")
    relative_dates = {
        "next monday": (today + timedelta(days=(0 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        "next tuesday": (today + timedelta(days=(1 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        "next wednesday": (today + timedelta(days=(2 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        "next thursday": (today + timedelta(days=(3 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        "next friday": (today + timedelta(days=(4 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        "next saturday": (today + timedelta(days=(5 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        "next sunday": (today + timedelta(days=(6 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        "tomorrow": (today + timedelta(days=1)).strftime("%A, %B %d, %Y"),
    }
    
    for pattern, date in relative_dates.items():
        if pattern in query.lower():
            return f"The date on {pattern.capitalize()} is {date}"

    # Handling queries like "What's the date 2 weeks from now?"
    match = re.search(r"what's the date (\d+) (day|week|month)s? from now", query, re.IGNORECASE)
    if match:
        num = int(match.group(1))
        unit = match.group(2)

        if unit == "day":
            future_date = today + timedelta(days=num)
        elif unit == "week":
            future_date = today + timedelta(weeks=num)
        elif unit == "month":
            future_date = today.replace(month=today.month + num if today.month + num <= 12 else (today.month + num) % 12)
        else:
            return "Sorry, I couldn't process that request."

        return f"The date {num} {unit}{'s' if num > 1 else ''} from now is {future_date.strftime('%A, %B %d, %Y')}."

    return "I'm not sure how to process that date-related request."

# Ensure the reminders folder exists
REMINDERS_DIR = "data/reminders"
os.makedirs(REMINDERS_DIR, exist_ok=True)

def get_next_reminder_filename():
    """Finds the next available reminder file name (reminder_1.bat, reminder_2.bat, etc.)."""
    existing_files = [f for f in os.listdir(REMINDERS_DIR) if f.startswith("reminder_") and f.endswith(".bat")]
    existing_numbers = sorted([int(f.split("_")[1].split(".")[0]) for f in existing_files if f.split("_")[1].split(".")[0].isdigit()])
    
    next_number = (existing_numbers[-1] + 1) if existing_numbers else 1
    return f"reminder_{next_number}.bat"

def parse_time_input(time_str):
    """Parses input time formats like '11 AM', '3:30 PM', 'in 2 hours', 'in 30 minutes'."""
    now = datetime.now()

    # Handling absolute times like "11 AM", "7:30 PM"
    match = re.match(r"(\d{1,2})(?::(\d{2}))?\s?(AM|PM)", time_str, re.IGNORECASE)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        am_pm = match.group(3).upper()

        if am_pm == "PM" and hour != 12:
            hour += 12
        if am_pm == "AM" and hour == 12:
            hour = 0  # Midnight case

        reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If the time has already passed today, reject it
        if reminder_time < now:
            return None, "The specified time has already passed today."

        return reminder_time, None

    # Handling relative times like "in 2 hours", "in 30 minutes"
    match = re.match(r"in\s+(\d+)\s+(second|minute|hour|seconds|minutes|hours)", time_str, re.IGNORECASE)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)

        if "second" in unit:
            reminder_time = now + timedelta(seconds=amount)
        elif "minute" in unit:
            reminder_time = now + timedelta(minutes=amount)
        elif "hour" in unit:
            reminder_time = now + timedelta(hours=amount)
        else:
            return None, "Invalid time format."

        return reminder_time, None

    return None, "Invalid time format. Please use formats like '11 AM', '7:30 PM', or 'in 2 hours'."

def set_reminder(task, time_str):
    """Sets a reminder at a given time."""
    reminder_time, error = parse_time_input(time_str)
    if error:
        return error

    reminder_time_str = reminder_time.strftime("%H:%M")

    # Get the next available reminder filename
    script_filename = get_next_reminder_filename()
    script_path = os.path.join(REMINDERS_DIR, script_filename)

    # Write the batch script to trigger a notification
    with open(script_path, "w") as file:
        file.write(f'@echo off\n')
        file.write(f'msg * "Reminder: {task}"\n')

    # Schedule the task using Windows Task Scheduler
    subprocess.run(
    f'schtasks /create /tn "Reminder_{script_filename}" /tr "{os.path.abspath(script_path)}" /sc once /st "{reminder_time_str}"',shell=True)
    return f"Reminder set for '{task}' at {reminder_time.strftime('%I:%M %p')}."

