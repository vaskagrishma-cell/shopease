
import mysql.connector
import os

MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")


def get_connection():
    return mysql.connector.connect(
        host="mysql-3ca8c7d8-vaskagrishma-2cf8.j.aivencloud.com",
        port=17911,
        user="shopease_app",
        password=MYSQL_PASSWORD,
        database="defaultdb",
        ssl_disabled=False
    )


def create_tables():
    con = get_connection()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100),
        email VARCHAR(100) UNIQUE,
        password VARCHAR(255),
        role VARCHAR(20) DEFAULT 'user'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(150),
        description TEXT,
        price DECIMAL(10,2),
        image VARCHAR(255),
        stock INT DEFAULT 0,
        category VARCHAR(100) DEFAULT 'Other'
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT,
        total DECIMAL(10,2),
        status VARCHAR(50) DEFAULT 'Placed',
        order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        order_id INT,
        product_id INT,
        quantity INT,
        price DECIMAL(10,2),
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)

    cur.execute("""
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'products'
    AND COLUMN_NAME = 'category'
    """)

    category_exists = cur.fetchone()[0]

    if not category_exists:
        cur.execute("""
        ALTER TABLE products
        ADD COLUMN category VARCHAR(100) DEFAULT 'Other'
        """)

    con.commit()
    cur.close()
    con.close()
