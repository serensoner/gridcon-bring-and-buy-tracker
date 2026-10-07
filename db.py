import os
import sqlite3
import hashlib

def get_connection(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str):
    conn = get_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT UNIQUE NOT NULL,
                game_name TEXT,
                seller TEXT,
                price TEXT,
                first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_items INTEGER,
                new_items INTEGER,
                status TEXT,
                error_message TEXT
            )
        """)
    conn.close()

def is_db_empty(db_path: str) -> bool:
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM seen_entries")
    row = cursor.fetchone()
    conn.close()
    return row['cnt'] == 0

def compute_fingerprint(row_dict: dict) -> str:
    """
    Computes a deterministic fingerprint for a sheet row.
    We use core identifying fields: Timestamp, Game Name, Seller Name, Price, Contact.
    """
    keys = ["Timestamp", "What game are you selling?", "Your name", "Price", "Your contact details (phone number / email address)"]
    raw_str = "||".join(str(row_dict.get(k, "")).strip().lower() for k in keys)
    if raw_str == "||||||":
        # Fallback if dictionary keys differ
        raw_str = "||".join(str(v).strip().lower() for v in row_dict.values())
    return hashlib.sha256(raw_str.encode('utf-8')).hexdigest()

def process_entries(db_path: str, entries: list[dict], is_initial_seed: bool = False) -> list[dict]:
    """
    Checks entries against seen_entries table.
    Returns a list of NEW entries (additions).
    Saves new entries to the database.
    If is_initial_seed is True, records all current entries without treating them as new alerts.
    """
    init_db(db_path)
    conn = get_connection(db_path)
    new_entries = []

    with conn:
        for entry in entries:
            fp = compute_fingerprint(entry)
            game_name = entry.get("What game are you selling?") or entry.get("Game") or ""
            seller = entry.get("Your name") or entry.get("Seller") or ""
            price = entry.get("Price") or entry.get("Price (UKP)") or ""

            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM seen_entries WHERE fingerprint = ?", (fp,))
            exists = cursor.fetchone()

            if not exists:
                cursor.execute(
                    "INSERT INTO seen_entries (fingerprint, game_name, seller, price) VALUES (?, ?, ?, ?)",
                    (fp, game_name, seller, price)
                )
                if not is_initial_seed:
                    new_entries.append(entry)

    conn.close()
    return new_entries

def log_sync(db_path: str, total_items: int, new_items: int, status: str = "SUCCESS", error_message: str = ""):
    init_db(db_path)
    conn = get_connection(db_path)
    with conn:
        conn.execute(
            "INSERT INTO sync_logs (total_items, new_items, status, error_message) VALUES (?, ?, ?, ?)",
            (total_items, new_items, status, error_message)
        )
    conn.close()

def get_last_sync_info(db_path: str) -> dict:
    init_db(db_path)
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sync_logs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"synced_at": None, "total_items": 0, "new_items": 0, "status": "NEVER_RUN"}
