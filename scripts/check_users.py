"""Quick script to check registered users."""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "health_system.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM users")
total = c.fetchone()[0]
print(f"总注册账户: {total}\n")

c.execute("SELECT id, name, created_at, is_active FROM users ORDER BY id")
for r in c.fetchall():
    status = "活跃" if r[3] else "禁用"
    print(f"  ID={r[0]}  用户名={r[1]}  注册时间={r[2]}  状态={status}")

conn.close()
