#!/usr/bin/env python3
"""
Main entry point for Crypto Analyser
Starts the application with GUI
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import and run the GUI version
from scripts.run_with_gui import main

if __name__ == "__main__":
    main()