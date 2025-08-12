#!/usr/bin/env python3
"""
Test different cryptocurrency data sources
Compare reliability and data quality of volume measurements
"""

import sys
import os
import asyncio
import json
from datetime import datetime, timedelta

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from server.implementations.multi_source_provider import MultiSourceProvider


async def test_data_sources():
    """Test and compare multiple data sources"""
    
    print("Cryptocurrency Data Source Reliability Test")
    print("=" * 50)
    
    # Initialize multi-source provider
    provider = MultiSourceProvider()
    
    # Test parameters
    test_rounds = 5
    test_interval = 10  # seconds between tests
    
    print(f"\nRunning {test_rounds} test rounds (every {test_interval}s)...")
    print("This will help identify which sources provide the most stable volume data.")
    
    results = []
    
    for round_num in range(1, test_rounds + 1):
        print(f"\n--- Round {round_num}/{test_rounds} ---")
        
        try:
            # Fetch data from all sources
            data = await provider.fetch_current_price('bitcoin')
            
            if data:
                result = {
                    'round': round_num,
                    'timestamp': datetime.utcnow().isoformat(),
                    'price': data.price,
                    'volume_24h': data.volume_24h,
                    'market_cap': data.market_cap
                }
                results.append(result)
                
                print(f"Price: ${data.price:,.2f}")
                print(f"Volume: ${data.volume_24h:,.0f}" if data.volume_24h else "Volume: None")
                print(f"Market Cap: ${data.market_cap:,.0f}" if data.market_cap else "Market Cap: None")
            else:
                print("No data received")
                results.append({
                    'round': round_num,
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': 'No data received'
                })
        
        except Exception as e:
            print(f"Error in round {round_num}: {e}")
            results.append({
                'round': round_num,
                'timestamp': datetime.utcnow().isoformat(),
                'error': str(e)
            })
        
        # Wait before next round (except last)
        if round_num < test_rounds:
            print(f"Waiting {test_interval}s...")
            await asyncio.sleep(test_interval)
    
    # Analyze results
    print(f"\n" + "=" * 50)
    print("ANALYSIS RESULTS")
    print("=" * 50)
    
    successful_rounds = [r for r in results if 'error' not in r]
    failed_rounds = [r for r in results if 'error' in r]
    
    print(f"Success rate: {len(successful_rounds)}/{test_rounds} ({len(successful_rounds)/test_rounds*100:.1f}%)")
    
    if failed_rounds:
        print(f"Failed rounds: {[r['round'] for r in failed_rounds]}")
    
    if len(successful_rounds) > 1:
        # Analyze volume stability
        volumes = [r['volume_24h'] for r in successful_rounds if r['volume_24h']]
        
        if len(volumes) > 1:
            min_vol = min(volumes)
            max_vol = max(volumes)
            avg_vol = sum(volumes) / len(volumes)
            variance = max_vol - min_vol
            variance_pct = (variance / min_vol) * 100 if min_vol > 0 else 0
            
            print(f"\nVolume Analysis:")
            print(f"  Average: ${avg_vol:,.0f}")
            print(f"  Range: ${min_vol:,.0f} - ${max_vol:,.0f}")
            print(f"  Variance: ${variance:,.0f} ({variance_pct:.2f}%)")
            
            # Check for suspicious spikes
            if variance_pct > 5:  # More than 5% variance
                print(f"  WARNING: HIGH VARIANCE DETECTED ({variance_pct:.1f}%)")
                print(f"  This suggests data quality issues similar to our current problem")
            else:
                print(f"  GOOD: LOW VARIANCE ({variance_pct:.1f}% - Good stability)")
        
        # Analyze price stability  
        prices = [r['price'] for r in successful_rounds if r['price']]
        
        if len(prices) > 1:
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
            price_variance = max_price - min_price
            price_variance_pct = (price_variance / min_price) * 100 if min_price > 0 else 0
            
            print(f"\nPrice Analysis:")
            print(f"  Average: ${avg_price:,.2f}")
            print(f"  Range: ${min_price:,.2f} - ${max_price:,.2f}")
            print(f"  Variance: ${price_variance:,.2f} ({price_variance_pct:.3f}%)")
    
    # Save detailed results
    results_file = f"data/source_test_results_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to: {results_file}")
    except Exception as e:
        print(f"\nCould not save results file: {e}")
    
    # Recommendations
    print(f"\n" + "=" * 50)
    print("RECOMMENDATIONS")
    print("=" * 50)
    
    if len(successful_rounds) >= test_rounds * 0.8:  # 80% success rate
        print("GOOD: Data source appears reliable for basic connectivity")
    else:
        print("BAD: Data source has connectivity issues")
    
    if len(successful_rounds) > 1:
        volumes = [r['volume_24h'] for r in successful_rounds if r['volume_24h']]
        if volumes and len(volumes) > 1:
            variance_pct = ((max(volumes) - min(volumes)) / min(volumes)) * 100
            
            if variance_pct < 1:
                print("EXCELLENT: Volume data is very stable - excellent for analytics")
            elif variance_pct < 5:
                print("GOOD: Volume data has acceptable stability")
            elif variance_pct < 20:
                print("WARNING: Volume data shows moderate variance - consider smoothing")
            else:
                print("BAD: Volume data is highly unstable - try different source")
    
    print(f"\nNext steps:")
    print(f"  1. Run this test with longer intervals (60s, 5min)")
    print(f"  2. Test during different market hours")
    print(f"  3. Compare with your current CoinGecko data")
    print(f"  4. Consider implementing multi-source averaging")


async def test_specific_source():
    """Test a specific data source in detail"""
    print("Individual Source Testing")
    print("=" * 30)
    
    provider = MultiSourceProvider()
    
    # Test each source individually
    sources = ['coingecko', 'coinmarketcap', 'mobula', 'binance']
    
    for source_name in sources:
        print(f"\nTesting {source_name}...")
        try:
            if source_name == 'coingecko':
                result = await provider._fetch_coingecko('bitcoin')
            elif source_name == 'coinmarketcap':
                result = await provider._fetch_coinmarketcap('bitcoin')
            elif source_name == 'mobula':
                result = await provider._fetch_mobula('bitcoin')
            elif source_name == 'binance':
                result = await provider._fetch_binance('bitcoin')
            
            if result:
                print(f"  SUCCESS")
                print(f"  Price: ${result.price:,.2f}")
                print(f"  Volume: ${result.volume_24h:,.0f}" if result.volume_24h else "  Volume: Not available")
                print(f"  Market Cap: ${result.market_cap:,.0f}" if result.market_cap else "  Market Cap: Not available")
            else:
                print(f"  FAILED - No data returned")
                
        except Exception as e:
            print(f"  ERROR: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--individual":
        asyncio.run(test_specific_source())
    else:
        asyncio.run(test_data_sources())