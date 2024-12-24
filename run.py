#!/usr/bin/env python3
"""
Anthropic Status Bot entry point script.
This script sets up the Python path and starts the bot.
"""

import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == '__main__':
    from index import main
    main()