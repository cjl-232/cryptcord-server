from base64 import b64encode
from datetime import datetime

from aiosqlite import Connection

from database import get_user_id
from exceptions import MalformedDataError
from json_types import JSONDict

# At some point I'll want better documentation of the commands. At that point, it'll
# probably be helpful to somehow have their required arguments stored in one place...
# An outright class, perhaps? See if there's some way to override the () operator like in C++?

_GET_MESSAGES_QUERY = ' '.join([
    'SELECT',
    '  m.timestamp,',
    '  u.public_key,',
    '  m.encrypted_message,',
    '  m.signature',
    'FROM',
    '  messages m',
    'LEFT JOIN',
    '  users u',
    'ON',
    '  m.sender_id = u.id',
    'WHERE',
    '  m.recipient_id = ?',
    '  AND m.timestamp >= ?',
    'ORDER BY',
    '  m.sender_id,',
    '  m.timestamp',
])

_SEND_MESSAGE_QUERY = ' '.join([
    'INSERT INTO',
    '  messages(',
    '    sender_id,',
    '    recipient_id,',
    '    encrypted_message,',
    '    signature,',
    '    timestamp',
    '  )',
    'VALUES(?, ?, ?, ?, ?)',
])

async def get_messages(user_id: int, data: JSONDict, conn: Connection):
    """Retrieve the user's messages from the connection."""
    parameters = (user_id, data.get('min_datetime', datetime.min))
    await conn.set_trace_callback(print)
    messages = await conn.execute_fetchall(_GET_MESSAGES_QUERY, parameters)
    return {
        'status': 200,
        'message': f'{len(messages)} messages retrieved.',
        'data': messages,
    }

async def send_message(user_id: int, data: JSONDict, conn: Connection):
    try:
        recipient_id = await get_user_id(conn, data['recipient_public_key'])
        encrypted_message = data['encrypted_message']
        signature = data['signature']
        timestamp = datetime.now()
        parameters = (
            user_id,
            recipient_id,
            encrypted_message,
            signature,
            timestamp,
        )
        await conn.execute(_SEND_MESSAGE_QUERY, parameters)
    except KeyError:
        raise MalformedDataError()
    return {'status': 201, 'message': 'Message sent.'}