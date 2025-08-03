from database import SessionLocal, BitcoinPrice
import pandas as pd
from datetime import datetime

def test_gui_query(limit=10):
    """Test the GUI database query"""
    print(f"Testing GUI query with limit={limit}")
    
    db = SessionLocal()
    try:
        # Get the most recent entries, then reverse for chronological order
        prices = db.query(BitcoinPrice).order_by(BitcoinPrice.timestamp.desc()).limit(limit).all()
        prices.reverse()  # Now oldest to newest for proper chart display
        
        if prices:
            print(f"Retrieved {len(prices)} entries:")
            for i, price in enumerate(prices):
                age = datetime.utcnow() - price.timestamp
                print(f"   {i+1}. ${price.price:,.2f} at {price.timestamp} (age: {age})")
            
            # Create DataFrame like GUI does
            df = pd.DataFrame([
                {
                    'timestamp': price.timestamp,
                    'price': price.price,
                    'volume_24h': price.volume_24h,
                    'market_cap': price.market_cap
                }
                for price in prices
            ])
            
            print(f"\nDataFrame created with {len(df)} rows")
            print(f"Time range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            return df
        else:
            print("No data retrieved")
            return pd.DataFrame()
    finally:
        db.close()

if __name__ == "__main__":
    df = test_gui_query(5)
    if not df.empty:
        print("\nLast few prices from DataFrame:")
        print(df[['timestamp', 'price']].tail())