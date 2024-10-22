import sqlite3
from datetime import datetime

def add_missing_columns():
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()

    # Check for missing columns and add them if not present
    c.execute("PRAGMA table_info(ip_log)")
    columns = [col[1] for col in c.fetchall()]

    if 'mac_address' not in columns:
        c.execute("ALTER TABLE ip_log ADD COLUMN mac_address TEXT DEFAULT 'N/A'")
    if 'active_status' not in columns:
        c.execute("ALTER TABLE ip_log ADD COLUMN active_status INTEGER DEFAULT 1")
    if 'time_span' not in columns:
        c.execute("ALTER TABLE ip_log ADD COLUMN time_span INTEGER DEFAULT 0")
    
    conn.commit()
    conn.close()

def initialize_db():
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS ip_log (
            timestamp TEXT,
            ip_address TEXT PRIMARY KEY,  -- Made ip_address the primary key
            mac_address TEXT DEFAULT 'N/A',
            active_status INTEGER DEFAULT 1,
            time_span INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def log_ip_addresses(ip_addresses):
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for device in ip_addresses:
        ip = device.get('ip')
        mac = device.get('mac', 'N/A')
        active_status = device.get('active_status', 1)
        time_span = device.get('time_span', 0)
        c.execute('''
            INSERT INTO ip_log (timestamp, ip_address, mac_address, active_status, time_span)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(ip_address) DO UPDATE SET
                timestamp=excluded.timestamp,
                mac_address=excluded.mac_address,
                active_status=excluded.active_status,
                time_span=excluded.time_span
        ''', (timestamp, ip, mac, active_status, time_span))
    conn.commit()
    conn.close()

def fetch_all_logs():
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    c.execute("SELECT * FROM ip_log")
    data = c.fetchall()
    conn.close()
    return data

if __name__ == '__main__':
    initialize_db()
    # Example usage
    devices = [
        {'ip': '192.168.1.1', 'mac': '00:11:22:33:44:55', 'active_status': 1, 'time_span': 120},
        {'ip': '192.168.1.2', 'mac': '66:77:88:99:AA:BB', 'active_status': 0, 'time_span': 60}
    ]
    log_ip_addresses(devices)
    logs = fetch_all_logs()
    for log in logs:
        print(log)
