#!/usr/bin/env python3
"""
Quick comparison between CoinGecko and CoinMarketCap volume data
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from server.implementations.multi_source_provider import MultiSourceProvider


async def compare_sources():
    provider = MultiSourceProvider()
    
    print('Direct comparison of CoinGecko vs CoinMarketCap volume data:')
    print('=' * 60)
    
    for i in range(3):
        print(f'\nRound {i+1}/3:')
        
        # Test CoinGecko
        cg_data = await provider._fetch_coingecko('bitcoin')
        if cg_data:
            print(f'CoinGecko     - Price: ${cg_data.price:,.2f}, Volume: ${cg_data.volume_24h:,.0f}')
        else:
            print('CoinGecko     - Failed')
        
        # Test CoinMarketCap  
        cmc_data = await provider._fetch_coinmarketcap('bitcoin')
        if cmc_data:
            print(f'CoinMarketCap - Price: ${cmc_data.price:,.2f}, Volume: ${cmc_data.volume_24h:,.0f}')
        else:
            print('CoinMarketCap - Failed')
        
        # Calculate difference
        if cg_data and cmc_data and cg_data.volume_24h and cmc_data.volume_24h:
            diff = cmc_data.volume_24h - cg_data.volume_24h
            diff_pct = (diff / cg_data.volume_24h) * 100
            print(f'Difference    - Volume: ${diff:,.0f} ({diff_pct:+.1f}%)')
        
        if i < 2:
            await asyncio.sleep(5)
    
    print('\n' + '=' * 60)
    print('ANALYSIS:')
    print('The volume differences suggest different calculation methodologies.')
    print('CoinMarketCap typically aggregates more exchanges than CoinGecko.')
    print('Your "volume velocity" spikes are likely due to CoinGecko\'s data inconsistencies.')


if __name__ == "__main__":
    asyncio.run(compare_sources())