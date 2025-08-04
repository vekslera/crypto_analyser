import asyncio
from server.bitcoin_service import BitcoinService
from server.database import SessionLocal, BitcoinPrice
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    """Check database entries"""
    print("Checking database...")
    db = SessionLocal()
    
    try:
        # Count total entries
        total_count = db.query(BitcoinPrice).count()
        print(f"Total database entries: {total_count}")
        
        if total_count == 0:
            print("ERROR: No data in database")
            return False
        
        # Get most recent entries
        recent_entries = db.query(BitcoinPrice).order_by(BitcoinPrice.timestamp.desc()).limit(5).all()
        
        print(f"Most recent {len(recent_entries)} entries:")
        for i, entry in enumerate(recent_entries):
            age = datetime.utcnow() - entry.timestamp
            print(f"   {i+1}. ${entry.price:,.2f} at {entry.timestamp} (age: {age})")
        
        # Check if we have recent data (within last hour)
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_count = db.query(BitcoinPrice).filter(BitcoinPrice.timestamp > one_hour_ago).count()
        
        print(f"Entries in last hour: {recent_count}")
        
        if recent_count > 0:
            print("SUCCESS: Found recent entries")
            return True
        else:
            print("WARNING: No entries in the last hour")
            return False
            
    except Exception as e:
        print(f"DATABASE ERROR: {e}")
        return False
    finally:
        db.close()

async def test_api():
    """Test API fetch"""
    print("\nTesting API fetch...")
    service = BitcoinService()
    
    try:
        price_data = await service.fetch_bitcoin_price()
        if price_data:
            print(f"SUCCESS: API fetch ${price_data['price']:,.2f}")
            return price_data
        else:
            print("ERROR: API fetch failed")
            return None
    except Exception as e:
        print(f"API ERROR: {e}")
        return None

async def test_db_write():
    """Test database write"""
    print("\nTesting database write...")
    
    price_data = await test_api()
    if not price_data:
        return False
    
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
        print("SUCCESS: Database write completed")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"DATABASE WRITE ERROR: {e}")
        return False
    finally:
        db.close()

async def main():
    print("=== Bitcoin Database Diagnostics ===")
    
    # Check current database state
    db_ok = check_database()
    
    # Test API
    api_ok = await test_api()
    
    # Test database write
    write_ok = await test_db_write()
    
    print("\n=== SUMMARY ===")
    print(f"Database has data: {'YES' if db_ok else 'NO'}")
    print(f"API working: {'YES' if api_ok else 'NO'}")
    print(f"Database write: {'YES' if write_ok else 'NO'}")
    
    if not db_ok:
        print("\nRECOMMENDATIONS:")
        print("- Check if scheduler is running")
        print("- Check scheduler logs for errors")
        print("- Verify database permissions")

if __name__ == "__main__":
    asyncio.run(main())