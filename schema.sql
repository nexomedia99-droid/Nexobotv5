import sqlite3
import os

DB_PATH = "data.db"

def init_db():
    first_setup = not os.path.exists(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    if first_setup:
        with open("schema.sql", "r") as f:
            conn.executescript(f.read())
        print("[DB] Database baru dibuat dengan schema.sql")
    return conn
