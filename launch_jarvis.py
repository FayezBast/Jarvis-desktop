#!/usr/bin/env python3
"""
Jarvis Desktop GUI Launcher
Simple script to launch the Jarvis desktop application
"""

import sys
import os

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import and run the GUI
from jarvis_gui import main

if __name__ == "__main__":
    main()
