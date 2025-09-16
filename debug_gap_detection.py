#!/usr/bin/env python3
"""
Debug gap detection to see why it's not finding the missing 30 days
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta, timezone

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.dependency_container import container
from server.services.gap_filling_service import GapFillingService
from core.api_config import GAP_DETECTION_MIN_HOURS

async def debug_gap_detection():
    """Debug the gap detection logic"""
    
    print("DEBUGGING GAP DETECTION")
    print("=" * 30)
    
    # Initialize container
    await container.initialize()
    
    # Get services
    database_repo = container.get_database_repository()
    gap_service = GapFillingService(database_repo)
    
    # Get current data
    all_prices = await database_repo.get_price_history(limit=50000)
    print(f"Database has {len(all_prices)} records")
    
    if all_prices:
        all_prices.sort(key=lambda x: x.timestamp)
        earliest = all_prices[0].timestamp
        latest = all_prices[-1].timestamp
        print(f"Date range: {earliest} to {latest}")
        print(f"Earliest timezone: {earliest.tzinfo}")
        print(f"Latest timezone: {latest.tzinfo}")
    
    # Check current time
    now = datetime.now(timezone.utc)
    print(f"Current time: {now}")
    
    # Check 30 days ago
    recent_start = now - timedelta(days=30)
    print(f"30 days ago: {recent_start}")
    
    if all_prices:
        latest_time = latest
        if latest_time.tzinfo is None:
            latest_time = latest_time.replace(tzinfo=timezone.utc)
        
        gap_to_now = (now - latest_time).total_seconds() / 3600
        print(f"Gap from latest record to now: {gap_to_now:.1f} hours")
        
        earliest_time = earliest
        if earliest_time.tzinfo is None:
            earliest_time = earliest_time.replace(tzinfo=timezone.utc)
        
        gap_from_start = (earliest_time - recent_start).total_seconds() / 3600
        print(f"Gap from 30 days ago to earliest record: {gap_from_start:.1f} hours")
        print(f"Earliest > recent_start? {earliest_time > recent_start}")
    
    # Test gap detection
    print("\nTesting gap detection...")
    gaps = await gap_service.detect_gaps(check_recent_days=30)
    print(f"Found {len(gaps)} gaps:")
    
    for i, gap in enumerate(gaps, 1):
        print(f"  {i}. {gap['start']} to {gap['end']} ({gap['duration_hours']:.1f}h)")

if __name__ == "__main__":
    asyncio.run(debug_gap_detection())