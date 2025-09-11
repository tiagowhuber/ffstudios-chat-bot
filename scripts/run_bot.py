#!/usr/bin/env python3
"""
Development utility script to start the bot in development mode.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Start the bot with development settings."""
    project_root = Path(__file__).parent.parent
    main_script = project_root / "main.py"
    
    print(" Starting FFStudios Chat Bot in development mode...")
    print(f" Project root: {project_root}")
    print(f" Running: {main_script}")
    print("-" * 50)
    
    try:
        subprocess.run([sys.executable, str(main_script)], cwd=project_root, check=True)
    except KeyboardInterrupt:
        print("\n Bot stopped by user")
    except subprocess.CalledProcessError as e:
        print(f" Error running bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()