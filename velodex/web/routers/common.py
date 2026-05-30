from typing import Iterable, Optional

from pydantic import BaseModel


class RiderFields(BaseModel):
    """Rider attributes shared by the riders and overrides schemas."""

    source: Optional[str] = None
    source_url: Optional[str] = None
    name: Optional[str] = None
    nationality: Optional[str] = None
    birth_date: Optional[str] = None
    sanctions: Optional[str] = None
    team: Optional[str] = None
    instagram: Optional[str] = None
    notes: Optional[str] = None


def row_to_dict(columns: list[str], row, date_keys: Iterable[str]) -> dict:
    """Zip a DB row into a dict, converting the given datetime columns to ISO."""
    d = dict(zip(columns, row))
    for key in date_keys:
        if d.get(key) is not None:
            d[key] = d[key].isoformat()
    return d
