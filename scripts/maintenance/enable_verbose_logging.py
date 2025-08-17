#!/usr/bin/env python3
"""
Enable verbose logging for the optimal scheduler
Modifies logging levels to show detailed information
"""

import sys
import os
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)


def enable_verbose_logging():
    """Enable verbose logging throughout the application"""
    
    print("ENABLING VERBOSE LOGGING")
    print("=" * 30)
    
    # Set root logger to DEBUG
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Create console handler if not exists
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Enable DEBUG level for specific components
    components_to_debug = [
        'server.optimal_scheduler',
        'server.services.crypto_service',
        'server.implementations.multi_source_provider', 
        'server.implementations.coingecko_provider',
        'server.implementations.hybrid_provider'
    ]
    
    for component in components_to_debug:
        logger = logging.getLogger(component)
        logger.setLevel(logging.DEBUG)
        print(f"✓ Enabled DEBUG logging for: {component}")
    
    print("\nVerbose logging is now enabled!")
    print("You should now see detailed logs for:")
    print("  • Volume fetching from CoinMarketCap")
    print("  • Price smoothing calculations")
    print("  • Database insertion operations")
    print("  • Volume velocity calculations")
    
    return True


if __name__ == "__main__":
    enable_verbose_logging()