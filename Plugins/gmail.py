import smtplib
import os
import re
import sqlite3
from dotenv import load_dotenv
import ollama
from datetime import datetime, timedelta

# Load environment variables
env_path = os.path.abspath("../Data/.env")  # Ensure correct path
load_dotenv(env_path)

EMAIL = os.getenv("narenkumars22mss025@skasc.ac.in")
PASSWORD = os.getenv("qomj xord bljz mecd")

# Define database path (same as database.py)
db_path = "C:/Users/Naren kumar/Desktop/Final project/Data/chats.db"

# Ensure database exists and contains emails table
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS emails (name TEXT PRIMARY KEY, email TEXT)")
conn.commit()
conn.close()
print("Database check completed.")

def get_email_from_db(name):
    """Retrieve email from the database, ignoring case differences."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM emails WHERE LOWER(name) = LOWER(?)", (name,))
        result = cursor.fetchone()
        return result[0] if result else None

def save_email_to_db(name, email):
    """Save a new email to the database if it does not already exist."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO emails (name, email) VALUES (?, ?)", (name, email))
        conn.commit()

def detect_and_format_dates(context):
    """Detect relative date expressions and replace them with actual dates."""
    today = datetime.today()
    date_patterns = {
        r"\bnext\s+saturday\b": (today + timedelta(days=(5 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        r"\bnext\s+sunday\b": (today + timedelta(days=(6 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        r"\btomorrow\b": (today + timedelta(days=1)).strftime("%A, %B %d, %Y"),
        r"\bnext\s+monday\b": (today + timedelta(days=(0 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        r"\bnext\s+tuesday\b": (today + timedelta(days=(1 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        r"\bnext\s+wednesday\b": (today + timedelta(days=(2 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        r"\bnext\s+thursday\b": (today + timedelta(days=(3 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
        r"\bnext\s+friday\b": (today + timedelta(days=(4 - today.weekday()) % 7 + 7)).strftime("%A, %B %d, %Y"),
    }
    
    for pattern, date in date_patterns.items():
        context = re.sub(pattern, date, context, flags=re.IGNORECASE)
    
    return context

def generate_email(subject, context, tone="formal"):
    """Generate email content using AI (LLaMA) based on extracted details."""
    context = detect_and_format_dates(context)
    if not subject:
        subject = f"Regarding {context[:30]}..."  
    prompt = f"Write a {tone} email with the subject '{subject}' and context: {context}"
    response = ollama.chat(model='llama3.2', messages=[{"role": "user", "content": prompt}])
    return subject, response['message']['content']

def send_email(receiver_id, subject, body):
    """Send an email via SMTP."""
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    try:
        s.login(EMAIL, PASSWORD)
        message = "\r\n".join([
            f"From: {EMAIL}",
            f"To: {receiver_id}",
            f"Subject: {subject}",
            "",
            f"{body}"
        ])
        s.sendmail(EMAIL, receiver_id, message)
    except smtplib.SMTPRecipientsRefused:
        print(f"Error: Invalid recipient email: {receiver_id}")
        return False
    except smtplib.SMTPAuthenticationError:
        print("Error: SMTP authentication failed. Check your email/password or enable 'Less Secure Apps' in Gmail settings.")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
        return False
    finally:
        s.quit()
    return True

def check_email(email):
    """Validate email format."""
    verifier = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return bool(re.fullmatch(verifier, email))

def compose_and_send_email(command):
    """Extract recipient, subject, and context from user command."""
    match = re.search(r"email to (\w+) (.+)", command, re.IGNORECASE)
    
    if not match:
        print("Could not identify recipient or message context.")
        return False

    recipient_name, context = match.groups()
    recipient_name = recipient_name.capitalize()
    receiver_id = get_email_from_db(recipient_name)

    if not receiver_id:
        receiver_id = input(f"Enter email for {recipient_name}: ").strip()
        if not check_email(receiver_id):
            print("Invalid email format.")
            return False
        save_email_to_db(recipient_name, receiver_id)

    # Generate subject dynamically
    subject = f"Regarding {context[:30]}..."

    # Generate email content
    subject, draft = generate_email(subject, context)

    # Ask for review
    confirmation = input(f"Do you want to review the email before sending? (yes/no): ").strip().lower()
    if confirmation == "yes":
        print("\nGenerated Email:\n", draft)
        edit_confirmation = input("Do you want to edit the email? (yes/no): ").strip().lower()
        if edit_confirmation == "yes":
            print("Edit your email below:")
            draft = input()
    
    return send_email(receiver_id, subject, draft)
