import sqlite3
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
    con.commit()
    con.close()

def save_message(user_id, role, text, db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    cursor = con.cursor()
    cursor.execute("INSERT INTO messages (user_id, role, text) VALUES (?, ?, ?)",
                    (user_id, role, text))
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

if __name__ == "__main__":
    setup()
    save_message(1212, 'user', 'Hello, This is test message 1')
    save_message(1212, 'user', 'Hello, This is test message 2')
    save_message(1212, 'user', 'Hello, This is test message 3')
    messages_1 = fetch_messages(1111, 1)
    for message in messages_1:
        print(message)
    messages_2= fetch_messages(1212, 2)
    for message in messages_2:
        print(message)


