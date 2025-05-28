import aiosqlite
import sqlite3

from datetime import datetime

def create_tables(conn: sqlite3.Connection):
    conn.execute(' '.join([
        'CREATE TABLE IF NOT EXISTS users(',
        '  id INTEGER PRIMARY KEY,',
        '  public_key CHAR(44) UNIQUE NOT NULL',
        ')',
    ]))
    conn.execute(' '.join([
        'CREATE TABLE IF NOT EXISTS messages(',
        '  id INTEGER PRIMARY KEY,',
        '  sender_id INTEGER NOT NULL,',
        '  recipient_id INTEGER NOT NULL,',
        '  encrypted_message TEXT NOT NULL,',
        '  signature CHAR(88) NOT NULL,',
        '  timestamp DATETIME NOT NULL,',
        '  FOREIGN KEY(sender_id) REFERENCES users(id),',
        '  FOREIGN KEY(recipient_id) REFERENCES users(id)'
        ')',
    ]))
    conn.execute(' '.join([
        'CREATE INDEX IF NOT EXISTS message_users ON messages(',
        '  sender_id,',
        '  recipient_id',
        ')',
    ]))
    conn.execute(' '.join([
        'CREATE INDEX IF NOT EXISTS retrieval_index ON messages(',
        '  sender_id,',
        '  recipient_id,',
        '  timestamp',
        ')',
    ]))
    conn.commit()