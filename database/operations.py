from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from connections.schemas.requests import (
    PostExchangeKeyRequestModel,
    PostMessageRequestModel,
    RetrievalRequestModel,
)
from database.models import Message, ExchangeKey, User
from database.schemas.output import (
    PostedDataOutputSchema,
    StoredExchangeKeyOutputSchema,
    StoredMessageOutputSchema,
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
    ) -> PostedDataOutputSchema:
    sender = await get_or_create_user(engine, request.public_key)
    recipient = await get_or_create_user(engine, request.recipient_public_key)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        message = Message(
            encrypted_text=request.encrypted_text,
            signature=request.signature,
            sender_id=sender.id,
            recipient_id=recipient.id,
        )
        session.add(message)
        await session.commit()
        return PostedDataOutputSchema.model_validate(message)
    
async def retrieve_messages(
        engine: AsyncEngine,
        request: RetrievalRequestModel,
    ) -> list[StoredMessageOutputSchema]:
    # Retrieve the requesting user.
    user = await get_or_create_user(engine, request.public_key)

    # Construct the statement to execute.
    statement = select(Message).where(Message.recipient_id == user.id)
    if request.sender_keys is not None:
        statement = statement.join(
            Message.sender,
        ).where(
            User.public_key.in_(request.sender_keys),
        )
    if request.min_datetime is not None:
        statement = statement.where(
            Message.timestamp >= request.min_datetime,
        )
    statement = statement.order_by(Message.timestamp)

    # Execute the statement and retrieve the results.
    async with AsyncSession(engine) as session:
        messages = [
            StoredMessageOutputSchema.model_validate(message)
            for message in await session.scalars(statement)
        ]
        return messages
    
async def create_exchange_key(
        engine: AsyncEngine,
        request: PostExchangeKeyRequestModel,
    ) -> PostedDataOutputSchema:
    sender = await get_or_create_user(engine, request.public_key)
    recipient = await get_or_create_user(engine, request.recipient_public_key)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        exchange_key = ExchangeKey(
            key=request.exchange_key,
            signature=request.signature,
            sender_id=sender.id,
            recipient_id=recipient.id,
        )
        session.add(exchange_key)
        await session.commit()
        return PostedDataOutputSchema.model_validate(exchange_key)
    
async def retrieve_exchange_keys(
        engine: AsyncEngine,
        request: RetrievalRequestModel,
    ) -> list[StoredExchangeKeyOutputSchema]:
    # Retrieve the requesting user.
    user = await get_or_create_user(engine, request.public_key)

    # Construct the statement to execute.
    statement = select(ExchangeKey).where(ExchangeKey.recipient_id == user.id)
    if request.sender_keys is not None:
        statement = statement.join(
            ExchangeKey.sender,
        ).where(
            User.public_key.in_(request.sender_keys),
        )
    if request.min_datetime is not None:
        statement = statement.where(
            ExchangeKey.timestamp >= request.min_datetime,
        )
    statement = statement.order_by(ExchangeKey.timestamp)

    # Execute the statement and retrieve the results.
    async with AsyncSession(engine) as session:
        exchange_keys = [
            StoredExchangeKeyOutputSchema.model_validate(exchange_key)
            for exchange_key in await session.scalars(statement)
        ]
        return exchange_keys