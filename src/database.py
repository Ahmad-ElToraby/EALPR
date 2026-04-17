import sqlite3
from datetime import datetime
from pathlib import Path

from src.severity import calculate_severity, get_severity_info

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "aman.db"

def init_db():
    """
    Initializes the database by creating the necessary directory and the 'scans' table if they do not exist.
    """
    # Create the data directory if it doesn't exist
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_text TEXT NOT NULL,
            governorate TEXT,
            vehicle_type TEXT,
            confidence REAL,
            color_code TEXT,
            timestamp TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            image_hash TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_text TEXT NOT NULL,
            governorate TEXT,
            severity INTEGER NOT NULL,
            category TEXT,
            description TEXT,
            reported_by TEXT,
            timestamp TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            confirmed_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        )
    ''')
    conn.commit()
    conn.close()

def save_scan(plate_text: str, governorate: str, vehicle_type: str, confidence: float, color_code: str) -> int:
    """
    Inserts a new scan record into the database and returns the new row's ID.
    
    Args:
        plate_text: Extracted text from the license plate.
        governorate: Detected governorate.
        vehicle_type: Detected vehicle type.
        confidence: Combined confidence score.
        color_code: Detected color category.
        
    Returns:
        The integer ID of the newly inserted row.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.utcnow().isoformat()
    cursor.execute('''
        INSERT INTO scans (plate_text, governorate, vehicle_type, confidence, color_code, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (plate_text, governorate, vehicle_type, confidence, color_code, timestamp))
    
    inserted_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return inserted_id

def get_recent_scans(limit: int = 50) -> list[dict]:
    """
    Retrieves the most recent scans up to the given limit, ordered by timestamp in descending order.
    
    Args:
        limit: Maximum number of records to return.
        
    Returns:
        A list of dictionaries where each dictionary represents a scan row.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM scans ORDER BY timestamp DESC LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_scans_by_governorate(governorate: str) -> list[dict]:
    """
    Retrieves all scans associated with a given governorate, ordered by timestamp in descending order.
    
    Args:
        governorate: The governorate string to filter by.
        
    Returns:
        A list of dictionaries where each dictionary represents a scan row.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM scans WHERE governorate = ? ORDER BY timestamp DESC
    ''', (governorate,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_scan_count() -> int:
    """
    Returns the total number of scan records stored in the database.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM scans')
    count = cursor.fetchone()[0]
    
    conn.close()
    
    return count

def file_report(plate_text: str, category: str, description: str = "", reported_by: str = "anonymous", latitude: float = None, longitude: float = None, governorate: str = None) -> int:
    """
    Files a user report for a particular license plate.
    Automatically calculates severity based on historical report count.
    
    Returns:
        The integer ID of the newly inserted report.
    """
    if len(description) > 500:
        description = description[:500]
        
    existing_count = len(get_reports_by_plate(plate_text))
    new_count = existing_count + 1
    severity = calculate_severity(new_count)
    
    if not governorate:
        governorate = "Unknown"
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.utcnow().isoformat()
    cursor.execute('''
        INSERT INTO reports (plate_text, governorate, severity, category, description, reported_by, timestamp, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (plate_text, governorate, severity, category, description, reported_by, timestamp, latitude, longitude))
    
    inserted_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    save_scan(plate_text=plate_text, governorate=governorate, vehicle_type="reported", confidence=1.0, color_code="")
    
    return inserted_id

def get_reports_by_plate(plate_text: str) -> list[dict]:
    """
    Returns all active reports for a given plate, ordered by timestamp DESC.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM reports WHERE plate_text = ? AND status = 'active' ORDER BY timestamp DESC
    ''', (plate_text,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_recent_reports(limit: int = 50) -> list[dict]:
    """
    Returns most recent active reports across all plates, ordered by timestamp DESC.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM reports WHERE status = 'active' ORDER BY timestamp DESC LIMIT ?
    ''', (limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def get_hotspot_plates(min_reports: int = 2) -> list[dict]:
    """
    Returns plates that have been reported min_reports or more times.
    This is the data source for the community danger map.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT plate_text, COUNT(*) as report_count, MAX(severity) as max_severity, governorate 
        FROM reports 
        WHERE status='active' 
        GROUP BY plate_text 
        HAVING COUNT(*) >= ? 
        ORDER BY report_count DESC
    ''', (min_reports,))
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def confirm_report(report_id: int) -> bool:
    """
    Increments confirmed_count by 1 for the given report_id.
    
    Returns:
        True if the row existed, False if not found.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE reports SET confirmed_count = confirmed_count + 1 WHERE id = ?
    ''', (report_id,))
    
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return changed

def get_plate_severity(plate_text: str) -> dict:
    """
    Calculates the current danger level of a plate dynamically.
    """
    reports = get_reports_by_plate(plate_text)
    count = len(reports)
    level = calculate_severity(count)
    
    return {
        "plate_text": plate_text,
        "report_count": count,
        "severity_level": level,
        "severity_info": get_severity_info(level)
    }

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
    print(f"Current scan count: {get_scan_count()}")
