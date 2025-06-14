from datetime import datetime

from pydantic import BaseModel, ConfigDict

class _PostedDataOutputSchema(BaseModel):
    timestamp: datetime
    class Config:
        from_attributes = True

class PostedMessageOutputSchema(_PostedDataOutputSchema):
    """A schema to store metadata after posting a message."""
    nonce: str

class PostedExchangeKeyOutputSchema(_PostedDataOutputSchema):
    """A schema to store metadata after posting an exchange key."""

class StoredExchangeKeyOutputSchema(BaseModel):
    """A schema used when retrieving exchange keys."""
    model_config = ConfigDict(from_attributes=True)
    key: str
    signature: str
    sender_key: str
    timestamp: datetime
    response_to: str | None

class StoredMessageOutputSchema(BaseModel):
    """A schema used when retrieving messages."""
    model_config = ConfigDict(from_attributes=True)
    encrypted_text: str
    signature: str
    sender_key: str
    timestamp: datetime
    nonce: str

class UserOutputSchema(BaseModel):
    """A schema used when retrieving user instances."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    public_key: str