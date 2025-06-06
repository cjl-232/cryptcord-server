# VALIDATE KEYS AND SIGNATURES HERE

import binascii
import os

from base64 import urlsafe_b64decode, urlsafe_b64encode
from contextlib import asynccontextmanager
from datetime import datetime
from secrets import token_bytes
from typing import Annotated, Any

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import AfterValidator, BaseModel, Field
from sqlalchemy.ext.asyncio import create_async_engine

from connections.schemas.requests import (
    PostMessageRequestModel,
    RetrieveMessagesRequestModel,
)
from connections.schemas.responses import (
    RetrieveMessagesResponseModel,
    PostMessageResponseModel,
)
from database import operations
from database.models import Base

def is_base64(value: str) -> str:
    try:
        return urlsafe_b64encode(urlsafe_b64decode(value)).decode()
    except binascii.Error:
        raise ValueError('String is not valid Base64')


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

# Define the base models used to create endpoint-specific body models.
class PublicKeyModel(BaseModel):
    public_key: Annotated[
        str,
        Field(
            description=(
                'A url-safe Base64 representation of a 32-byte value. This '
                'should correspond to a Ed25519 public key owned by the '
                'sender of the request.'
            ),
            examples=[urlsafe_b64encode(token_bytes(32))],
            max_length=44,
            min_length=44,
        ),
        AfterValidator(is_base64),
    ]
class RecipientPublicKeyModel(BaseModel):
    recipient_public_key: Annotated[
        str,
        Field(
            description=(
                'A url-safe Base64 representation of a 32-byte value. This '
                'should correspond to a Ed25519 public key owned by the '
                'desired recipient.'
            ),
            examples=[urlsafe_b64encode(token_bytes(32))],
            max_length=44,
            min_length=44,
        ),
        AfterValidator(is_base64),
    ]


# Define the model for all responses.
class Response(BaseModel):
    status: str
    message: str | None = None
    data: Any = None




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


class OutboundMessageModel(PublicKeyModel, RecipientPublicKeyModel):
    encrypted_text: Annotated[
        str,
        Field(
            description=(
                f'A Fernet token produced from encrypting plaintext of up to '
                f'{MAX_PLAINTEXT_LENGTH} characters.'
            ),
            max_length=MAX_CIPHERTEXT_LENGTH,
            examples=[urlsafe_b64encode(b'Lorem ipsum dolor sit amet...')],
        ),
    ]
    signature: Annotated[
        str,
        Field(
            description=(
                'A url-safe Base64 representation of a 64-byte value. This '
                'should correspond to a signature produced from the sender '
                'signing the Fernet token with an Ed25519 private key.'
            ),
            max_length=88,
            min_length=88,
            examples=[urlsafe_b64encode(token_bytes(64))],
        ),
        AfterValidator(is_base64),
    ]

@app.post("/messages/send")
async def post_message(request: PostMessageRequestModel):
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
    response = PostMessageResponseModel.model_validate({
        'status': 'success',
        'message': 'Message successfully posted.',
        'data': {
            'timestamp': message_data.timestamp,
            'nonce': message_data.nonce,
        },
    })
    return response

@app.post("/messages/retrieve")
async def retrieve_messages(request: RetrieveMessagesRequestModel):
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

class OutboundKeyExchange(PublicKeyModel, RecipientPublicKeyModel):
    x25519_public_key: Annotated[
        str,
        Field(
            description=(
                'A url-safe Base64 representation of a 32-byte value. This '
                'should correspond to the public key of an X25519 key pair '
                'generated by the sender of the request.'
            ),
            max_length=44,
            min_length=44,
            examples=[urlsafe_b64encode(token_bytes(32))],
        ),
        AfterValidator(is_base64),
    ]
    signature: Annotated[
        str,
        Field(
            description=(
                'A url-safe Base64 representation of a 64-byte value. This '
                'should correspond to a signature produced from the sender '
                'signing the raw X25519 key bytes with an Ed25519 private key.'
            ),
            max_length=88,
            min_length=88,
            examples=[urlsafe_b64encode(token_bytes(64))],
        ),
        AfterValidator(is_base64),
    ]

@app.post("/key_exchanges/send")
async def post_key_exchange(key_exchange: OutboundKeyExchange):
    posted_key_exchange = await operations.create_key_exchange(
        engine=engine,
        x25519_public_key=key_exchange.x25519_public_key,
        signature=key_exchange.signature,
        sender_key=key_exchange.public_key,
        recipient_key=key_exchange.recipient_public_key,
    )
    return Response(
        status='success',
        message='Key sent successfully.',
        data={
            'key_exchange_timestamp': posted_key_exchange.timestamp,
        }
    )

class InboundKeyExchangesModel(PublicKeyModel):
    contact_keys: Annotated[
        list[str] | None,
        Field(
            description=(
                'A list of keys belonging to users the requester is willing '
                'to accept messages and key exchanges from.'
            ),
            default=None,
        )
    ]
    min_datetime: Annotated[
        datetime | None,
        Field(
            description=(
                'An optional datetime that filters out key exchanges posted '
                'any earlier than the supplied value. This is intended to '
                'avoid unneccessarily repeating retrievals.'
            ),
            default=None,
        ),
    ]

@app.post("/key_exchanges/retrieve")
async def retrieve_key_exchanges(request: InboundKeyExchangesModel):
    retrieved_key_exchanges = await operations.get_key_exchanges(
        engine=engine,
        recipient_key=request.public_key,
        contact_keys=request.contact_keys,
        min_datetime=request.min_datetime,
    )
    return Response(
        status='success',
        message=f'{len(retrieved_key_exchanges)} key exchanges retrieved.',
        data={
            'key_exchanges': retrieved_key_exchanges,
        }
    )

@app.post("/")
async def read_root1(body: PublicKeyModel):
    # print(body.public_key)
    # print(type(body.public_key))
    return {
        'value': str(body.public_key),
        'type': str(type(body.public_key)),
        "Hello": "World"
    }

# @app.post("/")
# async def read_root():
#     return {"Hello": "World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: bytes | None = None) -> dict[str, Any]:
    return {"item_id": item_id, "q": q}

