import sqlite3
import os
import atexit
from flask import Flask, request, jsonify
from flask_cors import CORS
from main import main  # Import main function from main.py
from datetime import datetime, timedelta
from dotenv import load_dotenv
from Plugins.database import get_latest_session_id, create_new_session, get_or_create_daily_session,chat_buffer, commit_chat_buffer
import threading
import time


# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

def auto_save_buffer():
    """Periodically saves buffered chats to the database."""
    while True:
        time.sleep(60)  # Save every 60 seconds
        commit_chat_buffer()

# Start auto-save thread
threading.Thread(target=auto_save_buffer, daemon=True).start()

def ensure_session_exists():
    print("Checking for existing session...")  # Debugging step
    session_id = get_latest_session_id()
    
    if session_id:
        print(f"Found existing session: {session_id}")
    else:
        print("No session found. Creating a new session...")
        session_id = create_new_session()
    
    return session_id

env_path = os.path.join(os.path.dirname(__file__), '..', 'Data', '.env')
load_dotenv(env_path)

DB_PATH = os.getenv('DB_FILE')

@app.route("/process_voice", methods=["POST"])
def process_voice():
    """Handles voice commands sent from frontend"""
    data = request.json
    user_input = data.get("text", "").strip()

    if not user_input:
        return jsonify({"response": "No input received.", "read_aloud": False})

    print("User Input:", user_input)
    
    response = main(user_input)

    if isinstance(response, dict):
        ai_response = response.get("response", "No response generated.")
        details = response.get("details", "")
        read_aloud = response.get("read_aloud", False)
    else:
        ai_response = response
        details = ""
        read_aloud = False

    return jsonify({
        "response": ai_response,
        "details": details,
        "read_aloud": read_aloud
    })

@app.route("/get_sessions", methods=["GET"])
def get_sessions():
    """Fetch stored chat sessions from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT session_id, start_time FROM sessions ORDER BY start_time DESC")
        sessions = cursor.fetchall()
        conn.close()

        print("Sessions Retrieved:", sessions)

        categorized_sessions = {
            "Today": [],
            "Yesterday": [],
            "Previous Chats": []
        }

        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        for session_id, time in sessions:
            try:
                session_datetime = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                session_datetime = datetime.strptime(time, "%Y-%m-%d")

            session_date = session_datetime.date()

            if session_date == today:
                category = "Today"
            elif session_date == yesterday:
                category = "Yesterday"
            else:
                category = "Previous Chats"

            categorized_sessions[category].append({
                "id": session_id,
                "time": time
            })

        return jsonify(categorized_sessions)
    except Exception as e:
        print(f"Error in get_sessions: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/get_chat_history/<int:session_id>", methods=["GET"])
def get_chat_history(session_id):
    """Fetch all chat messages for a given session."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_input, ai_response, timestamp 
        FROM chat_history 
        WHERE session_id = ? 
        ORDER BY timestamp
    """, (session_id,))
    
    messages = cursor.fetchall()
    conn.close()

    chat_data = [{"user": row[0], "bot": row[1], "time": row[2]} for row in messages]
    return jsonify(chat_data)

def get_or_create_session():
    """Ensure a session exists for today and return its session ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today_date = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("SELECT session_id FROM sessions WHERE DATE(start_time) = ?", (today_date,))
    session = cursor.fetchone()

    if session:
        session_id = session[0]
        print(f"Using existing session ID: {session_id}")
    else:
        cursor.execute("INSERT INTO sessions (start_time) VALUES (?)", (today_date,))
        conn.commit()
        session_id = cursor.lastrowid
        print(f"Created new session ID: {session_id}")
    print(f"🛠️ DEBUG: Storing chat in session ID: {session_id}")

    conn.close()
    return session_id

@app.route('/store_chat', methods=['POST'])
def store_chat():
    """Buffer chat messages instead of storing them instantly."""
    data = request.json
    user_input = data.get("user_input")
    ai_response = data.get("ai_response")

    if not user_input or not ai_response:
        print("Invalid input received! User input or AI response missing.")
        return jsonify({"error": "Invalid input"}), 400

    session_id = get_or_create_daily_session()
    print(f"Buffering chat for session ID: {session_id}")

    # Store the chat in the buffer (NOT in the database yet)
    chat_buffer.append((session_id, user_input, ai_response, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    # 🛠 DEBUG: Print buffer state
    print(f"🛠️ DEBUG: Current chat buffer → {chat_buffer}")  

    return jsonify({"message": "Chat buffered successfully", "session_id": session_id})

# Ensure buffered chats are saved on server shutdown
atexit.register(commit_chat_buffer)

@app.before_request
def setup():
    """Runs before handling any request (Flask 2.3+ safe)."""
    print("Server started. Chat buffering enabled.")


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Commit buffered chats to the database on shutdown."""
    if chat_buffer:
        print("Committing buffered chat messages to the database...")
        commit_chat_buffer()
        chat_buffer.clear()
    print("All buffered chats saved.")
import atexit
atexit.register(commit_chat_buffer)  # Ensure it's called only at exit

if __name__ == "__main__":
    print("Starting Flask server on port 8000...")
    app.run(host="0.0.0.0", port=8000, debug=False)
