"""Delete test accounts, keep ID=2 (zx) and ID=12 (z)."""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "health_system.db")
KEEP_IDS = {2, 12}
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT id, name FROM users WHERE id NOT IN (?, ?)", tuple(KEEP_IDS))
to_delete = c.fetchall()
print(f"即将删除 {len(to_delete)} 个账户:")
for uid, name in to_delete:
    print(f"  ID={uid}  {name}")

if not to_delete:
    print("无需删除")
    conn.close()
    exit()

delete_ids = [r[0] for r in to_delete]
placeholders = ",".join("?" * len(delete_ids))

# chat_messages depends on chat_sessions
c.execute(f"SELECT id FROM chat_sessions WHERE user_id IN ({placeholders})", delete_ids)
session_ids = [r[0] for r in c.fetchall()]
if session_ids:
    sp = ",".join("?" * len(session_ids))
    c.execute(f"DELETE FROM chat_messages WHERE session_id IN ({sp})", session_ids)
    print(f"  删除 chat_messages: {c.rowcount} 条")

tables = [
    "chat_sessions", "health_analyses", "health_warnings", "ai_analyses",
    "tongue_diagnoses", "user_food_records", "user_sport_records",
    "user_health_goals", "health_records",
]

for table in tables:
    c.execute(f"DELETE FROM {table} WHERE user_id IN ({placeholders})", delete_ids)
    if c.rowcount > 0:
        print(f"  删除 {table}: {c.rowcount} 条")

c.execute(f"DELETE FROM users WHERE id IN ({placeholders})", delete_ids)
print(f"  删除 users: {c.rowcount} 条")

conn.commit()

c.execute("SELECT id, name FROM users ORDER BY id")
remaining = c.fetchall()
print(f"\n剩余 {len(remaining)} 个账户:")
for uid, name in remaining:
    print(f"  ID={uid}  {name}")

conn.close()
print("\n完成")
