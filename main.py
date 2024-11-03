from flask import Flask, request, render_template
from flask_socketio import SocketIO
import sqlite3
from datetime import datetime, timedelta
import subprocess

app = Flask(__name__)
socketio = SocketIO(app)

import math  # Import math to use ceil function

def log_ip_addresses(ip_addresses):
    try:
        with sqlite3.connect('ip_log.db') as conn:
            c = conn.cursor()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Mark all devices as inactive
            c.execute('UPDATE ip_log SET active_status = 0')

            for device in ip_addresses:
                ip = device.get('ip')
                mac = device.get('mac')
                
                # Only proceed if the MAC address exists
                if not mac:
                    continue
                
                # Assume the device is active since we found it
                active_status = 1  
                time_span = 0
                nickname = None  # Initialize nickname as None

                # Check the last timestamp for this IP address
                c.execute('SELECT timestamp, time_span, nickname FROM ip_log WHERE ip_address = ?', (ip,))
                row = c.fetchone()
                
                if row:
                    last_timestamp = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                    previous_time_span = row[1]
                    nickname = row[2]  # Get the existing nickname if available

                    # Calculate the time difference in minutes
                    time_difference = (datetime.now() - last_timestamp).total_seconds() / 60
                    
                    if time_difference <= 1:
                        # Update time_span based on the last active period
                        time_span = math.ceil(previous_time_span + time_difference)
                    else:
                        # If more than a minute has passed, reset time_span to current active duration
                        time_span = 1  # Set to 1 minute for the current connection

                else:
                    # If no previous record exists, set time_span to 1 minute for new entries
                    time_span = 1  

                # Insert or update the record in the database
                c.execute('''    
                    INSERT INTO ip_log (ip_address, mac_address, timestamp, active_status, time_span, nickname)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ip_address) DO UPDATE SET
                        mac_address=excluded.mac_address,
                        timestamp=excluded.timestamp,
                        active_status=excluded.active_status,
                        time_span=excluded.time_span,
                        nickname=excluded.nickname
                ''', (ip, mac, timestamp, active_status, time_span, nickname))
            
            conn.commit()
            socketio.emit('update', {'data': 'Database updated'})
    except Exception as e:
        print(f'Error: {e}')

@app.route('/log_ip_addresses', methods=['POST'])
def log_ip_addresses_route():
    data = request.get_json()
    ip_addresses = data.get('devices', [])
    log_ip_addresses(ip_addresses)
    return {'status': 'success'}, 200

@app.route('/set_nickname', methods=['POST'])
def set_nickname():
    ip = request.form.get('ip')
    nickname = request.form.get('nickname')

    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    c.execute('UPDATE ip_log SET nickname = ? WHERE ip_address = ?', (nickname, ip))
    conn.commit()
    conn.close()

    return {'status': 'success', 'nickname': nickname}  # Return JSON response





@app.route('/')
def index():
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    c.execute("SELECT * FROM ip_log")
    data = c.fetchall()
    conn.close()
    return render_template('index.html', data=data)

def run_nmap():
    result = subprocess.run(['nmap', '-sn', '192.168.43.0/24'], capture_output=True, text=True, shell=True)
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
