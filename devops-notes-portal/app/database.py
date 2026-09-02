import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

NOTES_DATA_DIR = os.getenv("NOTES_DIR", "/app/data/notes")
# Store database directly inside the PVC directory so state persists across restarts
DB_PATH = os.path.join(NOTES_DATA_DIR, ".cidr_planner.db")

def get_db_connection():
    os.makedirs(NOTES_DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    
    # Ensure tables exist
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calculation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        cidr TEXT NOT NULL,
        cloud_provider TEXT NOT NULL,
        total_ips INTEGER NOT NULL,
        usable_ips INTEGER NOT NULL,
        subnet_mask TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vpc_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        project_name TEXT NOT NULL,
        vpc_cidr TEXT NOT NULL,
        cloud_provider TEXT NOT NULL,
        subnets_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    return conn

def init_db():
    conn = get_db_connection()
    conn.close()

# Auto-initialize on import
try:
    init_db()
except Exception as _e:
    pass

# Database Operations

def get_or_create_user(username: str) -> Dict[str, Any]:
    username = username.strip()
    if not username:
        username = "guest"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
    else:
        cursor.execute("UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE username = ?", (username,))
        conn.commit()
    user_dict = dict(row)
    conn.close()
    return user_dict

def save_calculation_history(username: str, cidr: str, cloud_provider: str, total_ips: int, usable_ips: int, subnet_mask: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Check if latest entry for this user is already the exact same calculation
    cursor.execute("""
    SELECT cidr, cloud_provider FROM calculation_history 
    WHERE username = ? 
    ORDER BY id DESC LIMIT 1
    """, (username,))
    latest = cursor.fetchone()
    if latest and latest["cidr"] == cidr and latest["cloud_provider"] == cloud_provider:
        conn.close()
        return

    cursor.execute("""
    INSERT INTO calculation_history (username, cidr, cloud_provider, total_ips, usable_ips, subnet_mask)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (username, cidr, cloud_provider, total_ips, usable_ips, subnet_mask))
    conn.commit()
    conn.close()

def get_user_history(username: str, limit: int = 30) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM calculation_history 
    WHERE username = ? 
    ORDER BY created_at DESC 
    LIMIT ?
    """, (username, limit))
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results

def clear_user_history(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM calculation_history WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def save_vpc_project(username: str, project_name: str, vpc_cidr: str, cloud_provider: str, subnets_json: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO vpc_projects (username, project_name, vpc_cidr, cloud_provider, subnets_json, updated_at)
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (username, project_name, vpc_cidr, cloud_provider, subnets_json))
    conn.commit()
    project_id = cursor.lastrowid
    conn.close()
    return project_id

def get_user_vpc_projects(username: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM vpc_projects 
    WHERE username = ? 
    ORDER BY updated_at DESC
    """, (username,))
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results

def delete_vpc_project(project_id: int, username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vpc_projects WHERE id = ? AND username = ?", (project_id, username))
    conn.commit()
    conn.close()
