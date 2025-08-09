import os
import subprocess
import sys


def run_flask_app():
    env = os.environ.copy()
    env['FLASK_APP'] = 'app.py'
    flask_command = [
        sys.executable, '-m', 'flask', 'run',
        '--host=0.0.0.0', '--port=5000'
    ]
    print(f"Running Flask app with command: {' '.join(flask_command)}")
    flask_process = subprocess.Popen(flask_command, env=env)
    return flask_process


if __name__ == '__main__':
    flask_proc = run_flask_app()
    try:
        flask_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping Flask app...")
    finally:
        if flask_proc.poll() is None:
            flask_proc.terminate()
        print("Flask app terminated.")
