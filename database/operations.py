from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from connections.schemas.requests import (
    PostMessageRequestModel,
    RetrieveMessagesRequestModel,
)
from database.models import EncryptedMessage, KeyExchange, User
from database.schemas.output import (
    CreatedMessageOutputSchema,
    MessageOutputSchema,
    UserOutputSchema,
)

async def get_or_create_user(
        engine: AsyncEngine,
        public_key: str,
    ) -> UserOutputSchema:
    """Retrieves or creates a user for the supplied public key."""
    statement = select(User).where(User.public_key == public_key)
    async with AsyncSession(engine) as session:
        statement = select(User).where(User.public_key == public_key)
        user = await session.scalar(statement)
        if user is None:
            user = User(public_key=public_key)
            session.add(user)
            try:
                await session.commit()
            except IntegrityError:
                await session.rollback()
            result = await session.scalars(statement)
            user = result.one()
        return UserOutputSchema.model_validate(user)
    
async def create_message(
        engine: AsyncEngine,
        request: PostMessageRequestModel,
    ) -> CreatedMessageOutputSchema:
    sender = await get_or_create_user(engine, request.public_key)
    recipient = await get_or_create_user(engine, request.recipient_public_key)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        message = EncryptedMessage(
            encrypted_text=request.encrypted_text,
            signature=request.signature,
            sender_id=sender.id,
            recipient_id=recipient.id,
        )
        session.add(message)
        await session.commit()
        return CreatedMessageOutputSchema.model_validate(message)
    
async def retrieve_messages(
        engine: AsyncEngine,
        request: RetrieveMessagesRequestModel,
    ) -> list[MessageOutputSchema]:
    # Retrieve the requesting user.
    user = await get_or_create_user(engine, request.public_key)

    # Construct the statement to execute.
    statement = select(
        EncryptedMessage,
    ).where(
        EncryptedMessage.recipient_id == user.id,
    )
    if request.sender_keys is not None:
        statement = statement.where(
            EncryptedMessage.sender_id.in_(request.sender_keys),
        )
    if request.min_datetime is not None:
        statement = statement.where(
            EncryptedMessage.timestamp >= request.min_datetime,
        )
    statement = statement.order_by(EncryptedMessage.timestamp)

    # Execute the statement and retrieve the results.
    async with AsyncSession(engine) as session:
        messages = [
            MessageOutputSchema.model_validate(message)
            for message in await session.scalars(statement)
        ]
        return messages

# async def get_messages(
#         engine: AsyncEngine,
#         recipient_key: str,
#         contact_keys: list[str] | None = None,
#         min_datetime: datetime | None = None,
#     ) -> list[dict[str, Any]]:
#     user = await get_or_create_user(engine, recipient_key)
#     statement = select(EncryptedMessage)
#     statement = statement.where(EncryptedMessage.recipient_id == user.id)
#     if contact_keys:
#         statement = statement.where(
#             EncryptedMessage.sender_id.in_(contact_keys),
#         )
#     if min_datetime is not None:
#         statement = statement.where(EncryptedMessage.timestamp >= min_datetime)
#     statement = statement.order_by(EncryptedMessage.timestamp)
#     async with AsyncSession(engine) as session:
#         messages = await session.scalars(statement)
#         result: list[dict[str, Any]] = [
#             {
#                 'sender_key': message.sender.public_key,
#                 'encrypted_text': message.encrypted_text,
#                 'signature': message.signature,
#                 'timestamp': message.timestamp,
#                 'nonce': message.id,
#             }
#             for message in messages
#         ]
#         return result

async def create_key_exchange(
        engine: AsyncEngine,
        x25519_public_key: str,
        signature: str,
        sender_key: str,
        recipient_key: str,
    ) -> KeyExchange:
    sender = await get_or_create_user(engine, sender_key)
    recipient = await get_or_create_user(engine, recipient_key)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        key_exchange = KeyExchange(
            x25519_public_key=x25519_public_key,
            signature=signature,
            sender_id=sender.id,
            recipient_id=recipient.id,
        )
        session.add(key_exchange)
        await session.commit()
        return key_exchange

async def get_key_exchanges(
        engine: AsyncEngine,
        recipient_key: str,
        contact_keys: list[str] | None = None,
        min_datetime: datetime | None = None,
    ) -> list[dict[str, Any]]:
    user = await get_or_create_user(engine, recipient_key)
    statement = select(KeyExchange)
    statement = statement.where(KeyExchange.recipient_id == user.id)
    if contact_keys:
        statement = statement.where(
            EncryptedMessage.sender_id.in_(contact_keys),
        )
    if min_datetime is not None:
        statement = statement.where(KeyExchange.timestamp >= min_datetime)
    async with AsyncSession(engine) as session:
        messages = await session.scalars(statement)
        result: list[dict[str, Any]] = [
            {
                'sender_key': message.sender.public_key,
                'x25519_public_key': message.x25519_public_key,
                'signature': message.signature,
                'timestamp': message.timestamp,
            }
            for message in messages
        ]
        return result
