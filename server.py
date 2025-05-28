import aiosqlite
import asyncio
import binascii
import json
import sqlite3

from asyncio import StreamReader, StreamWriter
from base64 import b64decode
from secrets import randbits

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

import server.database_functions
import server.exceptions
import server.handling

_REQUIRED_PARAMETERS: list[tuple[str, type]] = [
    ('data', dict),
    ('signature', str),
    ('public_key', str),
]

class MalformedRequestError(Exception):
    pass

class RequestTooLargeError(Exception):
    pass

_MalformationExceptions = (
    binascii.Error,
    json.JSONDecodeError,
    MalformedRequestError,
    server.exceptions.MalformedDataError,
)

class Server:
    def __init__(
            self,
            db_name: str,
            host: str = '127.0.0.1',
            port: int = 8888,
            max_request_bytes: int = 4096,
        ):
        # Store all necessary parameters.
        self.db_name = db_name
        self.host = host
        self.port = port
        self.max_request_bytes = max_request_bytes

        # Ensure that the database is set up.
        with sqlite3.connect(db_name) as conn:
            server.database_functions.create_tables(conn)
        
        # Prepare a variable to hold an asynchronous connection.
        self.db_connection = None

    async def main(self):
        """Start listening for requests on the context's host and port."""
        self.db_connection = await aiosqlite.connect(self.db_name)
        server = await asyncio.start_server(self.listen, self.host, self.port)
        try:
            async with server:
                await server.serve_forever()
        except asyncio.CancelledError:
            pass
        finally:
            await self.db_connection.commit()
            await self.db_connection.close()


    async def listen(self, reader: StreamReader, writer: StreamWriter):
        """Retrieve and validate an incoming request."""
        # Report the address of the connection.
        address = writer.get_extra_info('peername')
        print(f'Connection from {address}.')

        try:
            # Read the request and validate its size.
            if self.max_request_bytes == -1:
                raw_request = await reader.read(self.max_request_bytes)
            else:
                raw_request = await reader.read(self.max_request_bytes + 1)
                if len(raw_request) > self.max_request_bytes:
                    raise RequestTooLargeError()
            
            # Extract a dictionary from the raw request.
            request = json.loads(raw_request)

            # Validate the overall structure of the request.
            if not isinstance(request, dict):
                raise MalformedRequestError()
            for name, type in _REQUIRED_PARAMETERS:
                if name not in request:
                    raise MalformedRequestError()
                elif not isinstance(request[name], type):
                    raise MalformedRequestError()
                
            # Verify the signature provided.
            data = request['data']
            signature = b64decode(request['signature'])
            key_bytes = b64decode(request['public_key'])
            if len(key_bytes) != 32:
                raise MalformedRequestError()
            public_key = Ed25519PublicKey.from_public_bytes(key_bytes)
            public_key.verify(signature, json.dumps(data).encode())                

            # Pass the request data to the handling logic.
            response = await server.handling.handle_data(
                conn=self.db_connection,
                data=data,
                public_key=request['public_key'],
            )
        except _MalformationExceptions:
            response = {
                'status': '400',
                'message': 'Malformed request.',
            }
        except InvalidSignature:
            response = {
                'status': '401',
                'message': 'Invalid signature.',
            }
        except server.handling.UnrecognisedCommandError:
            response = {
                'status': '404',
                'message': 'Unrecognised command.',
            }
        except RequestTooLargeError:
            response = {
                'status': '413',
                'message': 'Request too large.',
            }
        except Exception as e:
            response = {
                'status': '500',
                'message': str(e),
            }

        # Attach a 32-byte nonce to the response.
        #response['nonce'] = randbits(256)

        # Send the response to the client.
        writer.write(json.dumps(response).encode())
        await writer.drain()

        # Close the connection.
        writer.close()
        await writer.wait_closed()


if __name__ == '__main__':
    server = Server('server/server_database.db')
    asyncio.run(server.main())