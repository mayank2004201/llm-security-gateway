import subprocess
import sys
import os

def run():
    # Set up paths
    script_path = os.path.join("app", "dashboard", "app.py")
    
    # Run streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", script_path]
    subprocess.run(cmd)

if __name__ == "__main__":
    run()
