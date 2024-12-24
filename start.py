#!/usr/bin/env python3
"""
Anthropic Status Bot entry point script.
Combines process management and Python path setup in a single file.
"""

import os
import sys
import subprocess

def setup_python_path():
    """Add src directory to Python path."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Start the Anthropic Status Bot with proper error handling."""
    try:
        print("Starting Anthropic Status Bot...")
        setup_python_path()
        from index import main as bot_main
        bot_main()
    except ImportError as e:
        print(f"Error importing bot modules: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting bot: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nBot shutdown requested")
        sys.exit(0)

if __name__ == "__main__":
    main()