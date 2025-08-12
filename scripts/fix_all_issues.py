#!/usr/bin/env python3
"""
Fix all the identified issues:
1. Add missing volume_velocity column to database
2. Fix CMC Unicode issue
3. Fix duplicate logging
"""

import sys
import os
import sqlite3

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def fix_database_schema():
    """Add missing volume_velocity column to database"""
    
    print("FIXING DATABASE SCHEMA")
    print("=" * 30)
    
    db_path = os.path.join(project_root, "data", "crypto_analyser.db")
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if volume_velocity column exists
        cursor.execute("PRAGMA table_info(bitcoin_prices)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"Current columns: {columns}")
        
        if 'volume_velocity' not in columns:
            print("Adding volume_velocity column...")
            cursor.execute("ALTER TABLE bitcoin_prices ADD COLUMN volume_velocity REAL")
            conn.commit()
            print("SUCCESS: volume_velocity column added successfully")
        else:
            print("OK: volume_velocity column already exists")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: fixing database: {e}")
        return False


def test_cmc_fetch():
    """Test CMC fetch to identify Unicode issues"""
    
    print("\nTESTING CMC FETCH")
    print("=" * 30)
    
    try:
        import asyncio
        from server.implementations.multi_source_provider import MultiSourceProvider
        
        async def test_fetch():
            provider = MultiSourceProvider()
            
            print("Testing CoinMarketCap fetch...")
            try:
                data = await provider._fetch_coinmarketcap("bitcoin")
                if data:
                    print("SUCCESS: CMC fetch successful!")
                    print(f"  Price: ${data.price:,.2f}")
                    print(f"  Volume: ${data.volume_24h:,.0f}")
                    return True
                else:
                    print("ERROR: CMC fetch returned no data")
                    return False
            except Exception as e:
                print(f"ERROR: CMC fetch error: {e}")
                print(f"Error type: {type(e)}")
                if 'codec' in str(e).lower() or 'unicode' in str(e).lower():
                    print("DIAGNOSIS: This appears to be a Unicode/encoding issue")
                return False
        
        result = asyncio.run(test_fetch())
        return result
        
    except Exception as e:
        print(f"ERROR: testing CMC: {e}")
        return False


def fix_logging_duplication():
    """Provide instructions to fix duplicate logging"""
    
    print("\nFIXING LOGGING DUPLICATION")
    print("=" * 30)
    
    print("Issue: Logs appear twice due to multiple handlers")
    print("Solution: Modify run_with_gui.py to prevent handler duplication")
    print()
    print("The fix is to check if handlers already exist before adding new ones.")
    print("This has been noted for the code update.")


def main():
    """Run all fixes"""
    
    print("FIXING ALL IDENTIFIED ISSUES")
    print("=" * 40)
    
    # Fix 1: Database schema
    db_fixed = fix_database_schema()
    
    # Fix 2: Test CMC fetch
    cmc_working = test_cmc_fetch()
    
    # Fix 3: Note logging fix needed
    fix_logging_duplication()
    
    print("\nSUMMARY")
    print("=" * 20)
    print(f"Database schema: {'FIXED' if db_fixed else 'NEEDS ATTENTION'}")
    print(f"CMC fetch: {'WORKING' if cmc_working else 'NEEDS FIXING'}")
    print("Logging duplication: CODE UPDATE NEEDED")
    
    if db_fixed and cmc_working:
        print("\nMost issues resolved! Ready to test OptimalScheduler")
    else:
        print("\nSome issues remain - see details above")


if __name__ == "__main__":
    main()