import os
import sqlite3
import re
from pypdf import PdfReader
DB_PATH = 'agent.db'
MAX_CHUNK_CHARS = 1500

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
    c = con.cursor()
    c.execute ('''CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5
                (text , file UNINDEXED, page UNINDEXED)''')
    con.commit()
    con.close()

def ingest_folder(db_path=DB_PATH):
    setup_docs(db_path)
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'docs_samples')
    disk_files = set()
    for filename in os.listdir(folder):
        extension = os.path.splitext(filename)[1].lower()
        if extension in ('.txt', '.pdf'):
            disk_files.add(filename)
            file_path = os.path.join(folder, filename)
            try:
                if extension == '.pdf':
                    ingest_pdf(file_path, db_path)
                else:
                    ingest_file(file_path, db_path)
            except Exception as error:
                print(f'Failed to ingest {filename}: {error}')

    con = sqlite3.connect(db_path)
    try:
        stored_files = {
            row[0] for row in con.execute('SELECT DISTINCT file FROM docs')
        }
        for filename in stored_files - disk_files:
            con.execute('DELETE FROM docs WHERE file = ?', (filename,))
        con.commit()
    finally:
        con.close()

def ingest_file(file_path, db_path=DB_PATH):
    file_name = os.path.basename(file_path)
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    con = sqlite3.connect(db_path)
    try:
        c = con.cursor()
        c.execute('DELETE FROM docs WHERE file = ?', (file_name,))
        c.executemany(
            'INSERT INTO docs (text, file, page) VALUES (?, ?, ?)',
            [(line, file_name, page) for page, line in enumerate(lines, 1)]
        )
        con.commit()
    finally:
        con.close()

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

def ingest_pdf(file_path, db_path=DB_PATH):
    setup_docs(db_path)
    file_name = os.path.basename(file_path)
    reader = PdfReader(file_path)
    con = sqlite3.connect(db_path)
    skipped_pages = 0
    try:
        con.execute('DELETE FROM docs WHERE file = ?', (file_name,))
        for page_number, page in enumerate(reader.pages, 1):
            text = strip_references((page.extract_text() or '').strip())
            if not text:
                skipped_pages += 1
                print(f'{file_name}: page {page_number} skipped (no text)')
                continue
            chunks = split_into_chunks(text, MAX_CHUNK_CHARS)
            con.executemany(
                'INSERT INTO docs (text, file, page) VALUES (?, ?, ?)',
                [(chunk, file_name, page_number) for chunk in chunks]
            )
        con.commit()
    finally:
        con.close()
    return skipped_pages

def search_documents(question, db_path=DB_PATH):
    """Search documents and return results with named fields."""
    query = make_query(question)
    if query is None:
        return []

    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            'SELECT text, file, page, rank FROM docs WHERE docs MATCH ? '
            'ORDER BY rank LIMIT 5', (query,)).fetchall()
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