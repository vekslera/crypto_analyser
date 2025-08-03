import asyncio
from bitcoin_service import BitcoinService
from database import SessionLocal, BitcoinPrice
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_api_fetch():
    """Test if we can fetch current Bitcoin price"""
    print("🔍 Testing API fetch...")
    service = BitcoinService()
    
    try:
        price_data = await service.fetch_bitcoin_price()
        if price_data:
            print(f"✅ API fetch successful: ${price_data['price']:,.2f}")
            print(f"   Timestamp: {price_data['timestamp']}")
            print(f"   Market Cap: ${price_data.get('market_cap', 0):,.0f}")
            print(f"   24h Volume: ${price_data.get('volume_24h', 0):,.0f}")
            return True
        else:
            print("❌ API fetch failed - no data returned")
            return False
    except Exception as e:
        print(f"❌ API fetch error: {e}")
        return False

def check_database():
    """Check recent database entries"""
    print("\n🔍 Checking database...")
    db = SessionLocal()
    
    try:
        # Count total entries
        total_count = db.query(BitcoinPrice).count()
        print(f"📊 Total database entries: {total_count}")
        
        if total_count == 0:
            print("❌ No data in database")
            return False
        
        # Get most recent entries
        recent_entries = db.query(BitcoinPrice).order_by(BitcoinPrice.timestamp.desc()).limit(10).all()
        
        print(f"📈 Most recent {len(recent_entries)} entries:")
        for i, entry in enumerate(recent_entries):
            age = datetime.utcnow() - entry.timestamp
            print(f"   {i+1}. ${entry.price:,.2f} at {entry.timestamp} (⏰ {age} ago)")
        
        # Check if we have recent data (within last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_count = db.query(BitcoinPrice).filter(BitcoinPrice.timestamp > one_hour_ago).count()
        
        if recent_count > 0:
            print(f"✅ Found {recent_count} entries in the last hour")
            return True
        else:
            print("⚠️  No entries in the last hour - scheduler might not be running")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        db.close()

async def test_full_collection():
    """Test a complete data collection cycle"""
    print("\n🔍 Testing full collection cycle...")
    
    # Test API fetch
    api_ok = await test_api_fetch()
    if not api_ok:
        return False
    
    # Test database write
    service = BitcoinService()
    try:
        price_data = await service.fetch_bitcoin_price()
        if price_data:
            db = SessionLocal()
            try:
                db_price = BitcoinPrice(
                    price=price_data['price'],
                    timestamp=price_data['timestamp'],
                    volume_24h=price_data.get('volume_24h'),
                    market_cap=price_data.get('market_cap')
                )
                db.add(db_price)
                db.commit()
                print("✅ Database write successful")
                
                # Test pandas series
                service.add_to_series(price_data['price'], price_data['timestamp'])
                series_count = len(service.data_series)
                print(f"✅ Pandas series updated - now has {series_count} entries")
                
                return True
                
            except Exception as e:
                db.rollback()
                print(f"❌ Database write failed: {e}")
                return False
            finally:
                db.close()
    except Exception as e:
        print(f"❌ Collection test failed: {e}")
        return False

def check_coingecko_rate_limits():
    """Check if we're hitting CoinGecko rate limits"""
    print("\n🔍 Checking CoinGecko API status...")
    import requests
    
    try:
        # Test with a simple ping
        response = requests.get("https://api.coingecko.com/api/v3/ping", timeout=10)
        if response.status_code == 200:
            print("✅ CoinGecko API is accessible")
            
            # Check rate limit headers
            if 'x-ratelimit-remaining' in response.headers:
                remaining = response.headers['x-ratelimit-remaining']
                print(f"📊 Rate limit remaining: {remaining}")
            
            return True
        else:
            print(f"⚠️  CoinGecko API returned status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CoinGecko API check failed: {e}")
        return False

async def main():
    print("🚀 Bitcoin Data Collection Diagnostics")
    print("=" * 50)
    
    # Run all tests
    api_ok = await test_api_fetch()
    db_ok = check_database()
    coingecko_ok = check_coingecko_rate_limits()
    collection_ok = await test_full_collection()
    
    print("\n📋 Summary:")
    print(f"   API Fetch: {'✅' if api_ok else '❌'}")
    print(f"   Database: {'✅' if db_ok else '❌'}")
    print(f"   CoinGecko API: {'✅' if coingecko_ok else '❌'}")
    print(f"   Full Collection: {'✅' if collection_ok else '❌'}")
    
    if not db_ok:
        print("\n💡 Recommendations:")
        print("   - Check if the scheduler is running")
        print("   - Verify network connectivity")
        print("   - Check if there are any error logs")
        print("   - Try restarting the application")

if __name__ == "__main__":
    asyncio.run(main())