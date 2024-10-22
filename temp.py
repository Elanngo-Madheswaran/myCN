import subprocess
import requests
import json
import time

# Run nmap scan
def run_nmap():
    result = subprocess.run(['nmap', '-sn', '192.168.137.0/24'], capture_output=True, text=True, shell=True)
    return result.stdout

# Parse nmap output and update the device dictionary
def parse_nmap_output(output, device_dict):
    lines = output.split('\n')
    current_device = {}
    current_time = time.time()
    for line in lines:
        if 'Nmap scan report for' in line:
            if current_device:
                mac = current_device.get('mac')
                if mac:
                    # If device exists, update its timespan
                    if mac in device_dict:
                        previous_time = device_dict[mac]['last_seen']
                        current_device['time_span'] = current_device.get('time_span', 0) + int(current_time - previous_time)
                    else:
                        current_device['time_span'] = 0
                    current_device['last_seen'] = current_time
                    current_device['active_status'] = 1  # Device is active
                    device_dict[mac] = current_device
            current_device = {'ip': line.split()[-1]}
        elif 'MAC Address:' in line:
            current_device['mac'] = line.split('MAC Address: ')[1].split(' ')[0]
    if current_device:
        mac = current_device.get('mac')
        if mac:
            if mac in device_dict:
                previous_time = device_dict[mac]['last_seen']
                current_device['time_span'] = current_device.get('time_span', 0) + int(current_time - previous_time)
            else:
                current_device['time_span'] = 0
            current_device['last_seen'] = current_time
            current_device['active_status'] = 1  # Device is active
            device_dict[mac] = current_device
    return device_dict

# Send data to Flask backend
def send_to_flask(device_dict):
    url = 'http://127.0.0.1:5000/log_ip_addresses'  # Replace with your Flask app's URL
    devices = list(device_dict.values())
    data = {'devices': devices}
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code == 200:
        print('Data sent successfully')
    else:
        print('Failed to send data')

# Run the script
device_dict = {}
output = run_nmap()
device_dict = parse_nmap_output(output, device_dict)
send_to_flask(device_dict)
