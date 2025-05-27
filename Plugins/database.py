import atexit
import sqlite3
import os
from datetime import datetime, timedelta

# Define database path
db_path = "DB_PATH"

# Ensure database directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Connect to SQLite database (Persistent Connection)
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

# Create tables if they don't exist
cursor.executescript('''
    CREATE TABLE IF NOT EXISTS sessions (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        user_input TEXT,
        ai_response TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    );

    CREATE TABLE IF NOT EXISTS emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE
    );

    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reminder_text TEXT,
        reminder_time DATETIME
    );
''')
conn.commit()
print("Database initialized at:", os.path.abspath(db_path))

# Function to create a new session
def create_new_session():
    """Creates a new session and returns its ID."""
    cursor.execute("INSERT INTO sessions (start_time) VALUES (datetime('now'))")
    conn.commit()

    cursor.execute("SELECT last_insert_rowid()")
    session_id = cursor.fetchone()[0]

    print(f"New session created with ID: {session_id}")
    return session_id
# Function to get or create a daily session
def get_or_create_daily_session():
    """Ensures only one session per day."""
    today_date = datetime.now().date()

    # Fetch the latest session ID and its date
    cursor.execute("SELECT session_id, DATE(start_time) FROM sessions ORDER BY start_time DESC LIMIT 1")
    last_session = cursor.fetchone()

    if last_session and last_session[1] == str(today_date):
        print(f"Using existing session ID: {last_session[0]}")
        return last_session[0]  # Use today's existing session

    # If no session for today, create a new one
    return create_new_session()
# Function to get latest session or create a new one
def get_latest_session_id():
    """Returns the latest session ID or creates a new one if none exists."""
    cursor.execute("SELECT session_id FROM sessions ORDER BY start_time DESC LIMIT 1")
    session = cursor.fetchone()
    
    if session:
        return session[0]

    return create_new_session()

# 🛠 **Chat Buffer (Stores chats until shutdown)**
chat_buffer = []

def store_chat_buffered(user_input, ai_response):
    """Buffer chat messages without writing to the database immediately."""
    session_id = get_latest_session_id()
    chat_buffer.append((session_id, user_input, ai_response, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    print(f"Chat buffered for session {session_id} (Total Buffered: {len(chat_buffer)})")

def commit_chat_buffer():
    """Saves all buffered chat messages to the database when the server shuts down."""
    global chat_buffer  # Ensure buffer is accessed globally

    if not chat_buffer:
        print("No buffered chats to save. Skipping database commit.")
        return

    print(f"Committing {len(chat_buffer)} buffered chats to the database...")

    cursor.executemany(
        "INSERT INTO chat_history (session_id, user_input, ai_response, timestamp) VALUES (?, ?, ?, ?)",
        chat_buffer
    )
    conn.commit()
    chat_buffer.clear()  # Clear buffer after saving
    print("Buffered chats saved successfully.")

# Ensure buffered chats are stored when Flask shuts down
atexit.register(commit_chat_buffer)

# Function to fetch chat history grouped into Today, Yesterday, and Previous Chats
def get_chat_history_by_date():
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    cursor.execute("""
        SELECT session_id, user_input, ai_response, DATE(timestamp) as chat_date, TIME(timestamp) as chat_time
        FROM chat_history
        ORDER BY timestamp DESC
    """)
    data = cursor.fetchall()

    chat_dict = {
        "Today": [],
        "Yesterday": [],
        "Previous Chats": []
    }

    for session_id, user_input, ai_response, chat_date, chat_time in data:
        chat_entry = {
            "session_id": session_id,
            "time": chat_time,
            "user_input": user_input,
            "ai_response": ai_response
        }

        if chat_date == str(today):
            chat_dict["Today"].append(chat_entry)
        elif chat_date == str(yesterday):
            chat_dict["Yesterday"].append(chat_entry)
        else:
            chat_dict["Previous Chats"].append(chat_entry)

    return chat_dict

# Function to fetch all stored emails
def get_all_emails():
    cursor.execute("SELECT name, email FROM emails")
    return cursor.fetchall()

# Function to fetch all reminders
def get_all_reminders():
    cursor.execute("SELECT id, reminder_text, reminder_time FROM reminders ORDER BY reminder_time ASC")
    return cursor.fetchall()

# Close connection on exit
def close_connection():
    print("Closing database connection...")
    conn.close()

atexit.register(close_connection)
