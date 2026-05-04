
import sqlite3
import os
from pathlib import Path

db_path = Path.home() / "POSSystem" / "pos_data.db"
print(f"Checking DB at: {db_path}")

if not os.path.exists(db_path):
    print(f"DB not found!")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.execute("SELECT * FROM platforms")
rows = cursor.fetchall()
import sys
for row in rows:
    try:
        print(f"ID: {row['id']}, Name: {row['name']}, Type: {row['type']}, Active: {row['is_active']}")
    except:
        print(f"ID: {row['id']} (encoding error)")
conn.close()
