import os
import subprocess
import json
import requests
import time
import sys


def start_ngrok_and_get_url():
    print("Starting ngrok...")
    # Start ngrok in a subprocess, redirecting output to a pipe
    # Use --log=stdout to capture ngrok's own logs for debugging if needed
    ngrok_process = subprocess.Popen(
        ['./ngrok.exe', 'http', '5000', '--log=stdout'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    )

    api_url = "http://127.0.0.1:4040/api/tunnels"
    public_url = None
    for _ in range(30):  # Increased attempts to 30 (30 seconds)
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            tunnels = response.json()['tunnels']
            for tunnel in tunnels:
                if tunnel['proto'] == 'https':
                    public_url = tunnel['public_url']
                    print(f"Ngrok started. Public URL: {public_url}")
                    return public_url, ngrok_process
        except (requests.exceptions.ConnectionError, json.JSONDecodeError) as e:
            print(f"Attempt to get ngrok URL failed: {e}. Retrying...")
            time.sleep(1)
    print("Failed to start ngrok or get public URL after multiple attempts.")
    # Print ngrok's stderr output if it failed to start
    stderr_output = ngrok_process.stderr.read()
    if stderr_output:
        print(f"Ngrok stderr output:\n{stderr_output}")
    if ngrok_process.poll() is None:  # If ngrok process is still running
        ngrok_process.terminate()  # Ensure ngrok process is terminated if it fails to start
    return None, None


def run_flask_app(ngrok_url):
    env = os.environ.copy()
    if ngrok_url:
        env['NGROK_URL'] = ngrok_url
        print(f"Setting NGROK_URL environment variable: {ngrok_url}")
    else:
        print("NGROK_URL not available, running Flask without it.")

    # Command to run Flask app using the Flask CLI
    # Ensure the FLASK_APP environment variable is set for 'flask run'
    env['FLASK_APP'] = 'app.py'
    flask_command = [
        sys.executable, '-m', 'flask', 'run',
        '--host=0.0.0.0', '--port=5000'
    ]
    print(f"Running Flask app with command: {' '.join(flask_command)}")
    flask_process = subprocess.Popen(flask_command, env=env)
    return flask_process


if __name__ == '__main__':
    # Ensure ngrok.exe exists
    if not os.path.exists('ngrok.exe'):
        print("Error: ngrok.exe not found in the current directory.")
        print("Please download ngrok from https://ngrok.com/download and place it here.")
        sys.exit(1)

    ngrok_url, ngrok_proc = start_ngrok_and_get_url()

    if ngrok_proc:
        flask_proc = run_flask_app(ngrok_url)
        print(f"\nAccess your application at: {ngrok_url}")
        try:
            flask_proc.wait()  # Wait for Flask app to finish
        except KeyboardInterrupt:
            print("\nStopping Flask app and ngrok...")
        finally:
            if flask_proc.poll() is None:  # If Flask app is still running
                flask_proc.terminate()
            if ngrok_proc.poll() is None:  # If ngrok is still running
                ngrok_proc.terminate()
            print("Processes terminated.")
    else:
        print("Could not start ngrok. Running Flask app directly.")
        flask_proc = run_flask_app(None)
        try:
            flask_proc.wait()
        except KeyboardInterrupt:
            print("\nStopping Flask app...")
        finally:
            if flask_proc.poll() is None:
                flask_proc.terminate()
            print("Flask app terminated.")
