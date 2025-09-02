#!/usr/bin/env python3
"""
Quick start script for Football Data Platform.

One-command setup and data collection.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from setup_data_platform import DataPlatformSetup


async def quick_start():
    """Quick start the data platform."""

    print("🏆 Football Data Platform - Quick Start")
    print("="*60)

    setup = DataPlatformSetup()

    # Step 1: Health check
    print("1️⃣ Checking current status...")
    health = await setup.health_check()

    if health["overall_status"] == "healthy":
        print("✅ System is already healthy!")
    else:
        print("🔧 Setting up missing components...")

        # Step 2: Setup database if needed
        if not health["database"]:
            print("2️⃣ Setting up database...")
            if await setup.setup_database():
                print("✅ Database setup completed")
            else:
                print("❌ Database setup failed")
                return 1

        # Step 3: Verify API access
        if not health["api_access"]:
            print("3️⃣ Verifying API access...")
            if await setup.verify_api_access():
                print("✅ API access verified")
            else:
                print("❌ API access failed - check your API key")
                return 1

    # Step 4: Create sample data
    print("4️⃣ Creating sample data...")
    if await setup.create_sample_data():
        print("✅ Sample data created")
    else:
        print("⚠️ Sample data creation had issues")

    # Final health check
    print("5️⃣ Final verification...")
    final_health = await setup.health_check()

    print("\n" + "="*60)
    print("📊 SETUP COMPLETE")
    print("="*60)
    print(f"Status: {final_health['overall_status'].upper()}")
    print(f"Database: {'✅' if final_health['database'] else '❌'}")
    print(f"API Access: {'✅' if final_health['api_access'] else '❌'}")
    print(f"Data Available: {'✅' if final_health['data_freshness'] else '❌'}")

    if final_health["overall_status"] == "healthy":
        print("\n🎉 Your data platform is ready!")
        print("\n📋 Next steps:")
        print("   • Run historical backfill: make data-backfill")
        print("   • Start daily collection: make data-collect")
        print("   • Monitor data quality: make data-monitor")
        print("   • View data dashboard: http://localhost:8000/docs")
    else:
        print("\n⚠️ Setup completed with warnings")
        print("   Check the logs above for details")

    return 0 if final_health["overall_status"] in ["healthy", "degraded"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(quick_start())
    sys.exit(exit_code)
