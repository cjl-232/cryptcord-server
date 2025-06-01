# TODO somehow make malformed requests return information about missing parameters

# Generally port to sqlalchemy

import asyncio
import binascii
import json

from base64 import b64decode
from typing import Awaitable, Callable

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import exceptions

from database import _models, utilities
from handlers import key_exchanges, messages
from json_types import JSONDict

type _HandlerCallable = Callable[
    [AsyncSession, JSONDict, int],
    Awaitable[JSONDict],
]
    #'POST_KEY': key_exchanges.post_key,
    #'RETRIEVE_KEYS': key_exchanges.retrieve_keys,
_DATA_HANDLERS: dict[str, _HandlerCallable] = {
    'POST_MESSAGE': messages.post_message,
    'RETRIEVE_MESSAGES': messages.retrieve_messages,
}

# Need to make these more informative...
_MALFORMATION_EXCEPTIONS = (
    binascii.Error,
    exceptions.MalformedDataError,
    exceptions.MalformedRequestError,
    KeyError,
    json.JSONDecodeError,
    TypeError,
)

class Server:
    def __init__(
            self,
            database_url: str,
            host: str = '127.0.0.1',
            port: int = 8888,
            request_size_limit: int = 4096,
        ):
        self.engine = create_async_engine(database_url)
        self.host = host
        self.port = port
        self.request_size_limit = request_size_limit

    async def _listen(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
        ):
        """Retrieve, validate, and handle an inbound request."""
        address: str = writer.get_extra_info('peername')
        print(f'Connection from {address}.')

        try:
            # Confirm the request is a valid size.
            if self.request_size_limit <= -1:
                raw_request = await reader.read(-1)
            else:
                raw_request = await reader.read(self.request_size_limit + 1)
                if len(raw_request) > self.request_size_limit:
                    raise exceptions.RequestTooLargeError()
                
            # Extract the request from the raw bytes.
            request = json.loads(raw_request.decode())
            print(request)
            if not isinstance(request['data'], dict):
                raise exceptions.MalformedRequestError
            elif not isinstance(request['public_key'], str):
                raise exceptions.MalformedRequestError
            elif not isinstance(request['signature'], str):
                raise exceptions.MalformedRequestError
            
            # Pull out the individual components.
            data: JSONDict = request['data']
            data_bytes = json.dumps(data).encode()
            public_key_bytes = b64decode(request['public_key'])
            signature_bytes = b64decode(request['signature'])

            # Validate the authenticity of the request.
            public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key.verify(signature_bytes, data_bytes)

            # Attempt to handle the data.
            if not data['action'] in _DATA_HANDLERS:
                raise exceptions.UnrecognisedCommandError()
            
            handler = _DATA_HANDLERS[data['action']]

            async with AsyncSession(self.engine, expire_on_commit=False) as session:
                user_id = await utilities.get_user_id(
                    session=session,
                    public_key=request['public_key'],
                )
                response = await handler(
                    session,
                    data,
                    user_id,
                )
        except exceptions.RequestTooLargeError:
            response: JSONDict = {
                'status': 413,
                'message': (
                    f'Request too large. The maximum request size is '
                    f'{self.request_size_limit} bytes.'
                ),
            }
        except Exception as e:
            response: JSONDict = {
                'status': 500,
                'message': str(e),
            }
        # except Exception as e:
        #     response: JSONDict = {
        #         'status': 500,
        #         'message': str(e),
        #     }

        # Send the response to the client.
        writer.write(json.dumps(response).encode())
        await writer.drain()

        # Close the connection.
        writer.close()
        await writer.wait_closed()

    async def main(self):
        """Set up the database, then begin listening for connections."""
        async with self.engine.begin() as conn:
            await conn.run_sync(_models.Base.metadata.drop_all)
            await conn.run_sync(_models.Base.metadata.create_all)
        server = await asyncio.start_server(
            client_connected_cb=self._listen,
            host=self.host,
            port=self.port,
        )
        async with server:
            await server.serve_forever()

if __name__ == '__main__':
    server = Server('sqlite+aiosqlite:///test.db')
    asyncio.run(server.main())

# import asyncio
# import binascii
# import json
# import sqlite3

# from asyncio import StreamReader, StreamWriter
# from base64 import b64decode
# from typing import Awaitable, Callable

# import aiosqlite

# from cryptography.exceptions import InvalidSignature
# from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
# from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# import exceptions

# from database import create_tables, get_user_id
# from handlers import key_exchanges, messages
# from json_types import JSONDict

