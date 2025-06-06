from pydantic import BaseModel

from database.schemas.output import (
    CreatedMessageOutputSchema,
    MessageOutputSchema,
)

class BaseResponseModel(BaseModel):
    status: str
    message: str

class _RetrieveMessagesResponseDataModel(BaseModel):
    """A list of validated messages to return on a retrieval request."""
    messages: list[MessageOutputSchema]

class PostMessageResponseModel(BaseResponseModel):
    data: CreatedMessageOutputSchema

class RetrieveMessagesResponseModel(BaseResponseModel):
    data: _RetrieveMessagesResponseDataModel
