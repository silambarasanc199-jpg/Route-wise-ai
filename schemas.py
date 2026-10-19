"""Request and response validation."""
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class Priority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"

class DeliveryStatus(str, Enum):
    pending = "pending"
    in_transit = "in_transit"
    completed = "completed"
    delayed = "delayed"

ShortText = Annotated[str, Field(min_length=1, max_length=160)]
AddressText = Annotated[str, Field(min_length=4, max_length=500)]

class DeliveryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    order_id: Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")]
    customer_name: ShortText
    address: AddressText
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    priority: Priority
    deadline: datetime
    status: DeliveryStatus = DeliveryStatus.pending

    @field_validator("deadline")
    @classmethod
    def normalize_deadline(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

class DeliveryPatch(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    order_id: Annotated[str, Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")] | None = None
    customer_name: ShortText | None = None
    address: AddressText | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(default=None, ge=-180, le=180, allow_inf_nan=False)
    priority: Priority | None = None
    deadline: datetime | None = None
    status: DeliveryStatus | None = None

    @field_validator("deadline")
    @classmethod
    def normalize_deadline(cls, value: datetime | None) -> datetime | None:
        if value is None: return value
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def require_fields(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Updated fields cannot be null")
        return self

class StatusUpdate(BaseModel):
    status: DeliveryStatus

class ProofInput(BaseModel):
    secure_url: str = Field(min_length=1, max_length=2000)
    public_id: str = Field(min_length=1, max_length=500)

class DeliveryOut(BaseModel):
    id: str
    order_id: str
    customer_name: str
    address: str
    latitude: float
    longitude: float
    priority: Priority
    deadline: datetime
    status: DeliveryStatus
    created_at: datetime
    updated_at: datetime

class HistoryOut(BaseModel):
    id: int
    event_type: str
    old_value: str | None
    new_value: str
    created_at: datetime

class ProofOut(BaseModel):
    id: int
    secure_url: str
    public_id: str
    created_at: datetime

class Depot(BaseModel):
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    label: str = Field(default="Depot", max_length=120)

class RouteRequest(BaseModel):
    depot: Depot
    delivery_ids: list[str] = Field(min_length=1, max_length=100)

class GeocodeResult(BaseModel):
    latitude: float
    longitude: float
    display_name: str
