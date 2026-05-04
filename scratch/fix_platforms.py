
import sqlite3
from pathlib import Path

db_path = Path.home() / "POSSystem" / "pos_data.db"
print(f"Connecting to {db_path}")

try:
    conn = sqlite3.connect(db_path)
    # Fix existing inactive platforms that might conflict
    # Renaming them by appending their ID
    conn.execute("UPDATE platforms SET name = name || ' (محذوف - ' || id || ')' WHERE is_active = 0 AND name NOT LIKE '%(محذوف%'")
    conn.commit()
    conn.close()
    print("Successfully fixed inactive platform names.")
except Exception as e:
    print(f"Error: {e}")
