#!/usr/bin/env python3

import subprocess
import sys

def main():
    """Start the Anthropic Status Bot."""
    try:
        print("Starting Anthropic Status Bot...")
        subprocess.run([sys.executable, "run.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting bot: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nBot shutdown requested")
        sys.exit(0)

if __name__ == "__main__":
    main()