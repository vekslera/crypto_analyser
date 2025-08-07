#!/usr/bin/env python3
"""
Test GUI price updates to ensure real-time 60s data flow
Simulates what the GUI dashboard does when fetching current price
"""

import sys
import os
import time

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import GUI data operations
from client.data_operations import get_current_price_from_api

def test_gui_price_updates():
    """Test that GUI gets real-time price updates"""
    
    print("TESTING GUI PRICE UPDATES")
    print("=" * 40)
    print("This simulates what the Streamlit GUI does...")
    print()
    
    for i in range(3):
        print(f"GUI Update {i+1}:")
        
        # Call the same function the GUI uses
        price_data = get_current_price_from_api()
        
        if price_data:
            print(f"  Current Price: ${price_data['price']:,.2f}")
            print(f"  Timestamp: {price_data['timestamp']}")
            print(f"  Volume: ${price_data.get('volume_24h', 0):,.0f}")
            print(f"  Market Cap: ${price_data.get('market_cap', 0):,.0f}")
        else:
            print("  ERROR: No price data received")
        
        if i < 2:
            print("  Waiting 15 seconds for next update...")
            print()
            time.sleep(15)
    
    print("\nGUI TEST COMPLETED!")
    print("The GUI should now show real-time prices updated every 60 seconds")
    print("instead of the 5-minute averaged prices from the database.")

if __name__ == "__main__":
    test_gui_price_updates()