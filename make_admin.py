
from database import get_connection

con = get_connection()
cur = con.cursor()

cur.execute("SHOW COLUMNS FROM users LIKE 'role'")
column = cur.fetchone()

if not column:
    cur.execute(
        "ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"
    )

cur.execute(
    "UPDATE users SET role=%s WHERE email=%s",
    ('admin', 'jeshu@gmail.com')
)

con.commit()

cur.execute(
    "SELECT username, email, role FROM users WHERE email=%s",
    ('jeshu@gmail.com',)
)

print(cur.fetchone())

cur.close()
con.close()
