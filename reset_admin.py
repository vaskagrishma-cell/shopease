from database import get_connection
from werkzeug.security import generate_password_hash

email = "jeshu@gmail.com"
password = input("Enter new admin password: ")

con = get_connection()
cur = con.cursor()

cur.execute(
    "UPDATE users SET password=%s, role='admin' WHERE email=%s",
    (generate_password_hash(password), email)
)

con.commit()

print("Admin updated!" if cur.rowcount > 0 else "Admin account not found!")

cur.close()
con.close()