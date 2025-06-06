from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict

from database.models import User

def _validate_user(user: User) -> str:
    return user.public_key

type _User = Annotated[
    str,
    BeforeValidator(_validate_user),
]

class CreatedMessageOutputSchema(BaseModel):
    """A schema to retrieve metadata after posting a message."""
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    nonce: str

class MessageOutputSchema(BaseModel):
    """A schema used when retrieving message instances."""
    model_config = ConfigDict(from_attributes=True)

    sender: _User
    encrypted_text: str
    signature: str
    timestamp: datetime
    nonce: str

class UserOutputSchema(BaseModel):
    """A schema used when retrieving user instances."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_key: str