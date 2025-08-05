"""
Crypto Analyser GUI Dashboard
Main entry point for the Streamlit dashboard - now refactored for modularity

This file serves as the entry point and delegates all functionality to modular components
following the Single Responsibility Principle.
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import the main dashboard module
from dashboard_main import main

# Run the main dashboard
if __name__ == "__main__":
    main()
else:
    # For when imported by Streamlit
    main()