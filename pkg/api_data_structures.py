"""
Data structures for interaction via REST API.
"""

from pydantic import BaseModel


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
