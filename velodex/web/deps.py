from velodex.db import connect


def get_db():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
