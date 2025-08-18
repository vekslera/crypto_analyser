"""
Gap filling service for data collection
Integrates the gap detection and filling functionality into the backend
"""

import sys
import os
import sqlite3
import requests
import time
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import logging
import numpy as np

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from ..interfaces.database_interface import DatabaseRepository, PriceData

logger = logging.getLogger(__name__)


class GapFillingService:
    """Service for detecting and filling data gaps"""
    
    def __init__(self, database_repo: DatabaseRepository):
        self.database_repo = database_repo
        
    async def detect_gaps(self, min_gap_hours: float = 1.0, check_recent_days: int = 30) -> List[Dict[str, Any]]:
        """Detect all gaps > specified hours in the database, including gaps from missing recent data"""
        
        logger.info(f"Detecting gaps larger than {min_gap_hours} hours (checking last {check_recent_days} days)")
        
        # Get all price data ordered by timestamp
        all_prices = await self.database_repo.get_price_history(limit=50000)  # Get large dataset
        
        gaps = []
        now = datetime.now(timezone.utc)
        
        if len(all_prices) == 0:
            # Database is completely empty - treat entire recent period as one big gap
            start_time = now - timedelta(days=check_recent_days)
            logger.info(f"Database is empty - creating gap for entire {check_recent_days}-day period")
            gaps.append({
                'start': start_time,
                'end': now,
                'duration_hours': check_recent_days * 24
            })
            return gaps
        
        # Sort by timestamp
        all_prices.sort(key=lambda x: x.timestamp)
        
        # Check for gap from last record to now
        latest_record = all_prices[-1]
        latest_time = latest_record.timestamp
        if latest_time.tzinfo is None:
            latest_time = latest_time.replace(tzinfo=timezone.utc)
        
        gap_to_now = (now - latest_time).total_seconds() / 3600
        if gap_to_now > min_gap_hours:
            logger.info(f"Found gap from last record to now: {gap_to_now:.1f} hours")
            gaps.append({
                'start': latest_time,
                'end': now,
                'duration_hours': gap_to_now
            })
        
        # Check for gap from start of recent period to first record
        earliest_record = all_prices[0]
        earliest_time = earliest_record.timestamp
        if earliest_time.tzinfo is None:
            earliest_time = earliest_time.replace(tzinfo=timezone.utc)
        
        recent_start = now - timedelta(days=check_recent_days)
        gap_from_start = (earliest_time - recent_start).total_seconds() / 3600
        
        if gap_from_start > min_gap_hours and earliest_time > recent_start:
            logger.info(f"Found gap from start of recent period to first record: {gap_from_start:.1f} hours")
            gaps.append({
                'start': recent_start,
                'end': earliest_time,
                'duration_hours': gap_from_start
            })
        
        # Find gaps between existing records (original logic)
        for i in range(1, len(all_prices)):
            prev_time = all_prices[i-1].timestamp
            curr_time = all_prices[i].timestamp
            
            # Ensure timezone-aware comparison
            if prev_time.tzinfo is None:
                prev_time = prev_time.replace(tzinfo=timezone.utc)
            if curr_time.tzinfo is None:
                curr_time = curr_time.replace(tzinfo=timezone.utc)
            
            # Only check gaps within the recent period
            if prev_time >= recent_start or curr_time >= recent_start:
                gap_hours = (curr_time - prev_time).total_seconds() / 3600
                
                if gap_hours > min_gap_hours:
                    gaps.append({
                        'start': prev_time,
                        'end': curr_time,
                        'duration_hours': gap_hours
                    })
        
        # Sort gaps by start time
        gaps.sort(key=lambda x: x['start'])
        
        logger.info(f"Found {len(gaps)} gaps > {min_gap_hours} hours in recent {check_recent_days} days")
        return gaps
    
    def fetch_coingecko_data_for_range(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Fetch CoinGecko data for a specific time range"""
        
        # Calculate days difference
        duration = (end_time - start_time).total_seconds() / (24 * 3600)
        
        logger.info(f"Fetching {duration:.1f} days of data from CoinGecko")
        
        # CoinGecko market_chart/range endpoint
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range"
        
        # Convert to Unix timestamps (seconds)
        from_timestamp = int(start_time.timestamp())
        to_timestamp = int(end_time.timestamp())
        
        params = {
            'vs_currency': 'usd',
            'from': from_timestamp,
            'to': to_timestamp
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                prices = data.get('prices', [])
                market_caps = data.get('market_caps', [])
                total_volumes = data.get('total_volumes', [])
                
                logger.info(f"Received {len(prices)} data points from CoinGecko")
                
                # Process into records
                records = []
                for i in range(len(prices)):
                    timestamp_ms = prices[i][0]
                    price = prices[i][1]
                    
                    # Convert timestamp from milliseconds to datetime
                    timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
                    
                    # Get corresponding data
                    market_cap = market_caps[i][1] if i < len(market_caps) else None
                    volume_24h = total_volumes[i][1] if i < len(total_volumes) else None
                    
                    record = {
                        'timestamp': timestamp,
                        'price': price,
                        'volume_24h': volume_24h,
                        'market_cap': market_cap,
                        'volume_velocity': None,
                        'volatility': None,
                        'money_flow': None
                    }
                    
                    records.append(record)
                
                return records
                
            else:
                logger.error(f"CoinGecko API failed with status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching from CoinGecko: {e}")
            return []
    
    async def fill_gap(self, gap: Dict[str, Any]) -> int:
        """Fill a single gap with CoinGecko data"""
        
        gap_start = gap['start']
        gap_end = gap['end']
        duration_hours = gap['duration_hours']
        
        logger.info(f"Filling gap: {gap_start} to {gap_end} ({duration_hours:.1f}h)")
        
        # Fetch data for this range (extend slightly to ensure coverage)
        fetch_start = gap_start - timedelta(minutes=30)
        fetch_end = gap_end + timedelta(minutes=30)
        
        records = self.fetch_coingecko_data_for_range(fetch_start, fetch_end)
        
        if not records:
            logger.warning(f"No data received for gap")
            return 0
        
        # Filter records to only include the gap period (avoid duplicates)
        gap_records = []
        for record in records:
            if gap_start < record['timestamp'] < gap_end:
                gap_records.append(record)
        
        logger.info(f"Filtered to {len(gap_records)} records for gap period")
        
        if not gap_records:
            logger.warning(f"No records in gap period after filtering")
            return 0
        
        # Convert to PriceData objects and save
        inserted_count = 0
        for record in gap_records:
            try:
                price_data = PriceData(
                    price=record['price'],
                    timestamp=record['timestamp'],
                    volume_24h=record['volume_24h'],
                    volume_velocity=record['volume_velocity'],
                    market_cap=record['market_cap'],
                    volatility=record['volatility'],
                    money_flow=record['money_flow']
                )
                
                # Save to database (database should handle duplicates)
                success = await self.database_repo.save_price(price_data)
                if success:
                    inserted_count += 1
                    
            except Exception as e:
                logger.error(f"Error saving gap record: {e}")
                continue
        
        logger.info(f"Inserted {inserted_count} records for gap")
        return inserted_count
    
    async def fill_all_gaps(self, min_gap_hours: float = 1.0, max_gaps: int = 10, check_recent_days: int = 30) -> Dict[str, Any]:
        """Fill all detected gaps with rate limiting"""
        
        logger.info(f"Starting comprehensive gap filling (max {max_gaps} gaps, checking last {check_recent_days} days)")
        
        try:
            # Step 1: Detect all gaps
            gaps = await self.detect_gaps(min_gap_hours, check_recent_days)
            
            if not gaps:
                return {
                    'success': True,
                    'message': 'No gaps found! Database has continuous coverage.',
                    'gaps_filled': 0,
                    'records_inserted': 0
                }
            
            # Step 2: Sort gaps by size (fill largest first for efficiency)
            gaps_sorted = sorted(gaps, key=lambda x: x['duration_hours'], reverse=True)
            
            # Limit number of gaps to fill in one operation
            gaps_to_fill = gaps_sorted[:max_gaps]
            
            logger.info(f"Filling {len(gaps_to_fill)} largest gaps out of {len(gaps_sorted)} total")
            
            total_inserted = 0
            successful_fills = 0
            
            for i, gap in enumerate(gaps_to_fill):
                logger.info(f"Processing gap {i+1}/{len(gaps_to_fill)}: {gap['duration_hours']:.1f} hours")
                
                # Add delay between API calls to respect rate limits
                if i > 0:
                    logger.info("Waiting 2 seconds for rate limiting...")
                    time.sleep(2)
                
                inserted = await self.fill_gap(gap)
                total_inserted += inserted
                
                if inserted > 0:
                    successful_fills += 1
                
                # Add longer delay for large gaps
                if gap['duration_hours'] > 24:
                    logger.info("Waiting 5 seconds after large gap...")
                    time.sleep(5)
            
            # After successful gap filling, recalculate volatility for the new data
            volatility_result = await self.recalculate_volatility_for_recent_data(days_back=35)
            
            return {
                'success': True,
                'message': f'Gap filling complete! Filled {successful_fills} gaps with {total_inserted} records. Volatility recalculated for {volatility_result.get("records_updated", 0)} records.',
                'gaps_detected': len(gaps_sorted),
                'gaps_filled': successful_fills,
                'records_inserted': total_inserted,
                'remaining_gaps': len(gaps_sorted) - len(gaps_to_fill),
                'volatility_updated': volatility_result.get("records_updated", 0)
            }
            
        except Exception as e:
            logger.error(f"Error during gap filling: {e}")
            return {
                'success': False,
                'message': f'Gap filling failed: {str(e)}',
                'gaps_filled': 0,
                'records_inserted': 0
            }
    
    async def recalculate_volatility_for_recent_data(self, days_back: int = 35) -> Dict[str, Any]:
        """Recalculate volatility for recent data including backfilled records"""
        try:
            logger.info(f"Recalculating volatility for last {days_back} days of data")
            
            # Get recent data that might need volatility calculation
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
            all_prices = await self.database_repo.get_price_history(limit=10000)
            
            if len(all_prices) < 25:  # Need at least 25 records for 24h volatility
                logger.warning("Insufficient data for volatility calculation")
                return {
                    'success': False,
                    'message': 'Insufficient data for volatility calculation',
                    'records_updated': 0
                }
            
            # Sort by timestamp
            all_prices.sort(key=lambda x: x.timestamp)
            
            # Filter recent data
            recent_data = []
            for price_data in all_prices:
                timestamp = price_data.timestamp
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                if timestamp >= cutoff_date:
                    recent_data.append(price_data)
            
            if len(recent_data) < 25:
                logger.warning(f"Insufficient recent data: {len(recent_data)} records")
                return {
                    'success': False,
                    'message': f'Insufficient recent data: {len(recent_data)} records',
                    'records_updated': 0
                }
            
            logger.info(f"Processing {len(recent_data)} recent records for volatility")
            
            # Calculate volatility using pandas for efficiency
            df = pd.DataFrame([{
                'timestamp': r.timestamp,
                'price': r.price
            } for r in all_prices if r.price is not None])
            
            if len(df) < 25:
                return {
                    'success': False,
                    'message': 'Insufficient price data for volatility calculation',
                    'records_updated': 0
                }
            
            # Calculate returns
            df['returns'] = df['price'].pct_change()
            
            # Calculate 24-hour rolling volatility (annualized)
            # Assuming 5-minute intervals: 288 periods = 24 hours
            window_size = min(288, len(df) // 4)  # Adaptive window size
            df['volatility'] = df['returns'].rolling(window=window_size, min_periods=24).std() * np.sqrt(365 * 288) * 100
            
            # Update records in database
            updated_count = 0
            for price_data in recent_data:
                # Find corresponding volatility
                matching_rows = df[df['timestamp'] == price_data.timestamp]
                if not matching_rows.empty and not pd.isna(matching_rows.iloc[0]['volatility']):
                    volatility = float(matching_rows.iloc[0]['volatility'])
                    
                    # Update the record directly in database
                    try:
                        # Create updated PriceData object
                        updated_price_data = PriceData(
                            price=price_data.price,
                            timestamp=price_data.timestamp,
                            volume_24h=price_data.volume_24h,
                            volume_velocity=None,  # Not used anymore
                            market_cap=price_data.market_cap,
                            volatility=volatility,
                            money_flow=price_data.money_flow
                        )
                        
                        # Update in database
                        success = await self._update_record_volatility(price_data.timestamp, volatility)
                        if success:
                            updated_count += 1
                            
                    except Exception as e:
                        logger.warning(f"Failed to update volatility for {price_data.timestamp}: {e}")
                        continue
            
            logger.info(f"Updated volatility for {updated_count} records")
            return {
                'success': True,
                'message': f'Volatility recalculated for {updated_count} records',
                'records_updated': updated_count,
                'total_recent_records': len(recent_data)
            }
            
        except Exception as e:
            logger.error(f"Error recalculating volatility: {e}")
            return {
                'success': False,
                'message': f'Volatility recalculation failed: {str(e)}',
                'records_updated': 0
            }
    
    async def _update_record_volatility(self, timestamp: datetime, volatility: float) -> bool:
        """Update volatility for a specific record"""
        try:
            # Use direct SQL update for efficiency
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, 'data', 'crypto_analyser.db')
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE bitcoin_prices 
                SET volatility = ? 
                WHERE timestamp = ?
            """, (volatility, timestamp))
            
            conn.commit()
            conn.close()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Failed to update record volatility: {e}")
            return False