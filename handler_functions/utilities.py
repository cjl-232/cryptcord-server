import binascii

from base64 import b64decode

from aiosqlite import Connection

from server.exceptions import MalformedDataError

_RETRIEVAL_QUERY = 'SELECT id FROM users WHERE public_key = ?'
_INSERTION_QUERY = 'INSERT INTO users(public_key) VALUES(?) RETURNING id'

async def get_user_id(conn: Connection, public_key: str) -> int:
    """
    Retrieves a unique user id for the supplied public key.

    If the public key is already stored in the database's user's table, this
    returns the associated id. Otherwise, it adds a new row and then returns
    that row's id.
    """
    # Validate the key.
    try:
        if len(b64decode(public_key, validate=True)) != 32:
            raise MalformedDataError()
    except binascii.Error:
        raise MalformedDataError()
        
    # If the key is acceptable, execute the appropriate queries.
    parameters = (public_key,)
    async with conn.execute(_RETRIEVAL_QUERY, parameters) as cursor:
        row = await cursor.fetchone()
    if row is not None:
        return row[0]
    else:
        async with conn.execute(_INSERTION_QUERY, parameters) as cursor:
            row = await cursor.fetchone()
        return row[0]