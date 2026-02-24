from fastapi.security import APIKeyCookie

from velodex.db import connect

cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)


def get_db():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
