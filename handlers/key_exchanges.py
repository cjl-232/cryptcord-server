from sqlalchemy.ext.asyncio import AsyncConnection

from _database import get_user_id
from exceptions import MalformedDataError
from json_types import JSONDict

_POST_KEY_QUERY = ' '.join([
    'INSERT INTO',
    '  exchange_keys(',
    '    sender_id,',
    '    recipient_id,',
    '    public_exchange_key,',
    '    signature',
    '  )',
    'VALUES(?, ?, ?, ?)',
])

_RETRIEVE_KEYS_QUERY = ' '.join([
    'SELECT',
    '  u.public_key as sender_public_key,',
    '  e.public_exchange_key,',
    '  e.signature',
    'FROM',
    '  exchange_keys e',
    'LEFT JOIN',
    '  users u',
    'ON',
    '  e.sender_id = u.id',
    'WHERE',
    '  e.recipient_id = ?',
])

async def post_key(
        user_id: int,
        data: JSONDict,
        conn: AsyncConnection,
    ) -> JSONDict:
    """Post an exchange key for another user to collect."""
    try:
        recipient_id = await get_user_id(conn, data['recipient_public_key'])
        # Verify the key and signature parameters.
        public_exchange_key = data['public_exchange_key']
        signature = data['signature']
        parameters = (
            user_id,
            recipient_id,
            public_exchange_key,
            signature,
        )
        await conn.execute(_POST_KEY_QUERY, parameters)
    except KeyError:
        raise MalformedDataError()
    return {'status': 201, 'message': 'Key posted.'}

async def retrieve_keys(
        user_id: int,
        _: JSONDict,
        conn: AsyncConnection,
    ) -> JSONDict:
    """Retrieve all keys posted to the request's author."""
    parameters = (user_id,)
    keys = await conn.execute_fetchall(_RETRIEVE_KEYS_QUERY, parameters)
    return {
        'status': 200,
        'message': f'{len(keys)} keys retrieved.',
        'data': keys,
    }