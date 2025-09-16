#!/usr/bin/env python3
"""
Simple direct test of gap detection without full dependency injection
"""

import sqlite3
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import sys

# Add project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.api_config import GAP_DETECTION_MIN_HOURS

# Simple mock repository for testing
class SimpleRepository:
    def __init__(self, db_path):
        self.db_path = db_path
    
    async def get_price_history(self, limit=50000):
        """Get price history as simple objects"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get records
        rows = cursor.execute("""
            SELECT price, timestamp, volume_24h, market_cap, volatility, money_flow, volume_velocity
            FROM bitcoin_prices 
            ORDER BY timestamp DESC 
            LIMIT ?
        """, (limit,)).fetchall()
        
        conn.close()
        
        # Convert to simple objects
        results = []
        for row in rows:
            # Create simple object with timestamp attribute
            obj = type('PriceData', (), {})()
            obj.price = row[0]
            obj.timestamp = datetime.fromisoformat(row[1]) if row[1] else None
            obj.volume_24h = row[2]
            obj.market_cap = row[3]
            obj.volatility = row[4]
            obj.money_flow = row[5]
            obj.volume_velocity = row[6]
            results.append(obj)
        
        return results

async def test_gap_detection():
    """Test gap detection directly"""
    
    print("TESTING GAP DETECTION DIRECTLY")
    print("=" * 35)
    
    # Create simple repository
    db_path = os.path.join('.', 'data', 'crypto_analyser.db')
    repo = SimpleRepository(db_path)
    
    # Get data
    all_prices = await repo.get_price_history(limit=50000)
    print(f"Got {len(all_prices)} records from database")
    
    if not all_prices:
        print("No data - database is empty")
        return
    
    # Sort by timestamp
    all_prices.sort(key=lambda x: x.timestamp)
    
    now = datetime.now(timezone.utc)
    check_recent_days = 30
    min_gap_hours = GAP_DETECTION_MIN_HOURS
    
    print(f"Current time: {now}")
    print(f"Checking last {check_recent_days} days")
    
    gaps = []
    
    # Check for gap from last record to now
    latest_record = all_prices[-1]
    latest_time = latest_record.timestamp
    if latest_time.tzinfo is None:
        latest_time = latest_time.replace(tzinfo=timezone.utc)
    
    gap_to_now = (now - latest_time).total_seconds() / 3600
    print(f"Gap from latest record to now: {gap_to_now:.1f} hours")
    if gap_to_now > min_gap_hours:
        print(f"  -> Adding gap: {latest_time} to {now}")
        gaps.append({
            'start': latest_time,
            'end': now,
            'duration_hours': gap_to_now
        })
    
    # Check for gap from start of recent period to first record
    earliest_record = all_prices[0]
    earliest_time = earliest_record.timestamp
    if earliest_time.tzinfo is None:
        earliest_time = earliest_time.replace(tzinfo=timezone.utc)
    
    recent_start = now - timedelta(days=check_recent_days)
    gap_from_start = (earliest_time - recent_start).total_seconds() / 3600
    
    print(f"Gap from {check_recent_days} days ago to earliest record: {gap_from_start:.1f} hours")
    print(f"  recent_start: {recent_start}")
    print(f"  earliest_time: {earliest_time}")
    print(f"  earliest > recent_start: {earliest_time > recent_start}")
    
    if gap_from_start > min_gap_hours and earliest_time > recent_start:
        print(f"  -> Adding gap: {recent_start} to {earliest_time}")
        gaps.append({
            'start': recent_start,
            'end': earliest_time,
            'duration_hours': gap_from_start
        })
    
    print(f"\nFound {len(gaps)} gaps:")
    for i, gap in enumerate(gaps, 1):
        print(f"  {i}. {gap['start']} to {gap['end']} ({gap['duration_hours']:.1f}h)")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_gap_detection())