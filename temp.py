import subprocess
import requests
import json

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

def send_to_flask(devices):
    url = 'http://127.0.0.1:5000/log_ip_addresses'  # Replace with your Flask app's URL
    data = {'devices': devices}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        print('Data sent successfully')
    else:
        print('Failed to send data')

output = run_nmap()
devices = parse_nmap_output(output)
send_to_flask(devices)
