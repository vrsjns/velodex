from typing import List, Optional

from fastapi import Depends, Security
from fastapi.routing import APIRouter

from velodex.web.auth import get_current_user
from velodex.web.deps import cookie_scheme, get_db
from velodex.web.routers.common import RiderFields, row_to_dict

router = APIRouter(prefix="/api", tags=["riders"])


class RiderOut(RiderFields):
    scraped_at: Optional[str] = None
    valid_from: Optional[str] = None


@router.get(
    "/riders",
    summary="List or search riders",
    response_model=List[RiderOut],
    dependencies=[Security(cookie_scheme), Depends(get_current_user)],
)
def api_riders(q: str = "", conn=Depends(get_db)):
    with conn.cursor() as cur:
        if q:
            cur.execute(
                """SELECT source, source_url, name, nationality, birth_date,
                          sanctions, team, instagram, notes, scraped_at, valid_from
                   FROM riders_current
                   WHERE name ILIKE %s
                   ORDER BY name""",
                (f"%{q}%",),
            )
        else:
            cur.execute(
                """SELECT source, source_url, name, nationality, birth_date,
                          sanctions, team, instagram, notes, scraped_at, valid_from
                   FROM riders_current
                   ORDER BY name"""
            )
        columns = [desc[0] for desc in cur.description]
        rows = [
            row_to_dict(columns, row, ("scraped_at", "valid_from"))
            for row in cur.fetchall()
        ]
    return rows
