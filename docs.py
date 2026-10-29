import os
import sqlite3
import re
from pypdf import PdfReader

DB_PATH = 'agent.db'
MAX_CHUNK_CHARS = 1500
BASE = os.path.dirname(os.path.abspath(__file__))
DEMO_FOLDER = os.path.join(BASE, 'docs_samples')
USER_FOLDER = os.path.join(BASE, 'user_docs')

STOPWORDS = {
    'is', 'the', 'a', 'of', 'when', 'what', 'and', 'or', 'to',
    'in', 'on', 'for', 'with', 'at', 'by', 'from', 'this', 'that',
}

REF_LINE = re.compile(r'^\d{1,3}\.\s+\S')
REF_HINTS = ('doi:', 'http', 'retrieved', 'pmid', 'issn')


def strip_references(text):
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if REF_LINE.match(line.strip()):
            window = ' '.join(lines[i:i + 6]).lower()
            if any(h in window for h in REF_HINTS):
                return '\n'.join(lines[:i]).strip()
    return text


def setup_docs(db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    con.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5
                (text, file UNINDEXED, page UNINDEXED, user_id UNINDEXED)''')
    con.commit()
    con.close()


def folder_files():
    found = []
    if os.path.isdir(DEMO_FOLDER):
        for name in os.listdir(DEMO_FOLDER):
            path = os.path.join(DEMO_FOLDER, name)
            if os.path.isfile(path):
                found.append(('shared', name, path))
    if os.path.isdir(USER_FOLDER):
        for uid in os.listdir(USER_FOLDER):
            sub = os.path.join(USER_FOLDER, uid)
            if os.path.isdir(sub):
                for name in os.listdir(sub):
                    path = os.path.join(sub, name)
                    if os.path.isfile(path):
                        found.append((uid, name, path))
    return found


def ingest_path(file_path, user_id='shared', db_path=DB_PATH):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return ingest_pdf(file_path, user_id, db_path)
    return ingest_file(file_path, user_id, db_path)


def ingest_folder(db_path=DB_PATH):
    setup_docs(db_path)
    on_disk = set()
    for uid, name, path in folder_files():
        if os.path.splitext(name)[1].lower() not in ('.txt', '.pdf'):
            continue
        on_disk.add((uid, name))
        try:
            ingest_path(path, uid, db_path)
        except Exception as error:
            print(f'Failed to ingest {name}: {error}')
    con = sqlite3.connect(db_path)
    try:
        stored = set(con.execute(
            'SELECT DISTINCT user_id, file FROM docs').fetchall())
        for uid, name in stored - on_disk:
            con.execute('DELETE FROM docs WHERE user_id = ? AND file = ?',
                        (uid, name))
        con.commit()
    finally:
        con.close()


def ingest_file(file_path, user_id='shared', db_path=DB_PATH):
    user_id = str(user_id)
    file_name = os.path.basename(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    con = sqlite3.connect(db_path)
    try:
        con.execute('DELETE FROM docs WHERE file = ? AND user_id = ?',
                    (file_name, user_id))
        con.executemany(
            'INSERT INTO docs (text, file, page, user_id) VALUES (?, ?, ?, ?)',
            [(line, file_name, page, user_id)
             for page, line in enumerate(lines, 1)]
        )
        con.commit()
    finally:
        con.close()
    return len(lines)


def split_into_chunks(text, max_chars=MAX_CHUNK_CHARS):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    chunks, current, size = [], [], 0
    for line in lines:
        if current and size + len(line) > max_chars:
            chunks.append('\n'.join(current))
            current = current[-1:]  # overlap: keep the last line
            size = len(current[0])
        current.append(line)
        size += len(line)
    if current:
        chunks.append('\n'.join(current))
    return chunks


def ingest_pdf(file_path, user_id='shared', db_path=DB_PATH):
    user_id = str(user_id)
    setup_docs(db_path)
    file_name = os.path.basename(file_path)
    reader = PdfReader(file_path)
    con = sqlite3.connect(db_path)
    inserted = 0
    try:
        con.execute('DELETE FROM docs WHERE file = ? AND user_id = ?',
                    (file_name, user_id))
        for page_number, page in enumerate(reader.pages, 1):
            text = strip_references((page.extract_text() or '').strip())
            if not text:
                print(f'{file_name}: page {page_number} skipped (no text)')
                continue
            chunks = split_into_chunks(text, MAX_CHUNK_CHARS)
            con.executemany(
                'INSERT INTO docs (text, file, page, user_id) VALUES (?, ?, ?, ?)',
                [(chunk, file_name, page_number, user_id) for chunk in chunks]
            )
            inserted += len(chunks)
        con.commit()
    finally:
        con.close()
    return inserted


def search_documents(question, user_id='shared', db_path=DB_PATH):
    """Search this user's documents plus the shared demo documents."""
    query = make_query(question)
    if query is None:
        return []

    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            'SELECT text, file, page, rank FROM docs '
            'WHERE docs MATCH ? AND user_id IN (?, ?) '
            'ORDER BY rank LIMIT 5',
            (query, str(user_id), 'shared')).fetchall()
        if not rows:
            return []
        best = rows[0][3]  # rank is negative; more negative = better
        keep = [r for r in rows if r[3] <= best * 0.4][:3]
        return [{'text': t, 'file': f, 'page': p} for t, f, p, _ in keep]
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