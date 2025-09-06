#!/usr/bin/env python3
"""
Simple script to run the Instagram Pricing Analyzer Streamlit app
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit app"""
    try:
        # Change to the project directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Run the streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running the app: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nApp stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
