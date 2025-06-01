from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database._models import EncryptedMessage, User
from database.utilities import get_user_id
from exceptions import MalformedDataError
from json_types import JSONDict, JSONType

async def post_message(
        session: AsyncSession,
        data: JSONDict,
        user_id: int,
    ) -> JSONDict:
    recipient_public_key = str(data['recipient_public_key'])
    ciphertext = str(data['ciphertext'])
    signature = str(data['signature'])
    recipient_id = await get_user_id(session, recipient_public_key)
    message = EncryptedMessage(
        ciphertext=ciphertext,
        signature=signature,
        sender_id=user_id,
        recipient_id=recipient_id,
    )
    session.add(message)
    await session.commit()
    return {
        'status': 201,
        'message': 'Message posted successfully.',
        'data': {
            'timestamp': message.timestamp.isoformat(),
        }
    }

async def retrieve_messages(
        session: AsyncSession,
        data: JSONDict,
        user_id: int,
    ) -> JSONDict:
    min_datetime = datetime.min
    if 'min_datetime' in data:
        try:
            min_datetime = datetime.fromisoformat(str(data['min_datetime']))
        except:
            raise MalformedDataError('Invalid date format.')
    statement = select(
        EncryptedMessage,
    ).where(
        EncryptedMessage.recipient_id == user_id
        and EncryptedMessage.timestamp >= min_datetime
    ).order_by(
        EncryptedMessage.timestamp,
    )
    result = await session.execute(statement)
    response_data: JSONDict = {'messages': []}
    for row in result.fetchall():
        response_data['messages'].append({
            'id': row[0].id,
            'ciphertext': row[0].ciphertext,
        })
    print(response_data)
    response: JSONDict = {
        'status': 200,
        'message': f'{len(response_data['messages'])} messages retrieved.',
        'data': response_data,
    }
    return response

# from datetime import datetime

# from aiosqlite import Connection

# from _database import get_user_id
# from exceptions import MalformedDataError
# from json_types import JSONDict

# # At some point I'll want better documentation of the commands. At that point, it'll
# # probably be helpful to somehow have their required arguments stored in one place...
# # An outright class, perhaps? See if there's some way to override the () operator like in C++?

# _GET_MESSAGES_QUERY = ' '.join([
#     'SELECT',
#     '  m.timestamp,',
#     '  u.public_key,',
#     '  m.encrypted_message,',
#     '  m.signature',
#     'FROM',
#     '  messages m',
#     'LEFT JOIN',
#     '  users u',
#     'ON',
#     '  m.sender_id = u.id',
#     'WHERE',
#     '  m.recipient_id = ?',
#     '  AND m.timestamp >= ?',
#     'ORDER BY',
#     '  m.sender_id,',
#     '  m.timestamp',
# ])

# _SEND_MESSAGE_QUERY = ' '.join([
#     'INSERT INTO',
#     '  messages(',
#     '    sender_id,',
#     '    recipient_id,',
#     '    encrypted_message,',
#     '    signature,',
#     '    timestamp',
#     '  )',
#     'VALUES(?, ?, ?, ?, ?)',
# ])

# async def get_messages(
#         user_id: int,
#         data: JSONDict,
#         conn: Connection,
#     ) -> JSONDict:
#     """Retrieve the user's messages from the connection."""
#     parameters = (user_id, data.get('min_datetime', datetime.min))
#     await conn.set_trace_callback(print)
#     messages = await conn.execute_fetchall(_GET_MESSAGES_QUERY, parameters)
#     return {
#         'status': 200,
#         'message': f'{len(messages)} messages retrieved.',
#         'data': messages,
#     }

# async def send_message(
#         user_id: int,
#         data: JSONDict,
#         conn: Connection,
#     ) -> JSONDict:
#     try:
#         recipient_id = await get_user_id(conn, data['recipient_public_key'])
#         encrypted_message = data['encrypted_message']
#         signature = data['signature']
#         timestamp = datetime.now()
#         parameters = (
#             user_id,
#             recipient_id,
#             encrypted_message,
#             signature,
#             timestamp,
#         )
#         await conn.execute(_SEND_MESSAGE_QUERY, parameters)
#     except KeyError:
#         raise MalformedDataError()
#     return {'status': 201, 'message': 'Message sent.'}