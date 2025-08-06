# API Setup Guide

## CoinMarketCap API (Free Tier)

To use CoinMarketCap as an additional data source:

### 1. Get Free API Key
1. Visit https://coinmarketcap.com/api/
2. Click "Get Your API Key Now" (free)
3. Sign up with email (no credit card required)
4. Copy your API key from the dashboard

### 2. Set Environment Variable
**Windows:**
```bash
set CMC_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export CMC_API_KEY=your_api_key_here
```

### 3. Test the Integration
```bash
python scripts/test_data_sources.py --individual
```

### Free Tier Limits
- ✅ **10,000 calls/month** (≈333/day)
- ✅ **30 requests/minute**
- ✅ **Current market data**
- ❌ **No historical data**
- ⚠️ **Personal use only**

## Why Multiple Sources?

Our analysis shows different APIs provide **vastly different** volume data:

- **CoinGecko**: $35B+ (global aggregation)
- **CoinMarketCap**: $XX B (to be tested)
- **Mobula**: $400M (different methodology)  
- **Binance**: $1.2B (single exchange)

Using multiple sources helps us:
1. **Identify data reliability**
2. **Cross-validate volume spikes**
3. **Choose most stable source**
4. **Implement fallback options**

## Current Issue

Our volume velocity shows extreme spikes (±$2B/min) likely due to:
- CoinGecko data feed inconsistencies
- Exchange reporting delays
- API caching artifacts

Testing alternative sources will help identify if this is CoinGecko-specific or a general crypto data problem.