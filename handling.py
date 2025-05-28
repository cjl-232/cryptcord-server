import asyncio

from typing import Awaitable, Callable

from aiosqlite import Connection

from json_types import JSONDict
from server.exceptions import MalformedDataError, UnrecognisedCommandError
from server.handler_functions.messages import get_messages, send_message
from server.handler_functions.utilities import get_user_id

type _HandlerResult = Awaitable[JSONDict]
type _HandlerCallable = Callable[[Connection, int, JSONDict], _HandlerResult]
_DATA_HANDLERS: dict[str, _HandlerCallable] = {
    'GET_MESSAGES': get_messages,
    'SEND_MESSAGE': send_message,
}

async def handle_data(
        conn: Connection,
        data: JSONDict,
        public_key: str,
    ) -> JSONDict:
    id = await get_user_id(conn, public_key)
    if 'command' not in data:
        raise MalformedDataError()
    elif data['command'] not in _DATA_HANDLERS:
        raise UnrecognisedCommandError()
    if 'command' in data and data['command'] in _DATA_HANDLERS:
        return await _DATA_HANDLERS[data['command']](conn, id, data)
    else:
        raise MalformedDataError()