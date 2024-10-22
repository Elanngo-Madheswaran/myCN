import subprocess
import time

def run_flask_app():
    return subprocess.Popen(['python', 'myflask.py'])

def run_nmap_script():
    return subprocess.Popen(['python', 'temp.py'])

if __name__ == '__main__':
    # Start the Flask app
    flask_process = run_flask_app()
    time.sleep(5)  # Give the Flask app some time to start

    # Start the Nmap script
    nmap_process = run_nmap_script()

    try:
        # Keep the main script running while the subprocesses are active
        flask_process.wait()
        nmap_process.wait()
    except KeyboardInterrupt:
        # Handle cleanup on exit
        flask_process.terminate()
        nmap_process.terminate()
