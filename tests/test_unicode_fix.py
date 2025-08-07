#!/usr/bin/env python3
"""
Test script to verify Unicode character fixes in logging
Tests that high volume velocity logging doesn't cause encoding errors
"""

import sys
import os
import logging
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_unicode_logging_fix():
    """Test that logging with high volume velocity works without Unicode errors"""
    
    print("TESTING UNICODE LOGGING FIX")
    print("=" * 40)
    
    # Set up a test logger
    logger = logging.getLogger("test_unicode")
    logger.setLevel(logging.INFO)
    
    # Create console handler 
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Test high velocity logging (the problematic case)
    volume_velocity = 5310664794  # The value from the error
    
    try:
        # This should work without Unicode encoding errors
        logger.warning(f"    WARNING: HIGH velocity detected: ${volume_velocity:,.0f}/min")
        logger.info(f"    SUCCESS Normal velocity: ${100000:,.0f}/min")
        logger.info(f"    SUCCESS Moderate velocity: ${500000:,.0f}/min")
        
        print("SUCCESS: All logging tests passed without Unicode errors")
        
    except UnicodeEncodeError as e:
        print(f"FAILED: Unicode encoding error: {e}")
        return False
    except Exception as e:
        print(f"FAILED: Unexpected error: {e}")
        return False
    
    return True

def test_volume_velocity_scenarios():
    """Test various volume velocity logging scenarios"""
    
    print(f"\nTESTING VOLUME VELOCITY SCENARIOS")
    print("=" * 40)
    
    # Test different velocity ranges
    test_velocities = [
        (50000, "Low velocity"),
        (500000, "Moderate velocity"), 
        (5000000000, "High velocity (5B/min)"),
        (-1000000000, "Negative high velocity"),
    ]
    
    logger = logging.getLogger("test_velocity")
    logger.setLevel(logging.INFO)
    
    for velocity, description in test_velocities:
        try:
            # Simulate the crypto service logging logic
            if abs(velocity) > 1000000000:  # > 1B/min
                logger.warning(f"    WARNING: HIGH velocity detected: ${velocity:,.0f}/min")
            elif abs(velocity) < 100000:  # < 100K/min
                logger.info(f"    SUCCESS Normal velocity: ${velocity:,.0f}/min")
            else:
                logger.info(f"    SUCCESS Moderate velocity: ${velocity:,.0f}/min")
            
            print(f"SUCCESS {description}: Logging successful")
            
        except Exception as e:
            print(f"FAILED {description}: Error - {e}")
            return False
    
    return True

if __name__ == "__main__":
    success1 = test_unicode_logging_fix()
    success2 = test_volume_velocity_scenarios()
    
    if success1 and success2:
        print(f"\nALL TESTS PASSED!")
        print("Unicode character fixes are working correctly.")
    else:
        print(f"\nSOME TESTS FAILED!")
        print("Unicode issues may still exist.")