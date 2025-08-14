#!/usr/bin/env python3
"""
Entry point for server-only mode
Starts the FastAPI server without GUI
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import and run the server version
from scripts.runners.run import main

if __name__ == "__main__":
    main()