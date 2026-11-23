
from database import create_database, create_tables, get_connection
from werkzeug.security import generate_password_hash

create_database()
create_tables()

con = get_connection()
cur = con.cursor()

name = "Admin"
email = "admin@gmail.com"
password = generate_password_hash("Admin@123")

try:
    cur.execute("SELECT role FROM users WHERE email=%s", (email,))
    existing_user = cur.fetchone()

    if existing_user:
        if existing_user[0] == "admin":
            print("Admin account already exists; no changes made.")
        else:
            raise SystemExit(
                f"{email} is already registered as a non-admin user; no changes made."
            )
    else:
        cur.execute(
            "INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)",
            (name, email, password, "admin")
        )
        con.commit()
        print("Admin account created successfully!")
finally:
    cur.close()
    con.close()

