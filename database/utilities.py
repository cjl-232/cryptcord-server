from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

async def get_user_id(session: AsyncSession, public_key: str) -> int:
    statement = select(User).where(User.public_key == public_key)
    statement = select(User).where(User.public_key == public_key)
    result = await session.execute(statement)
    user = result.scalar_one_or_none()
    if user is None:
        user = User(public_key=public_key)
        session.add(user)
        await session.commit()
    result = await session.execute(statement)
    user = result.scalar_one()
    return user.id