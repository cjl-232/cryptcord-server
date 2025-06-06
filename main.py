#TODO move config file (yaml form?) into a settings pydantic model to reference
# Reference it by importing it from a file?

import os

from contextlib import asynccontextmanager

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from connections.schemas.requests import (
    PostExchangeKeyRequestModel,
    PostMessageRequestModel,
    RetrievalRequestModel,
)
from connections.schemas.responses import (
    PostDataResponseModel,
    RetrieveExchangeKeysResponseModel,
    RetrieveMessagesResponseModel,
)
from database import operations
from database.models import Base

# Set key constants.
MAX_PLAINTEXT_LENGTH = 2000
MAX_CIPHERTEXT_LENGTH = len(
    Fernet(Fernet.generate_key()).encrypt(
        bytes(MAX_PLAINTEXT_LENGTH),
    ),
)

# Load environment variables and use them to create the engine object.
load_dotenv()
URL = (
    f'postgresql+asyncpg://'
    f'{os.environ['DB_USERNAME']}:{os.environ['DB_PASSWORD']}'
    f'@{os.environ['HOST']}:{os.environ['PORT']}/{os.environ['DB_NAME']}'
)
engine = create_async_engine(URL)

@asynccontextmanager
async def lifespan(_: FastAPI):
    """Creates database tables on application startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    return

app = FastAPI(
    #dependencies=[Depends(verify_user_key)],
    lifespan=lifespan,
)

@app.post("/messages/send")
async def post_message(
    request: PostMessageRequestModel,
) -> PostDataResponseModel:
    """
    Post an encrypted message to the server.

    This request requires the user's public key, a public key belonging to
    the intended recipient, the encrypted text itself, and a signature
    generated from the user's private key being used on the encrypted text.
    The message **must** be encrypted with a secret key shared only by the user
    and the recipient, as it will otherwise be accessible by anyone who knows
    the recipient's public key. The response will contain the timestamp at
    which the message was successfully stored on the server, and a unique
    16-byte hexadecimal identifier for the message.
    """
    message_data = await operations.create_message(engine, request)
    response = PostDataResponseModel.model_validate({
        'status': 'success',
        'message': 'Message successfully posted.',
        'data': {
            'timestamp': message_data.timestamp,
            'nonce': message_data.nonce,
        },
    })
    return response

@app.post("/messages/retrieve")
async def retrieve_messages(
    request: RetrievalRequestModel,
) -> RetrieveMessagesResponseModel:
    """
    Retrieve encrypted messages stored on the server.

    This request requires the user's public key, and will retrieve all messages
    stored on the server that are addressed to that public key. To limit the
    size of responses, the user may optionally provide a 'whitelist' of
    public keys, retrieving only messages from one of these, or a minimum
    datetime for the message's timestamp, retrieving only messages sent at or
    after this datetime. The response will contain a list of messages, each
    with the sender's public key, the encrypted text, a signature that should
    be used to verify the authenticity of the message, the timestamp at which
    it was stored on the server, and a unique 16-byte hexadecimal identifier
    for the message.
    """
    messages = await operations.retrieve_messages(engine, request)
    response = RetrieveMessagesResponseModel.model_validate({
        'status': 'success',
        'message': f'{len(messages)} messages retrieved.',
        'data': {
            'messages': messages,
        },
    })
    return response

@app.post("/exchange_keys/send")
async def post_exchange_key(
    request: PostExchangeKeyRequestModel,
) -> PostDataResponseModel:
    """
    Post an exchange key to the server.

    This request requires the user's public key, a public key belonging to
    the intended recipient, the public key from an ephemeral 32-byte key pair,
    and a signature generated from the user's private key being used on the 
    raw bytes of the ephemeral public key. Once retrieved by the recipient,
    they can generate their own ephemeral key pair and transmit the public key.
    Once the initial sender retrieves the recipent's ephemeral public key,
    both parties will be able to derive a shared secret value by combining
    their own ephmeral private key with their counterpart's ephemeral public
    key.
    """
    exchange_key_data = await operations.create_exchange_key(engine, request)
    response = PostDataResponseModel.model_validate({
        'status': 'success',
        'message': 'Exchange key successfully posted.',
        'data': {
            'timestamp': exchange_key_data.timestamp,
            'nonce': exchange_key_data.nonce,
        },
    })
    return response

@app.post("/exchange_keys/retrieve")
async def retrieve_exchange_keys(
    request: RetrievalRequestModel,
) -> RetrieveExchangeKeysResponseModel:
    """
    Retrieve ephemeral keys stored on the server.

    This request requires the user's public key, and will retrieve all
    ephemeral keys stored on the server that are addressed to that public key.
    To limit the size of responses, the user may optionally provide a
    'whitelist' of public keys, retrieving only messages from one of these, or
    a minimum datetime for the message's timestamp, retrieving only messages
    sent at or after this datetime. The response will contain a list of
    ephemeral keys, each with the sender's public key, the ephemeral key
    itself, a signature that **must** be used to verify the authenticity of
    the key, message, the timestamp at which it was stored on the server, and
    a unique 16-byte hexadecimal identifier for the ephemeral key.
    """
    exchange_keys = await operations.retrieve_exchange_keys(engine, request)
    response = RetrieveExchangeKeysResponseModel.model_validate({
        'status': 'success',
        'message': f'{len(exchange_keys)} keys retrieved.',
        'data': {
            'exchange_keys': exchange_keys,
        },
    })
    return response