import os
import sqlite3
from datetime import datetime

# Initialize the database and create a table
def initialize_db():
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS ip_log (
            ip_address TEXT PRIMARY KEY,
            mac_address TEXT DEFAULT 'N/A',
            active_status INTEGER DEFAULT 1,
            time_span INTEGER DEFAULT 0,
            last_seen TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Log IP addresses and update time spans for existing devices
def log_ip_addresses(ip_addresses):
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    current_time = datetime.now()

    for device in ip_addresses:
        ip = device.get('ip')
        mac = device.get('mac', 'N/A')
        active_status = device.get('active_status', 1)
        
        # Check if the device is already logged
        c.execute('SELECT time_span, last_seen FROM ip_log WHERE ip_address = ?', (ip,))
        row = c.fetchone()

        if row:
            # Update time_span for already connected device
            previous_time_span = row[0]
            last_seen = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
            time_diff = (current_time - last_seen).total_seconds()
            new_time_span = previous_time_span + int(time_diff)

            c.execute('''
                UPDATE ip_log
                SET mac_address = ?, active_status = ?, time_span = ?, last_seen = ?
                WHERE ip_address = ?
            ''', (mac, active_status, new_time_span, current_time.strftime('%Y-%m-%d %H:%M:%S'), ip))
        else:
            # Insert a new device if not already in the log
            c.execute('''
                INSERT INTO ip_log (ip_address, mac_address, active_status, time_span, last_seen, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ip, mac, active_status, 0, current_time.strftime('%Y-%m-%d %H:%M:%S'), current_time.strftime('%Y-%m-%d %H:%M:%S')))

    conn.commit()
    conn.close()

# Fetch all logs from the database
def fetch_all_logs():
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    c.execute("SELECT * FROM ip_log")
    data = c.fetchall()
    conn.close()
    return data
