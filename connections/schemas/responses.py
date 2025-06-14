from pydantic import BaseModel

from database.schemas.output import (
    PostedMessageOutputSchema,
    PostedExchangeKeyOutputSchema,
    StoredExchangeKeyOutputSchema,
    StoredMessageOutputSchema,
)

class BaseResponseModel(BaseModel):
    status: str
    message: str

class _RetrieveMessagesResponseDataModel(BaseModel):
    """A list of messages to return on a retrieval request."""
    messages: list[StoredMessageOutputSchema]

class _RetrieveExchangeKeysResponseDataModel(BaseModel):
    """A list of exchange keys to return on a retrieval request."""
    exchange_keys: list[StoredExchangeKeyOutputSchema]

class PostMessageResponseModel(BaseResponseModel):
    data: PostedMessageOutputSchema

class PostExchangeKeyResponseModel(BaseResponseModel):
    data: PostedExchangeKeyOutputSchema

class RetrieveExchangeKeysResponseModel(BaseResponseModel):
    data: _RetrieveExchangeKeysResponseDataModel

class RetrieveMessagesResponseModel(BaseResponseModel):
    data: _RetrieveMessagesResponseDataModel