"""
Main configuration module for Crypto Analyser
Imports and re-exports all configuration settings for backward compatibility
"""

# Import all configuration sections
from .app_config import *
from .api_config import *
from .ui_config import *
from .user_parameters import *

# This module serves as a central import point for all configuration
# while maintaining the modular structure underneath