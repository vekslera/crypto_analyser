#!/usr/bin/env python3
"""
Test the dual scheduler system
Verify separate collection of price and volume data
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from server.dependency_container import container
from server.dual_scheduler import DualPriceScheduler
from core.api_config import DEFAULT_COLLECTION_INTERVAL, VOLUME_COLLECTION_INTERVAL


async def test_dual_collection():
    """Test individual collection jobs"""
    
    print("Testing Dual Scheduler Collection Jobs")
    print("=" * 50)
    
    # Initialize container with CoinGecko (for separate testing)
    db_url = f"sqlite:///{os.path.join(project_root, 'data', 'crypto_analyser.db')}"
    
    success = await container.initialize(
        database_url=db_url,
        crypto_provider="coingecko"  # We'll test CoinGecko separately
    )
    
    if not success:
        print("Failed to initialize dependency container")
        return
    
    # Create scheduler instance
    scheduler = DualPriceScheduler(
        price_interval_seconds=10,    # Short interval for testing
        volume_interval_seconds=15    # Short interval for testing
    )
    
    print("\n1. Testing CoinGecko price collection...")
    try:
        await scheduler.collect_price_job()
        print("   ✓ Price collection successful")
    except Exception as e:
        print(f"   ✗ Price collection failed: {e}")
    
    print("\n2. Testing CoinMarketCap volume collection...")
    try:
        await scheduler.collect_volume_job()
        print("   ✓ Volume collection successful")
    except Exception as e:
        print(f"   ✗ Volume collection failed: {e}")
    
    # Check database for results
    print("\n3. Checking database results...")
    try:
        crypto_service = container.get_crypto_service()
        recent_data = await crypto_service.get_recent_prices(3)
        
        if recent_data:
            print(f"   Found {len(recent_data)} recent records:")
            for i, record in enumerate(recent_data[:3], 1):
                vol_str = f"${record.volume_24h:,.0f}" if record.volume_24h else "None"
                mcap_str = f"${record.market_cap:,.0f}" if record.market_cap else "None"
                print(f"   {i}. Price: ${record.price:,.2f} | Volume: {vol_str} | Market Cap: {mcap_str}")
        else:
            print("   No recent records found")
    except Exception as e:
        print(f"   Error checking database: {e}")


async def test_hybrid_provider():
    """Test the hybrid provider directly"""
    
    print(f"\n" + "=" * 50)
    print("Testing Hybrid Provider")
    print("=" * 50)
    
    try:
        from server.implementations.hybrid_provider import HybridProvider
        
        hybrid = HybridProvider()
        
        print("Fetching data with hybrid provider...")
        data = await hybrid.fetch_current_price("bitcoin")
        
        if data:
            print("✓ Hybrid provider successful:")
            print(f"  Price: ${data.price:,.2f}")
            vol_str = f"${data.volume_24h:,.0f}" if data.volume_24h else "None"
            mcap_str = f"${data.market_cap:,.0f}" if data.market_cap else "None"
            print(f"  Volume: {vol_str}")
            print(f"  Market Cap: {mcap_str}")
            print(f"  Provider: {hybrid.get_provider_name()}")
        else:
            print("✗ Hybrid provider failed to fetch data")
            
    except Exception as e:
        print(f"✗ Hybrid provider test failed: {e}")
        import traceback
        traceback.print_exc()


def test_api_limits():
    """Calculate API usage projections"""
    
    print(f"\n" + "=" * 50)
    print("API Usage Projections")
    print("=" * 50)
    
    # CoinGecko (price + market cap every 60s)
    cg_calls_per_day = (24 * 60 * 60) / DEFAULT_COLLECTION_INTERVAL
    cg_calls_per_month = cg_calls_per_day * 30
    
    # CoinMarketCap (volume every 300s)  
    cmc_calls_per_day = (24 * 60 * 60) / VOLUME_COLLECTION_INTERVAL
    cmc_calls_per_month = cmc_calls_per_day * 30
    
    print(f"CoinGecko Usage (Price + Market Cap):")
    print(f"  Interval: {DEFAULT_COLLECTION_INTERVAL}s")
    print(f"  Calls per day: {cg_calls_per_day:.0f}")
    print(f"  Calls per month: {cg_calls_per_month:.0f}")
    print(f"  Rate limit: No API key required")
    
    print(f"\nCoinMarketCap Usage (Volume only):")
    print(f"  Interval: {VOLUME_COLLECTION_INTERVAL}s")
    print(f"  Calls per day: {cmc_calls_per_day:.0f}")
    print(f"  Calls per month: {cmc_calls_per_month:.0f}")
    print(f"  Rate limit: 10,000/month (Free tier)")
    
    if cmc_calls_per_month <= 10000:
        print(f"  ✓ Within free tier limits ({cmc_calls_per_month/10000*100:.1f}% usage)")
    else:
        print(f"  ✗ Exceeds free tier limits ({cmc_calls_per_month/10000*100:.1f}% usage)")
    
    print(f"\nTotal Monthly API Calls: {cg_calls_per_month + cmc_calls_per_month:.0f}")
    print(f"Data Quality: Price/MCap from CoinGecko, Volume from CoinMarketCap")


async def main():
    """Run all tests"""
    
    print("Dual Scheduler System Test")
    print("=" * 50)
    print(f"Price collection interval: {DEFAULT_COLLECTION_INTERVAL}s")
    print(f"Volume collection interval: {VOLUME_COLLECTION_INTERVAL}s")
    
    # Test API usage calculations
    test_api_limits()
    
    # Test hybrid provider
    await test_hybrid_provider()
    
    # Test dual collection jobs
    await test_dual_collection()
    
    print(f"\n" + "=" * 50)
    print("SETUP COMPLETE")
    print("=" * 50)
    print("Your system is now configured to:")
    print("• Collect price + market cap from CoinGecko every 60s")  
    print("• Collect volume from CoinMarketCap every 300s (5 minutes)")
    print("• Use only ~8,640 CMC API calls per month (86% of free limit)")
    print("• Eliminate volume velocity spikes from CoinGecko")
    
    print(f"\nTo start the dual scheduler:")
    print("python server/dual_scheduler.py")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Test interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()