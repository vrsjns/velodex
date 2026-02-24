import logging
import os
import sys

from dotenv import load_dotenv
import uvicorn

from velodex.db import connect, run_migrations
from velodex.web.auth import create_user, get_user_by_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

load_dotenv()
run_migrations()

admin_email = os.environ.get("ADMIN_EMAIL")
admin_password = os.environ.get("ADMIN_PASSWORD")
if admin_email and admin_password:
    conn = connect()
    try:
        if not get_user_by_email(conn, admin_email):
            create_user(conn, admin_email, admin_password, role="admin")
            logging.info("Seeded admin user: %s", admin_email)
        else:
            logging.info("Admin user already exists: %s", admin_email)
    finally:
        conn.close()

if __name__ == "__main__":
    uvicorn.run("velodex.web.app:app", host="0.0.0.0", port=8000)
