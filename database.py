import base64
import binascii
import sqlite3

import aiosqlite

from exceptions import MalformedRequestError

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

_USER_RETRIEVAL_QUERY = 'SELECT id FROM users WHERE public_key = ?'
_USER_INSERTION_QUERY = 'INSERT INTO users(public_key) VALUES(?) RETURNING id'

async def get_user_id(conn: aiosqlite.Connection, public_key: str) -> int:
    """
    Retrieves a unique user id for the supplied public key.

    If the public key is already stored in the database's user's table, this
    returns the associated id. Otherwise, it adds a new row and then returns
    that row's id.
    """
    # Validate the key.
    try:
        if len(base64.b64decode(public_key, validate=True)) != 32:
            raise MalformedRequestError('Invalid public key length.')
    except binascii.Error:
        raise MalformedRequestError('Invalid public key format.')
        
    # If the key is acceptable, execute the appropriate queries.
    parameters = (public_key,)
    async with conn.execute(_USER_RETRIEVAL_QUERY, parameters) as cursor:
        row = await cursor.fetchone()
    if row is None:
        async with conn.execute(_USER_INSERTION_QUERY, parameters) as cursor:
            row = await cursor.fetchone()
    return row[0]