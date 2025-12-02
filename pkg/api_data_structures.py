"""
Data structures for interaction via REST API.
"""

from pydantic import BaseModel


class PTZRecord(BaseModel):
    """
    Record contains pan, tilt and zoom from the client.
    """

    pan: int
    tilt: int
    zoom: int


class Focus(BaseModel):
    """
    Focus automatic flag and focus value.
    """

    auto: bool
    value: int | None


class Direction(BaseModel):
    """
    Geographic direction (N, E, W, SW, C, etc.) and coordinates.
    """

    direction: str
    x: int | None
    y: int | None
