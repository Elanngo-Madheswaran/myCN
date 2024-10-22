from flask import Flask, request, render_template
from flask_socketio import SocketIO
import sqlite3
from datetime import datetime
import subprocess

app = Flask(__name__)
socketio = SocketIO(app)

def log_ip_addresses(ip_addresses):
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for device in ip_addresses:
        ip = device.get('ip')
        mac = device.get('mac', 'N/A')
        active_status = 1  # Assume the device is active since we found it
        time_span = device.get('time_span', 0)
        c.execute('''
            INSERT INTO ip_log (timestamp, ip_address, mac_address, active_status, time_span)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(ip_address) DO UPDATE SET
                timestamp=excluded.timestamp,
                mac_address=excluded.mac_address,
                active_status=excluded.active_status,
                time_span=ip_log.time_span + 1
        ''', (timestamp, ip, mac, active_status, time_span))
    conn.commit()
    conn.close()
    socketio.emit('update', {'data': 'Database updated'})

@app.route('/log_ip_addresses', methods=['POST'])
def log_ip_addresses_route():
    data = request.get_json()
    ip_addresses = data.get('devices', [])
    log_ip_addresses(ip_addresses)
    return {'status': 'success'}, 200

@app.route('/')
def index():
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    c.execute("SELECT * FROM ip_log")
    data = c.fetchall()
    conn.close()
    return render_template('index.html', data=data)

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
    # Schedule the task to run every minute
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_task, 'interval', minutes=1)
    scheduler.start()

    # Start the Flask app
    socketio.run(app, debug=True)
