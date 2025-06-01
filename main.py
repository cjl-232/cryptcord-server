# VALIDATE KEYS AND SIGNATURES HERE

import binascii
import os

from base64 import b64decode, b64encode, urlsafe_b64decode, urlsafe_b64encode
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Any

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import AfterValidator, BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import create_async_engine

from database import operations
from database.models import Base

def is_base64(value: str) -> str:
    try:
        urlsafe_b64decode(value)
    except binascii.Error:
        raise ValueError('String is not valid Base64')
    return value


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

# Define the base model for all request bodies.
class BaseRequestModel(BaseModel):
    public_key: Annotated[
        str,
        Field(
            description=(
                'A Base64 representation of a 32-byte value. This should '
                'correspond to a Ed25519 public key owned by the sender of '
                'the request.'
            ),
            examples=[urlsafe_b64encode(b'abcd' * 8)],
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

class MessageRetrievalModel(BaseRequestModel):
    min_datetime: Annotated[
        datetime | None,
        Field(
            description=(
                'An optional datetime that filters out messages posted '
                'any earlier than the supplied value. This is intended to '
                'avoid unneccessarily repeating retrievals.'
            ),
            default=None,
        ),
    ]

@app.post("/messages/retrieve")
async def retrieve_messages(request: MessageRetrievalModel):
    retrieved_messages = await operations.get_messages(
        engine=engine,
        recipient_key=request.public_key,
        min_datetime=request.min_datetime,
    )
    return Response(
        status='success',
        message=f'{len(retrieved_messages)} messages retrieved.',
        data={
            'messages': retrieved_messages,
        }
    )


class OutgoingMessageModel(BaseRequestModel):
    recipient_public_key: Annotated[
        str,
        Field(
            description=(
                'A Base64 representation of a 32-byte value. This should '
                'correspond to a Ed25519 public key owned by the desired '
                'recipient of the message.'
            ),
            examples=[urlsafe_b64encode(b'efgh' * 8)],
            max_length=44,
            min_length=44,
        ),
        AfterValidator(is_base64),
    ]
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
                'A Base64 representation of a 64-byte value. This should '
                'correspond to signature produced from the sender signing the '
                'Fernet token with an Ed25519 private key.'
            ),
            max_length=88,
            min_length=88,
            examples=[urlsafe_b64encode(b'zyxwvuts' * 8)],
        ),
        AfterValidator(is_base64),
    ]

@app.post("/messages/send")
async def post_message(message: OutgoingMessageModel):
    posted_message = await operations.create_message(
        engine=engine,
        encrypted_text=message.encrypted_text,
        signature=message.signature,
        sender_key=message.public_key,
        recipient_key=message.recipient_public_key,
    )
    return Response(
        status='success',
        message='Message sent.',
        data={
            'message_timestamp': posted_message.timestamp,
        }
    )

@app.post("/")
async def read_root1(body: BaseRequestModel):
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

