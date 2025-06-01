from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from database.models import EncryptedMessage, User

async def get_user_id(engine: AsyncEngine, public_key: str) -> int:
    """Retrieves or creates a user id for the supplied public key."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        statement = select(User).where(User.public_key == public_key)
        result = await session.scalars(statement)
        user = result.one_or_none()
        if user is None:
            user = User(public_key=public_key)
            session.add(user)
            await session.commit()
        return user.id
    
async def create_message(
        engine: AsyncEngine,
        encrypted_text: str,
        signature: str,
        sender_key: str,
        recipient_key: str,
    ) -> EncryptedMessage:
    sender_id = await get_user_id(engine, sender_key)
    recipient_id = await get_user_id(engine, recipient_key)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        message = EncryptedMessage(
            encrypted_text=encrypted_text,
            signature=signature,
            sender_id=sender_id,
            recipient_id=recipient_id,
        )
        session.add(message)
        await session.commit()
        return message
