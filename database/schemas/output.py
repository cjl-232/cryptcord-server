from datetime import datetime

from pydantic import BaseModel, ConfigDict

class CreatedMessageOutputSchema(BaseModel):
    """A schema to retrieve metadata after posting a message."""
    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime
    nonce: str

class MessageOutputSchema(BaseModel):
    """A schema used when retrieving message instances."""
    model_config = ConfigDict(from_attributes=True)

    sender_key: str
    encrypted_text: str
    signature: str
    timestamp: datetime
    nonce: str

class UserOutputSchema(BaseModel):
    """A schema used when retrieving user instances."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    public_key: str