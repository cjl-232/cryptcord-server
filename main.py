# VALIDATE KEYS AND SIGNATURES HERE

import os

from base64 import b64decode, b64encode, urlsafe_b64decode, urlsafe_b64encode
from contextlib import asynccontextmanager
from typing import Annotated, Any

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import AfterValidator, BaseModel, Field, StringConstraints
from sqlalchemy.ext.asyncio import create_async_engine

from database.operations import create_message
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

class OutgoingMessage(BaseRequestModel):
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
        )
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
        )
    ]


@app.post("/messages/send")
async def post_message(message: OutgoingMessage):
    posted_message = await create_message(
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
            'timestamp': posted_message.timestamp,
        }
    )

    return {
        'sender': sender_id,
        'recipient': recipient_id,
    }

#app = FastAPI()

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

