"""
Data structures for interaction via REST API.
"""

from datetime import datetime
from pydantic import BaseModel, Field, computed_field
from uuid import UUID, uuid4


class ExtBaseModel(BaseModel):
    """
    Need to construct models from tuples.
    """

    @classmethod
    def from_tuple(cls, data_tuple: tuple):
        field_names = cls.model_fields.keys()
        return cls(**dict(zip(field_names, data_tuple)))


class PTZRecord(ExtBaseModel):
    """
    Record contains pan, tilt and zoom from the client.
    """

    pan: int
    tilt: int
    zoom: int


class Focus(ExtBaseModel):
    """
    Focus automatic flag and focus value.
    """

    auto: bool
    value: int | None


class Direction(ExtBaseModel):
    """
    Geographic direction (N, E, W, SW, C, etc.) and coordinates.
    """

    direction: str
    x: int | None
    y: int | None


class ServerEventData(BaseModel):
    @computed_field
    @property
    def event_type(self) -> str:
        return str(self.payload.__class__.__name__)

    timestamp: datetime = Field(default=datetime.now())
    payload: PTZRecord | Focus | Direction | str | None


class ServerEvent(ExtBaseModel):
    """
    Server event structure.

    @warning: field names are fixed!
    """

    event: str = Field(default='state_changed', freeze=True)

    id: UUID = Field(default_factory=uuid4)
    data: ServerEventData
