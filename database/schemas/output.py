from datetime import datetime

from pydantic import BaseModel, ConfigDict

class PostedDataOutputSchema(BaseModel):
    """A schema to store metadata after posting a message or exchange key."""
    model_config = ConfigDict(from_attributes=True)
    timestamp: datetime
    nonce: str

class StoredExchangeKeyOutputSchema(BaseModel):
    """A schema used when retrieving exchange keys."""
    model_config = ConfigDict(from_attributes=True)
    key: str
    signature: str
    sender_key: str
    timestamp: datetime
    nonce: str
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