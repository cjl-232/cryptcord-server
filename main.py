import os

from contextlib import asynccontextmanager

import sqlalchemy

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from connections.schemas.requests import (
    PostExchangeKeyRequestModel,
    PostMessageRequestModel,
    FetchDataRequestModel,
)
from connections.schemas.responses import (
    BaseResponseModel,
    PostMessageResponseModel,
    PostExchangeKeyResponseModel,
    FetchDataResponseModel,
)
from database import operations
from database.models import Base

load_dotenv()

URL = sqlalchemy.URL.create(
    drivername=os.environ['DB_DRIVERNAME'],
    username=os.environ['DB_USERNAME'],
    password=os.environ['DB_PASSWORD'],
    host=os.environ['DB_HOST'],
    port=int(os.environ['DB_PORT']),
    database=os.environ['DB_NAME'],
)

engine = create_async_engine(URL)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Creates database tables on application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    return

app = FastAPI(
    #dependencies=[Depends(verify_user_key)],
    lifespan=lifespan,
)

@app.get('/ping')
async def ping() -> BaseResponseModel:
    """Ping the server to test connection."""
    return BaseResponseModel(status='success', message='pong')

@app.post('/data/fetch')
async def fetch_data(
    request: FetchDataRequestModel,
) -> FetchDataResponseModel:
    """
    Retrieve exchange keys and encrypted messages stored on the server.

    This request requires the user's public key, and will retrieve all exchange
    keys and encrypted messages stored on the server that are addressed to
    them. To limit the size of responses, the user may optionally provide a 
    'whitelist' of public keys, retrieving only data addressed from one of
    these, or a minimum datetime at which the data was stored. The response
    will contain a list of messages and a list of exchange keys, with the
    following contents:

    * Each item will include the public key the data is addressed from and the
    timestamp at which it was stored.
    * Each message will include the encrypted text, a signature, and a unique
    16-byte identifier in hexadecimal form.
    * Each exchange key will include the public key of an ephemeral 32-byte
    key pair, a signature, and, if applicable, the public exchange key it was
    sent in response to.

    In all cases the client should use the provided signatures to validate
    the authenticity of the data.
    """
    messages = await operations.retrieve_messages(engine, request)
    exchange_keys = await operations.retrieve_exchange_keys(engine, request)
    response = FetchDataResponseModel.model_validate({
        'status': 'success',
        'message': (
            f'Fetched {len(messages)} messages and {len(exchange_keys)} '
            f'exchange keys.'
        ),
        'data': {
            'messages': messages,
            'exchange_keys': exchange_keys,
        },
    })
    return response

@app.post('/data/post/message', status_code=201)
async def post_message(
    request: PostMessageRequestModel,
) -> PostMessageResponseModel:
    """
    Post an encrypted message to the server.

    This request requires the user's public key, a public key belonging to
    the intended recipient, the encrypted text itself, and a signature
    generated from the user's private key being used on Base-64 encoded bytes
    corresponding to the encrypted text. In the typical case where Fernet
    encryption is used, the signature can be generated on the output directly.
    The message **must** be encrypted with a secret key shared only by the user
    and the recipient, as it will otherwise be accessible by anyone who knows
    the recipient's public key. The response will contain the timestamp at
    which the message was successfully stored on the server and a unique
    16-byte hexadecimal identifier for the message.
    """
    message_data = await operations.create_message(engine, request)
    response = PostMessageResponseModel.model_validate({
        'status': 'success',
        'message': 'Message successfully posted.',
        'data': {
            'timestamp': message_data.timestamp,
            'nonce': message_data.nonce,
        },
    })
    return response

@app.post("/data/post/exchange-key", status_code=201)
async def post_exchange_key(
    request: PostExchangeKeyRequestModel,
) -> PostExchangeKeyResponseModel:
    """
    Post an exchange key to the server.

    This request requires the user's public key, a public key belonging to
    the intended recipient, the public key from an ephemeral 32-byte key pair,
    and a signature generated from the user's private key being used on the
    raw bytes of the ephemeral public key. If this is being sent after
    receiving another ephemeral public key, it should also include that key,
    and the user is free to derive the shared secret value locally after
    a successful request. The response will contain the timestamp at which the
    key was successfully stored on the server.
    """
    exchange_key_data = await operations.create_exchange_key(engine, request)
    response = PostExchangeKeyResponseModel.model_validate({
        'status': 'success',
        'message': 'Exchange key successfully posted.',
        'data': {
            'timestamp': exchange_key_data.timestamp,
        },
    })
    return response