import sqlite3
from datetime import datetime, timedelta, timezone
DB_PATH = 'agent.db'

def setup(db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS messages 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER,
                   role TEXT,
                   text TEXT,
                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS reminders
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    reminder_text TEXT NOT NULL ,
                    due_at TEXT NOT NULL,
                    done INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # --- NEW GAMIFICATION TABLES ---
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_profile
                    (user_id INTEGER PRIMARY KEY,
                    total_xp INTEGER DEFAULT 0,
                    current_level INTEGER DEFAULT 1,
                    current_streak INTEGER DEFAULT 0,
                    last_completed_date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS habits
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    habit_name TEXT,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    # -------------------------------
    
    con.commit()
    con.close()

def save_message(user_id, role, text, db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute("INSERT INTO messages (user_id, role, text) VALUES (?, ?, ?)",
                    (user_id, role, text))
    con.commit()
    con.close()

def get_ist_now():
    ist_zone = timezone(timedelta(hours=5, minutes=30))
    ist_moment = datetime.now(ist_zone)
    return ist_moment.replace(tzinfo=None)

def save_reminder(user_id, reminder_text, due_at, db_path=DB_PATH):
    if not isinstance(reminder_text, str) or not reminder_text.strip():
        msg = "reminder_text must not be empty or whitespace-only"
        return msg

    try:
        due = datetime.fromisoformat(due_at)
    except (ValueError, TypeError):
        msg = "Invalid date format for due_at, it should be in ISO format (YYYY-MM-DDTHH:MM:SS)"
        return msg

    if due.tzinfo is not None:
         msg = ("Invalid due_at: do not include a timezone offset such as +05:30 or Z. "
       "Send the local IST time in the format YYYY-MM-DDTHH:MM:SS, "
       "for example 2026-10-20T18:06:00, and call the tool again.")
         return msg

    ist_now = get_ist_now()
    if due < ist_now:
        msg = f"{reminder_text} is rejected. Invalid due_at: the date and time must be in the future. Ask user again to" \
        " provide a valid future date and time in the format YYYY-MM-DDTHH:MM:SS."
        return msg
    due_text = due.isoformat(timespec='seconds')
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute("INSERT INTO reminders (user_id, reminder_text, due_at) VALUES (?, ?, ?)",
                   (user_id, reminder_text, due_text))
    con.commit()
    con.close()
    return f"Reminder saved successfully. Due = {due_text}"

def due_reminders(db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    now = get_ist_now().isoformat(timespec='seconds')
    cursor.execute(
        "SELECT id, user_id, reminder_text FROM reminders "
        "WHERE done = 0 AND due_at <= ? ORDER BY due_at ASC",
        (now,),
    )
    reminders = cursor.fetchall()
    con.close()
    return reminders

def mark_done(reminder_id, db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute("UPDATE reminders SET done = 1 WHERE id = ?", (reminder_id,))
    con.commit()
    con.close()

def fetch_messages(user_id,N, db_path=DB_PATH):
    con=sqlite3.connect(db_path)
    cursor=con.cursor()
    cursor.execute("SELECT role, text FROM messages WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, N))
    messages=cursor.fetchall()
    history = []
    for role, text in messages:
        history.append({"role": role, "content": text})
    con.close()
    return list(reversed(history))

# --- NEW GAMIFICATION FUNCTIONS ---
def log_habit(user_id, habit_name, db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute("INSERT INTO habits (user_id, habit_name) VALUES (?, ?)", (user_id, habit_name))
    
    cursor.execute("SELECT total_xp, current_streak, last_completed_date FROM user_profile WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    today = get_ist_now().date()
    
    if not row:
        total_xp, streak, level = 10, 1, 1
        cursor.execute("INSERT INTO user_profile (user_id, total_xp, current_level, current_streak, last_completed_date) VALUES (?, ?, ?, ?, ?)", 
                       (user_id, total_xp, level, streak, today.isoformat()))
    else:
        total_xp, streak, last_date_str = row
        total_xp += 10
        if last_date_str:
            last_date = datetime.fromisoformat(last_date_str).date()
            delta = (today - last_date).days
            if delta == 1: streak += 1
            elif delta > 1: streak = 1
        else: 
            streak = 1
        
        level = 3 if total_xp > 100 else (2 if total_xp > 50 else 1)
        cursor.execute("UPDATE user_profile SET total_xp = ?, current_level = ?, current_streak = ?, last_completed_date = ? WHERE user_id = ?", 
                       (total_xp, level, streak, today.isoformat(), user_id))
                       
    con.commit()
    con.close()
    return f"Habit logged! Earned 10 XP. Total XP: {total_xp}. Level: {level}. Streak: {streak} days."

def get_status(user_id, db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute("SELECT total_xp, current_level, current_streak FROM user_profile WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    con.close()
    if row:
        return f"XP: {row[0]}, Level: {row[1]}, Streak: {row[2]} days."
    return "No habits logged yet. Complete a study task to earn your first XP!"
