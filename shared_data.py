import pandas as pd
import threading
from datetime import datetime
from typing import Dict, Any

class SharedDataStore:
    """Singleton class to share data between scheduler and GUI"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.data_series = pd.Series(dtype=float, name='bitcoin_price')
            self._data_lock = threading.Lock()
            self._initialized = True
    
    def add_price(self, price: float, timestamp: datetime = None) -> None:
        """Thread-safe method to add price data"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        with self._data_lock:
            self.data_series[timestamp] = price
    
    def get_recent_data(self, limit: int = 100) -> pd.Series:
        """Thread-safe method to get recent data"""
        with self._data_lock:
            return self.data_series.tail(limit).copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Thread-safe method to get statistics"""
        with self._data_lock:
            if len(self.data_series) == 0:
                return {}
            
            return {
                'count': len(self.data_series),
                'mean': float(self.data_series.mean()),
                'std': float(self.data_series.std()),
                'min': float(self.data_series.min()),
                'max': float(self.data_series.max()),
                'latest': float(self.data_series.iloc[-1]) if len(self.data_series) > 0 else None
            }
    
    def clear_data(self) -> None:
        """Thread-safe method to clear all data"""
        with self._data_lock:
            self.data_series = pd.Series(dtype=float, name='bitcoin_price')

# Global instance
shared_data = SharedDataStore()