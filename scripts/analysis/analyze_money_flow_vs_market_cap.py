#!/usr/bin/env python3
"""
Deep analysis of the relationship between actual money flow (X) and market cap change (S)

Key definitions:
- Money flow X: Net USD that flows into/out of the market through actual trades
- Market cap change S: Total circulating supply × price change per BTC

Question: What is the mathematical relationship between X and S?
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def analyze_money_flow_theory():
    """Theoretical analysis of money flow vs market cap change"""
    
    print("DEEP ANALYSIS: MONEY FLOW (X) vs MARKET CAP CHANGE (S)")
    print("=" * 65)
    
    print("\nDEFINITIONS:")
    print("-" * 12)
    print("X = Net money flow (USD actually traded)")
    print("S = Market cap change = Circulating Supply × Price Change")
    print("P = Price per BTC")
    print("Q = Circulating supply (approximately 19.9M BTC)")
    print("V = Volume of BTC actually traded")
    print("Delta_P = Price change per BTC")
    print()
    
    print("FUNDAMENTAL INSIGHT:")
    print("-" * 20)
    print("In every trade:")
    print("- Someone sells V BTC for V × P USD")
    print("- Someone buys V BTC for V × P USD") 
    print("- NET money flow = 0 in individual trades")
    print()
    print("But market prices change based on:")
    print("- Order book depth and liquidity")
    print("- Supply/demand imbalance")
    print("- Market maker behavior")
    print()
    
    print("THE KEY RELATIONSHIP:")
    print("-" * 21)
    print("When we say 'X USD entered the market', we mean:")
    print("- Trading volume V was executed at price P + Delta_P")
    print("- Instead of at the previous price P") 
    print("- So X = V × Delta_P (the extra USD per BTC × BTC traded)")
    print("- But S = Q × Delta_P (the price change × ALL circulating BTC)")
    print()
    print("Therefore: S = (Q/V) × X")
    print("Or: X = (V/Q) × S")
    print()
    
    print("AMPLIFICATION FACTOR:")
    print("-" * 21)
    print("Market Cap Amplification = Q/V = Circulating Supply / Trading Volume")
    print()
    
    # Example calculations
    Q = 19.9e6  # BTC circulating supply
    examples = [
        {"V": 1000, "name": "Small trade (1,000 BTC)"},
        {"V": 10000, "name": "Medium trade (10,000 BTC)"},
        {"V": 50000, "name": "Large trade (50,000 BTC)"},
        {"V": 100000, "name": "Whale trade (100,000 BTC)"},
    ]
    
    print("EXAMPLES:")
    print("-" * 9)
    for ex in examples:
        V = ex["V"]
        amplification = Q / V
        print(f"{ex['name']}:")
        print(f"  Trading volume: {V:,.0f} BTC")
        print(f"  Amplification factor: {amplification:.1f}x")
        print(f"  If Delta_P = $100: X = $100 × {V:,.0f} = ${V*100:,.0f}")
        print(f"  Market cap change: S = ${V*100:,.0f} × {amplification:.1f} = ${V*100*amplification:,.0f}")
        print()

def analyze_liquidity_impact():
    """Analyze how market liquidity affects the X to S relationship"""
    
    print("LIQUIDITY IMPACT ON X->S RELATIONSHIP:")
    print("=" * 40)
    
    print("MARKET DEPTH SCENARIOS:")
    print("-" * 24)
    
    scenarios = [
        {
            "name": "DEEP LIQUIDITY (Bull Market)",
            "volume_needed_for_1_dollar": 1e6,  # $1M volume for $1 price change
            "description": "High volume needed for small price changes"
        },
        {
            "name": "MEDIUM LIQUIDITY (Normal Market)",
            "volume_needed_for_1_dollar": 500e3,  # $500K volume for $1 price change
            "description": "Moderate volume needed for price changes"
        },
        {
            "name": "SHALLOW LIQUIDITY (Bear Market/Low Volume)",
            "volume_needed_for_1_dollar": 100e3,  # $100K volume for $1 price change
            "description": "Small volume causes large price changes"
        }
    ]
    
    Q = 19.9e6 * 118000  # Market cap in USD (approximate)
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"  {scenario['description']}")
        
        volume_per_dollar = scenario['volume_needed_for_1_dollar']
        
        # Calculate for $10M money flow
        money_flow = 10e6
        price_change = money_flow / volume_per_dollar
        market_cap_change = price_change * 19.9e6
        amplification = market_cap_change / money_flow
        
        print(f"  Example: $10M money flow:")
        print(f"    Price impact: ${price_change:.2f}")
        print(f"    Market cap change: ${market_cap_change:,.0f}")
        print(f"    Amplification: {amplification:.1f}x")
        
def analyze_real_world_complications():
    """Analyze real-world complications in the X→S relationship"""
    
    print("\nREAL-WORLD COMPLICATIONS:")
    print("=" * 30)
    
    print("1. MULTIPLE SIMULTANEOUS TRADES:")
    print("-" * 32)
    print("   - Multiple trades happen simultaneously across exchanges")
    print("   - Arbitrage bots smooth price differences")
    print("   - Net effect is combined impact on price")
    print()
    
    print("2. ORDER BOOK DYNAMICS:")
    print("-" * 25)
    print("   - Large orders consume multiple price levels")
    print("   - Price impact is non-linear with volume")
    print("   - Market makers adjust spreads based on volatility")
    print()
    
    print("3. PSYCHOLOGICAL EFFECTS:")
    print("-" * 24)
    print("   - Price changes trigger additional buying/selling")
    print("   - Stop-losses and liquidations cascade")
    print("   - FOMO and panic amplify price movements")
    print()
    
    print("4. EXCHANGE DIFFERENCES:")
    print("-" * 22)
    print("   - Different exchanges have different liquidity")
    print("   - Arbitrage opportunities create additional trading")
    print("   - Some volume is inter-exchange transfers (not new money)")
    print()

def provide_practical_implications():
    """Provide practical implications for our volume velocity analysis"""
    
    print("\nPRACTICAL IMPLICATIONS FOR VOLUME VELOCITY:")
    print("=" * 50)
    
    print("1. MARKET CAP VELOCITY IS MORE MEANINGFUL:")
    print("-" * 40)
    print("   - Shows the ACTUAL impact of money flow on valuation")
    print("   - Reflects what market participants experience")
    print("   - Captures the amplification effect automatically")
    print()
    
    print("2. VOLUME VELOCITY HAS LIMITATIONS:")
    print("-" * 35)
    print("   - 24h sliding window artifacts (as we discovered)")
    print("   - Doesn't account for market depth variations")
    print("   - Same volume can have vastly different price impacts")
    print()
    
    print("3. RELATIONSHIP VARIES BY MARKET CONDITIONS:")
    print("-" * 45)
    print("   - Bull markets: High liquidity → X/S ratio is smaller")
    print("   - Bear markets: Low liquidity → X/S ratio is larger") 
    print("   - Volatile periods: Non-linear relationship due to cascading effects")
    print()
    
    print("4. RECOMMENDED APPROACH:")
    print("-" * 25)
    print("   - Use MARKET CAP VELOCITY as primary indicator")
    print("   - It inherently includes:")
    print("     * Actual money flow impact (X)")
    print("     * Market amplification effects (Q/V)")
    print("     * Liquidity conditions (market depth)")
    print("     * Real-time price discovery")
    print()
    
    print("5. THEORETICAL FORMULA:")
    print("-" * 22)
    print("   Market Cap Velocity ≈ Net Money Flow × Amplification Factor")
    print("   Where Amplification Factor = Circulating Supply / Effective Trading Volume")
    print("   And varies with market liquidity conditions")

def mathematical_relationship_summary():
    """Provide mathematical summary of X→S relationship"""
    
    print("\nMATHEMATICAL SUMMARY:")
    print("=" * 25)
    
    print("CORE RELATIONSHIP:")
    print("  S = (Q/V) × X")
    print("  Where:")
    print("    S = Market cap change")
    print("    Q = Circulating supply") 
    print("    V = Effective trading volume")
    print("    X = Net money flow")
    print()
    
    print("AMPLIFICATION FACTOR:")
    print("  A = Q/V = Circulating Supply / Trading Volume")
    print("  Typical range: 50x to 2000x depending on market conditions")
    print()
    
    print("PRACTICAL INTERPRETATION:")
    print("  - Small money flows (X) create large market cap changes (S)")
    print("  - The amplification depends on market liquidity")
    print("  - Market cap velocity captures this relationship naturally")
    print("  - This explains why market cap moves more than trading volume")

if __name__ == "__main__":
    analyze_money_flow_theory()
    analyze_liquidity_impact() 
    analyze_real_world_complications()
    provide_practical_implications()
    mathematical_relationship_summary()