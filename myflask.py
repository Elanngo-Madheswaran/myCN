from flask import Flask, request, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)

def log_ip_addresses(ip_addresses):
    conn = sqlite3.connect('ip_log.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for ip in ip_addresses:
        c.execute("INSERT INTO ip_log (timestamp, ip_address) VALUES (?, ?)", (timestamp, ip))
    conn.commit()
    conn.close()

@app.route('/log_ip_addresses', methods=['POST'])
def log_ip_addresses_route():
    data = request.get_json()
    ip_addresses = data.get('ip_addresses', [])
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

if __name__ == '__main__':
    app.run(debug=True)
