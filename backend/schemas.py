from pydantic import BaseModel, Field
from typing import Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

class Event(BaseModel):
    # 1. UUID: Ensures every event has a globally unique ID. 
    # default_factory=uuid4 means "if the user doesn't send an ID, generate one automatically".
    event_id: UUID = Field(default_factory=uuid4, description="Unique identifier for the event")

    # 2. Source: Where did this event come from?
    # example="payment_service" helps generate the documentation automatically.
    source: str = Field(..., description="The name of the service sending the event", example="payment_gateway")

    # 3. Payload: The actual data. We use Dict[str, Any] because the payload could be anything (flexible).
    payload: Dict[str, Any] = Field(..., description="The actual data of the event", example={"amount": 100, "currency": "USD"})

    # 4. Timestamp: When did this happen? Defaults to the current time (UTC) if not provided.
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the event creation")

    class Config:
        # This little nested class tells Swagger UI how to show a 'fake' example to the user
        json_schema_extra = {
            "example": {
                "source": "user_service",
                "payload": {"user_id": 123, "action": "login"},
                "created_at": "2024-01-01T12:00:00Z"
            }
        }