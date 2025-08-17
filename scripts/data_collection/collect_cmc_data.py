#!/usr/bin/env python3
"""
CoinMarketCap data collector with 60-second intervals
Stores data in database for volume velocity comparison
"""

import sys
import os
import asyncio
import sqlite3
import signal
from datetime import datetime, timedelta
import logging

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from server.implementations.multi_source_provider import MultiSourceProvider

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
running = True

def signal_handler(signum, frame):
    global running
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    running = False

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class CMCDataCollector:
    def __init__(self, db_path="data/bitcoin_data.db"):
        self.db_path = db_path
        self.provider = MultiSourceProvider()
        self.samples_collected = 0
        
    def initialize_db(self):
        """Initialize database table for CMC data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create CMC data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cmc_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                price FLOAT,
                volume_24h FLOAT,
                market_cap FLOAT,
                volume_velocity REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized for CMC data collection")
        
    def calculate_velocity(self):
        """Calculate volume velocity from last two data points"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get last two records
        cursor.execute("""
            SELECT timestamp, volume_24h 
            FROM cmc_data 
            ORDER BY timestamp DESC 
            LIMIT 2
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        if len(rows) < 2:
            return None
            
        # Calculate velocity: volume change per minute
        curr_time_str, curr_volume = rows[0]
        prev_time_str, prev_volume = rows[1]
        
        try:
            curr_time = datetime.fromisoformat(curr_time_str)
            prev_time = datetime.fromisoformat(prev_time_str)
            
            time_diff = (curr_time - prev_time).total_seconds() / 60  # minutes
            
            if time_diff > 0 and curr_volume is not None and prev_volume is not None:
                velocity = (curr_volume - prev_volume) / time_diff
                return velocity
        except:
            pass
            
        return None
    
    def update_velocity(self, velocity):
        """Update the last record with calculated velocity"""
        if velocity is None:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE cmc_data 
            SET volume_velocity = ? 
            WHERE id = (SELECT MAX(id) FROM cmc_data)
        """, (velocity,))
        
        conn.commit()
        conn.close()
    
    async def collect_sample(self):
        """Collect a single data sample"""
        try:
            # Fetch CoinMarketCap data
            data = await self.provider._fetch_coinmarketcap('bitcoin')
            
            if not data:
                logger.warning("No data received from CoinMarketCap")
                return False
            
            timestamp = datetime.utcnow()
            
            # Store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO cmc_data (timestamp, price, volume_24h, market_cap)
                VALUES (?, ?, ?, ?)
            """, (timestamp.isoformat(), data.price, data.volume_24h, data.market_cap))
            
            conn.commit()
            conn.close()
            
            # Calculate and update velocity
            velocity = self.calculate_velocity()
            if velocity is not None:
                self.update_velocity(velocity)
                velocity_str = f", Velocity: ${velocity:,.0f}/min"
            else:
                velocity_str = ""
            
            self.samples_collected += 1
            logger.info(f"Sample {self.samples_collected}: Price: ${data.price:,.2f}, "
                       f"Volume: ${data.volume_24h:,.0f}{velocity_str}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error collecting sample: {e}")
            return False
    
    async def run(self, duration_hours=1, interval_seconds=60):
        """Run the data collector"""
        global running
        
        self.initialize_db()
        
        end_time = datetime.utcnow() + timedelta(hours=duration_hours)
        logger.info(f"Starting CMC data collection for {duration_hours} hours")
        logger.info(f"Collecting every {interval_seconds} seconds")
        logger.info(f"Will collect until: {end_time}")
        logger.info("Press Ctrl+C to stop early")
        
        while running and datetime.utcnow() < end_time:
            success = await self.collect_sample()
            
            if not success:
                logger.warning("Failed to collect sample, continuing...")
            
            # Wait for next interval
            if running:
                logger.info(f"Waiting {interval_seconds}s for next sample...")
                try:
                    await asyncio.sleep(interval_seconds)
                except asyncio.CancelledError:
                    break
        
        logger.info(f"Data collection completed. Total samples: {self.samples_collected}")
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate a summary of collected data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM cmc_data")
        total_samples = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM cmc_data")
        time_range = cursor.fetchone()
        
        cursor.execute("SELECT AVG(volume_24h), MIN(volume_24h), MAX(volume_24h) FROM cmc_data WHERE volume_24h IS NOT NULL")
        volume_stats = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM cmc_data WHERE volume_velocity IS NOT NULL")
        velocity_count = cursor.fetchone()[0]
        
        conn.close()
        
        logger.info("=" * 50)
        logger.info("CMC DATA COLLECTION SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Total samples collected: {total_samples}")
        logger.info(f"Time range: {time_range[0]} to {time_range[1]}")
        logger.info(f"Volume statistics:")
        logger.info(f"  Average: ${volume_stats[0]:,.0f}")
        logger.info(f"  Range: ${volume_stats[1]:,.0f} - ${volume_stats[2]:,.0f}")
        logger.info(f"Velocity calculations: {velocity_count}")
        
        # Save summary to file
        summary_file = f"data/cmc_collection_summary_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        os.makedirs(os.path.dirname(summary_file), exist_ok=True)
        
        with open(summary_file, 'w') as f:
            f.write(f"CoinMarketCap Data Collection Summary\n")
            f.write("=" * 40 + "\n")
            f.write(f"Collection time: {datetime.utcnow()}\n")
            f.write(f"Total samples: {total_samples}\n")
            f.write(f"Time range: {time_range[0]} to {time_range[1]}\n")
            f.write(f"Average volume: ${volume_stats[0]:,.0f}\n")
            f.write(f"Volume range: ${volume_stats[1]:,.0f} - ${volume_stats[2]:,.0f}\n")
            f.write(f"Velocity calculations: {velocity_count}\n")
        
        logger.info(f"Summary saved to: {summary_file}")


async def main():
    collector = CMCDataCollector()
    
    # Default: collect for 1 hour every 60 seconds
    duration = 1  # hours
    interval = 60  # seconds
    
    # Allow command line arguments
    if len(sys.argv) > 1:
        try:
            duration = float(sys.argv[1])
        except:
            pass
    
    if len(sys.argv) > 2:
        try:
            interval = int(sys.argv[2])
        except:
            pass
    
    logger.info(f"CMC Data Collector - Duration: {duration}h, Interval: {interval}s")
    await collector.run(duration_hours=duration, interval_seconds=interval)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Collection stopped by user")
    except Exception as e:
        logger.error(f"Collection failed: {e}")