"""
Continuous Monitoring Smart Inventory System - Universal Launcher
Launches backend.py and frontend.py simultaneously and opens the dashboard in your browser.
"""

import os
import sys
import time
import subprocess
import webbrowser

def main():
    print("==================================================================")
    print("🚀 Starting Continuous Monitoring Smart Inventory System (SIMS)")
    print("==================================================================")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_script = os.path.join(base_dir, "backend.py")
    frontend_script = os.path.join(base_dir, "frontend.py")

    # 1. Start Backend API & Continuous Telemetry Engine
    print("\n[1/2] Launching Backend Engine (backend.py)...")
    backend_proc = subprocess.Popen(
        [sys.executable, backend_script],
        cwd=base_dir
    )
    print("      -> Backend process PID:", backend_proc.pid)
    print("      -> Waiting for API to initialize...")
    time.sleep(2)

    # 2. Start Frontend Streamlit Dashboard
    print("\n[2/2] Launching Frontend Dashboard (frontend.py)...")
    frontend_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", frontend_script, "--server.port=8501", "--server.headless=false"],
        cwd=base_dir
    )
    print("      -> Frontend process PID:", frontend_proc.pid)

    print("\n==================================================================")
    print("✅ System successfully launched!")
    print("🌐 Frontend Dashboard URL : http://localhost:8501")
    print("⚙️ Backend REST API URL   : http://localhost:5000")
    print("Press CTRL+C at any time in this console to shut down both services.")
    print("==================================================================\n")

    try:
        frontend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        frontend_proc.terminate()
        backend_proc.terminate()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
