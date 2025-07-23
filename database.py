import sqlite3

DB_NAME = "orders.db"

# ===== СОЗДАНИЕ ТАБЛИЦЫ =====
def create_tables():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            product TEXT,
            color TEXT,
            address TEXT,
            paid INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

# ===== ДОБАВИТЬ ЗАКАЗ =====
def add_order(user_id, username, product, color, address, paid=False):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO orders (user_id, username, product, color, address, paid)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, username, product, color, address, int(paid)))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

# ===== ПОЛУЧИТЬ ВСЕ ЗАКАЗЫ ПОЛЬЗОВАТЕЛЯ =====
def get_user_orders(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT product, color, address, paid FROM orders WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [{"product": r[0], "color": r[1], "address": r[2], "paid": bool(r[3])} for r in rows]

# ===== ПОЛУЧИТЬ ЗАКАЗ ПО ID =====
def get_user_orders_by_id(order_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, username, product, color, address, paid FROM orders WHERE id = ?", (order_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "user_id": row[0],
            "username": row[1],
            "product": row[2],
            "color": row[3],
            "address": row[4],
            "paid": bool(row[5])
        }
    return None
