#!/usr/bin/env python3
"""
Run the optimal scheduler with verbose logging enabled
Shows all detailed logs for volume fetching and DB insertion
"""

import sys
import os
import logging
import asyncio

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def setup_verbose_logging():
    """Set up verbose logging to see all details"""
    
    # Create logs directory
    logs_dir = os.path.join(project_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure root logger for maximum verbosity
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Console handler - shows everything
            logging.StreamHandler(sys.stdout),
            # File handler - saves everything to file
            logging.FileHandler(os.path.join(logs_dir, 'optimal_scheduler_verbose.log'), mode='w')
        ]
    )
    
    # Set specific loggers to DEBUG level
    loggers_to_debug = [
        'server.optimal_scheduler',
        'server.services.crypto_service', 
        'server.implementations.multi_source_provider',
        'server.implementations.coingecko_provider',
        'server.dependency_container'
    ]
    
    for logger_name in loggers_to_debug:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
    
    print("Verbose logging enabled for:")
    for logger_name in loggers_to_debug:
        print(f"  • {logger_name}")
    print()


async def initialize_system():
    """Initialize the system with proper database path"""
    from server.dependency_container import container
    
    # Use the correct database path
    db_url = f"sqlite:///{os.path.join(project_root, 'data', 'crypto_analyser.db')}"
    
    print(f"Initializing system with database: {db_url}")
    
    success = await container.initialize(
        database_url=db_url,
        crypto_provider="coingecko"  # Will use CoinGecko for price, CMC for volume
    )
    
    if not success:
        print("❌ Failed to initialize dependency container")
        return False
    
    print("✅ System initialized successfully")
    return True


def main():
    """Main function to run the optimal scheduler with verbose logging"""
    
    print("OPTIMAL SCHEDULER - VERBOSE LOGGING MODE")
    print("=" * 50)
    print("This will show detailed logs for:")
    print("  • CoinGecko price fetching (every 60s)")
    print("  • CoinMarketCap volume fetching (every 300s)")
    print("  • Price buffer management and smoothing")
    print("  • Volume velocity calculations")
    print("  • Database insertion operations")
    print("  • Error handling and fallbacks")
    print()
    
    # Set up verbose logging
    setup_verbose_logging()
    
    # Initialize system
    print("Initializing system...")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(initialize_system())
        if not success:
            return
        
        print("Starting optimal scheduler...")
        print("Press Ctrl+C to stop")
        print("-" * 50)
        
        # Import and start scheduler
        from server.optimal_scheduler import OptimalScheduler
        
        scheduler = OptimalScheduler()
        scheduler.start_scheduler()
        
    except KeyboardInterrupt:
        print("\n" + "=" * 50)
        print("Scheduler stopped by user")
    except Exception as e:
        print(f"\n❌ Scheduler failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        loop.close()


if __name__ == "__main__":
    main()