from datetime import datetime
from typing import Any, Self

from pydantic import BaseModel, Field, model_validator

from microsave_app.models.payload_registery import PAYLOAD_MODELS


class SaveEnvelope(BaseModel):
    client_app_id: str
    user_id: str
    save_slot: str
    schema_version: int = Field(ge=1)
    payload: dict[str, Any]

    @model_validator(mode='after')
    def check_payload_for_app(self) -> Self:
        payload_model: BaseModel = PAYLOAD_MODELS.get(self.client_app_id)
        if payload_model is None:
            raise ValueError(f"Unsupported client app id: {self.client_app_id}")
        
        validated_payload: BaseModel = payload_model.model_validate(self.payload)
        self.payload = validated_payload.model_dump()

        return self


class SaveDocument(SaveEnvelope):
    created_at: datetime
    updated_at: datetime


class SaveResponse(BaseModel):
    client_app_id: str
    user_id: str
    save_slot: str
    schema_version: int
    updated_at: datetime
    payload: dict[str, Any]
