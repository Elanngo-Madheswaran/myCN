from flask import Flask, request, render_template
from flask_socketio import SocketIO
import sqlite3
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    c.execute("SELECT * FROM ip_log")
    data = c.fetchall()
    conn.close()
    return render_template('index.html', data=data)

def log_ip_addresses(ip_addresses):
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    current_time = datetime.now()
    timestamp = current_time.strftime('%Y-%m-%d %H:%M:%S')

    for device in ip_addresses:
        ip = device.get('ip')
        mac = device.get('mac', 'N/A')
        active_status = 1  # Assume the device is active since we found it

        # Check if the device is already logged
        c.execute('SELECT time_span, last_seen FROM ip_log WHERE ip_address = ?', (ip,))
        row = c.fetchone()

        if row:
            previous_time_span = row[0]
            last_seen = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
            time_diff = (current_time - last_seen).total_seconds()

            # Update time_span with the new duration since last seen
            new_time_span = previous_time_span + int(time_diff)

            c.execute('''
                UPDATE ip_log
                SET mac_address = ?, active_status = ?, time_span = ?, last_seen = ?, timestamp = ?
                WHERE ip_address = ?
            ''', (mac, active_status, new_time_span, timestamp, timestamp, ip))
        else:
            # Insert a new device if it's not already in the log
            time_span = 0  # Set to 0 when inserting a new device
            c.execute('''
                INSERT INTO ip_log (ip_address, mac_address, active_status, time_span, last_seen, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ip, mac, active_status, time_span, timestamp, timestamp))

    conn.commit()
    conn.close()
    socketio.emit('update', {'data': 'Database updated'})

@app.route('/log_ip_addresses', methods=['POST'])
def log_ip_addresses_route():
    data = request.get_json()
    ip_addresses = data.get('devices', [])
    log_ip_addresses(ip_addresses)
    return {'status': 'success'}, 200

def run_nmap():
    result = subprocess.run(['nmap', '-sn', '192.168.137.0/24'], capture_output=True, text=True, shell=True)
    return result.stdout

def parse_nmap_output(output):
    lines = output.split('\n')
    devices = []
    current_device = {}
    for line in lines:
        if 'Nmap scan report for' in line:
            if current_device:
                devices.append(current_device)
            current_device = {'ip': line.split()[-1]}
        elif 'MAC Address:' in line:
            current_device['mac'] = line.split('MAC Address: ')[1].split(' ')[0]
    if current_device:
        devices.append(current_device)
    return devices

def scheduled_task():
    output = run_nmap()
    devices = parse_nmap_output(output)
    log_ip_addresses(devices)

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_task, 'interval', minutes=1)
    scheduler.start()
    socketio.run(app, debug=True)
