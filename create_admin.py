from database.db import get_db_connection
from werkzeug.security import generate_password_hash


# =========================
# ADMIN DETAILS (from environment variables)
# =========================

import os

fullname = os.getenv("ADMIN_FULLNAME", "Admin")

email = os.getenv("ADMIN_EMAIL")

password = os.getenv("ADMIN_PASSWORD")

if not email or not password:
    raise SystemExit(
        "ADMIN_EMAIL and ADMIN_PASSWORD must be set in .env "
        "(see .env.example) before creating an admin."
    )


# =========================
# DATABASE CONNECTION
# =========================

connection = get_db_connection()
cursor = connection.cursor()


# =========================
# CHECK EXISTING ADMIN
# =========================

cursor.execute(
    """
    SELECT id
    FROM admins
    WHERE email = ?
    """,
    (email,)
)

existing_admin = cursor.fetchone()


if existing_admin:

    print("Admin already exists!")

else:

    # Hash Password
    hashed_password = generate_password_hash(password)

    # Insert Admin
    cursor.execute(
        """
        INSERT INTO admins
        (fullname, email, password)
        VALUES (?, ?, ?)
        """,
        (
            fullname,
            email,
            hashed_password
        )
    )

    connection.commit()

    print("Admin created successfully!")
    print("Email:", email)


connection.close()