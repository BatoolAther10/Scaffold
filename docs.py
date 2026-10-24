import os
import sqlite3
import re
DB_PATH = 'agent.db'

STOPWORDS = {
    'is', 'the', 'a', 'of', 'when', 'what', 'and', 'or', 'to',
    'in', 'on', 'for', 'with', 'at', 'by', 'from', 'this', 'that',
}

def setup_docs(db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    c = con.cursor()
    c.execute ('''CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5
                (text , file UNINDEXED, page UNINDEXED)''')
    con.commit()
    con.close()

def ingest_folder(db_path=DB_PATH):
    setup_docs(db_path)
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs_samples')
    for filename in os.listdir(folder):
        if filename.lower().endswith('.txt'):
            ingest_file(os.path.join(folder, filename), db_path)

def ingest_file(file_path, db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    c = con.cursor()
    file_name = os.path.basename(file_path)
    c.execute('DELETE FROM docs WHERE file = ?', (file_name,))
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    c.executemany(
        'INSERT INTO docs (text, file, page) VALUES (?, ?, ?)',
        [(line, file_name, page) for page, line in enumerate(lines, 1)]
    )
    con.commit()
    con.close()

def search_documents(question, db_path=DB_PATH):
    """Search documents and return results with named fields."""
    query = make_query(question)
    if query is None:
        return []

    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            'SELECT text, file, page FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT 3',
            (query,)
        ).fetchall()
        return [
            {'text': text, 'file': file, 'page': page}
            for text, file, page in rows
        ]
    finally:
        con.close()

def make_query(text):
    words = [
        word
        for word in re.findall(r'[a-zA-Z0-9]+', text.lower())
        if word not in STOPWORDS
    ]
    if not words:
        return None
    return ' OR '.join(f'"{word}"' for word in words)