# type _HandlerCallable = Callable[
#     [int, JSONDict, aiosqlite.Connection],
#     Awaitable[JSONDict],
# ]

# _DATA_HANDLERS: dict[str, _HandlerCallable] = {
#     'POST_KEY': key_exchanges.post_key,
#     'RETRIEVE_KEYS': key_exchanges.retrieve_keys,
#     'GET_MESSAGES': messages.get_messages,
#     'SEND_MESSAGE': messages.send_message,
# }

# _REQUIRED_PARAMETERS: list[tuple[str, type]] = [
#     ('data', dict),
#     ('signature', str),
#     ('public_key', str),
# ]

# _MALFORMATION_EXCEPTIONS = (
#     binascii.Error,
#     exceptions.MalformedDataError,
#     exceptions.MalformedRequestError,
#     KeyError,
#     json.JSONDecodeError,
# )

# class Server:
#     def __init__(
#             self,
#             db_name: str,
#             host: str = '127.0.0.1',
#             port: int = 8888,
#             max_request_bytes: int = 4096,
#         ):
#         # Store all necessary parameters.
#         self.db_name = db_name
#         self.host = host
#         self.port = port
#         self.max_request_bytes = max_request_bytes

#         # Ensure that the database is set up.
#         with sqlite3.connect(db_name) as conn:
#             create_tables(conn)
        
#         # Prepare a variable to hold an asynchronous connection.
#         self.conn = None

#     async def main(self):
#         """Start listening for requests on the context's host and port."""
#         self.conn = await aiosqlite.connect(self.db_name)
#         server = await asyncio.start_server(self.listen, self.host, self.port)
#         try:
#             async with server:
#                 await server.serve_forever()
#         except asyncio.CancelledError:
#             pass
#         finally:
#             await self.conn.commit()
#             await self.conn.close()


#     async def listen(self, reader: StreamReader, writer: StreamWriter):
#         """Retrieve and validate an incoming request."""
#         # Report the address of the connection.
#         address = writer.get_extra_info('peername')
#         print(f'Connection from {address}.')

#         try:
#             # Read the request and validate its size.
#             if self.max_request_bytes == -1:
#                 raw_request = await reader.read(self.max_request_bytes)
#             else:
#                 raw_request = await reader.read(self.max_request_bytes + 1)
#                 if len(raw_request) > self.max_request_bytes:
#                     raise exceptions.RequestTooLargeError()
            
#             # Extract a dictionary from the raw request.
#             request = json.loads(raw_request)

#             # Validate the overall structure of the request.
#             if not isinstance(request, dict):
#                 raise exceptions.MalformedRequestError()
#             for name, type in _REQUIRED_PARAMETERS:
#                 if not isinstance(request[name], type):
#                     raise exceptions.MalformedRequestError()
                
#             # Verify the signature provided.
#             data = request['data']
#             signature = b64decode(request['signature'])
#             key_bytes = b64decode(request['public_key'])
#             if len(key_bytes) != 32:
#                 raise exceptions.MalformedRequestError()
#             public_key = Ed25519PublicKey.from_public_bytes(key_bytes)
#             public_key.verify(signature, json.dumps(data).encode())                

#             # Attempt to handle the request.
#             user_id = await get_user_id(self.conn, request['public_key'])
#             if data['command'] not in _DATA_HANDLERS:
#                 raise exceptions.UnrecognisedCommandError(data['command'])
#             handler = _DATA_HANDLERS[data['command']]
#             response = await handler(user_id, data, self.conn)

#         except _MALFORMATION_EXCEPTIONS:
#             response = {
#                 'status': '400',
#                 'message': 'Malformed request.',
#             }
#         except InvalidSignature:
#             response = {
#                 'status': '401',
#                 'message': 'Invalid signature.',
#             }
#         except exceptions.UnrecognisedCommandError as e:
#             response = {
#                 'status': '404',
#                 'message': f'{e} is not a recognised command.',
#             }
#         except exceptions.RequestTooLargeError:
#             response = {
#                 'status': '413',
#                 'message': 'Request too large.',
#             }
#         except Exception as e:
#             response = {
#                 'status': '500',
#                 'message': str(e),
#             }

#         # Send the response to the client.
#         writer.write(json.dumps(response).encode())
#         await writer.drain()

#         # Close the connection.
#         writer.close()
#         await writer.wait_closed()


# if __name__ == '__main__':
#     server = Server('database.db')
#     asyncio.run(server.main())