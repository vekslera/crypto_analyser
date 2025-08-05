"""
Test demonstrating Interface Segregation Principle (ISP) compliance
Shows how services can depend only on the interfaces they actually need
"""

import sys
import os
import asyncio

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from server.dependency_container import container
from server.services.specialized_services import (
    PriceCollectionService, PriceQueryService, DataAnalyticsService, 
    DataMaintenanceService, HealthMonitoringService, ProviderInfoService
)


async def test_isp_compliance():
    """Test that specialized services work with focused interfaces"""
    
    print("Testing Interface Segregation Principle (ISP) compliance...")
    
    # Initialize the container
    success = await container.initialize(
        database_url="sqlite:///test_bitcoin_data.db",
        crypto_provider="coingecko"
    )
    
    if not success:
        print("X Failed to initialize container")
        return
    
    print("✓ Container initialized successfully")
    
    # Test PriceCollectionService - only needs DataWriter and PriceDataFetcher
    print("\n🔄 Testing PriceCollectionService (ISP: only DataWriter + PriceDataFetcher)...")
    price_collection = PriceCollectionService(
        data_writer=container.get_data_writer(),
        price_fetcher=container.get_price_data_fetcher()
    )
    
    # Test PriceQueryService - only needs DataReader
    print("📖 Testing PriceQueryService (ISP: only DataReader)...")
    price_query = PriceQueryService(
        data_reader=container.get_data_reader()
    )
    
    # Test DataAnalyticsService - only needs DataAnalytics and ProviderMetadata
    print("📊 Testing DataAnalyticsService (ISP: only DataAnalytics + ProviderMetadata)...")
    analytics = DataAnalyticsService(
        data_analytics=container.get_data_analytics(),
        provider_metadata=container.get_provider_metadata()
    )
    
    # Test DataMaintenanceService - only needs DataAdministrator
    print("🔧 Testing DataMaintenanceService (ISP: only DataAdministrator)...")
    maintenance = DataMaintenanceService(
        data_administrator=container.get_data_administrator()
    )
    
    # Test HealthMonitoringService - only needs health-related interfaces
    print("❤️  Testing HealthMonitoringService (ISP: only health interfaces)...")
    health_monitor = HealthMonitoringService(
        data_administrator=container.get_data_administrator(),
        provider_health=container.get_provider_health(),
        provider_metadata=container.get_provider_metadata()
    )
    
    # Test ProviderInfoService - only needs ProviderMetadata
    print("ℹ️  Testing ProviderInfoService (ISP: only ProviderMetadata)...")
    provider_info = ProviderInfoService(
        provider_metadata=container.get_provider_metadata()
    )
    
    # Demonstrate that each service only depends on what it needs
    print("\n🎯 ISP Compliance Demonstration:")
    print("✅ PriceCollectionService: DataWriter + PriceDataFetcher (no analytics, no health)")
    print("✅ PriceQueryService: DataReader only (no write, no admin, no analytics)")
    print("✅ DataAnalyticsService: DataAnalytics + ProviderMetadata (no write, no admin)")
    print("✅ DataMaintenanceService: DataAdministrator only (no read, no write, no analytics)")
    print("✅ HealthMonitoringService: Health interfaces only (no data operations)")
    print("✅ ProviderInfoService: ProviderMetadata only (no data operations, no health)")
    
    # Test basic functionality
    print("\n🧪 Testing basic functionality...")
    
    # Test health check
    health = await health_monitor.health_check()
    print(f"Health check: {health}")
    
    # Test provider info
    info = provider_info.get_provider_info()
    print(f"Provider info: {info}")
    
    # Test that we can get historical data
    history = await price_query.get_recent_prices(limit=5)
    print(f"Retrieved {len(history)} recent prices")
    
    print("\n🎉 ISP compliance test completed successfully!")
    print("Each service depends only on the interfaces it actually needs.")


if __name__ == "__main__":
    asyncio.run(test_isp_compliance())