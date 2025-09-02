#!/usr/bin/env python3
"""
Data Platform Setup Script - 数据中台一键设置

Usage:
    python scripts/data_platform/setup_data_platform.py --help
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sqlalchemy import text

from football_predict_system.core.config import get_settings
from football_predict_system.core.database import get_database_manager
from football_predict_system.core.logging import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


class DataPlatformSetup:
    """Data platform setup and management."""

    def __init__(self):
        self.settings = get_settings()
        self.db_manager = get_database_manager()

    async def setup_database(self) -> bool:
        """Setup database schema."""
        logger.info("Setting up database schema...")

        try:
            # Read schema file
            schema_file = Path(__file__).parent.parent.parent / "sql" / "schema.sql"

            if not schema_file.exists():
                logger.error(f"Schema file not found: {schema_file}")
                return False

            with open(schema_file, encoding="utf-8") as f:
                schema_sql = f.read()

            # Execute schema
            async with self.db_manager.get_async_session() as session:
                # Split by semicolon and execute each statement
                statements = [s.strip() for s in schema_sql.split(";") if s.strip()]

                for statement in statements:
                    if statement:
                        await session.execute(text(statement))

                await session.commit()

            logger.info("Database schema setup completed")
            return True

        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            return False

    async def verify_api_access(self) -> bool:
        """Verify API access."""
        logger.info("Verifying API access...")

        if not self.settings.football_data_api_key:
            logger.error("FOOTBALL_DATA_API_KEY not configured")
            return False

        try:
            from football_predict_system.data_platform.sources.football_data_api import (
                FootballDataAPICollector,
            )

            collector = FootballDataAPICollector()
            df = await collector.fetch_competitions()
            await collector.close()

            logger.info(f"API access verified - {len(df)} competitions available")
            return True

        except Exception as e:
            logger.error(f"API verification failed: {e}")
            return False

    async def create_sample_data(self) -> bool:
        """Create sample data for testing."""
        logger.info("Creating sample data...")

        try:
            from football_predict_system.data_platform.sources.football_data_api import (
                POPULAR_COMPETITIONS,
                FootballDataAPICollector,
            )
            from football_predict_system.data_platform.storage.database_writer import (
                DatabaseWriter,
            )

            collector = FootballDataAPICollector()
            writer = DatabaseWriter()

            # Get Premier League teams
            teams_df = await collector.fetch_teams(
                POPULAR_COMPETITIONS["premier_league"]
            )

            if not teams_df.empty:
                result = await writer.upsert_teams(teams_df)
                logger.info(f"Sample teams created: {result}")

            # Get recent matches
            recent_matches = await collector.fetch_matches(
                competition_id=POPULAR_COMPETITIONS["premier_league"],
                date_from=datetime.utcnow() - timedelta(days=7),
                date_to=datetime.utcnow(),
            )

            if not recent_matches.empty:
                result = await writer.upsert_matches(recent_matches)
                logger.info(f"Sample matches created: {result}")

            await collector.close()
            logger.info("Sample data creation completed")
            return True

        except Exception as e:
            logger.error(f"Sample data creation failed: {e}")
            return False

    async def health_check(self) -> dict:
        """Perform comprehensive health check."""
        logger.info("Performing data platform health check...")

        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "database": False,
            "api_access": False,
            "data_freshness": False,
            "overall_status": "unhealthy",
        }

        try:
            # Database check
            async with self.db_manager.get_async_session() as session:
                result = await session.execute(text("SELECT 1"))
                health_status["database"] = result.scalar() == 1

            # API check
            health_status["api_access"] = await self.verify_api_access()

            # Data freshness check
            try:
                async with self.db_manager.get_async_session() as session:
                    result = await session.execute(
                        text("""
                        SELECT COUNT(*) FROM matches
                        WHERE created_at >= NOW() - INTERVAL '24 hours'
                        """)
                    )
                    recent_count = result.scalar()
                    health_status["data_freshness"] = recent_count > 0
            except Exception as e:
                logger.warning(f"数据新鲜度检查失败: {e}")
                health_status["data_freshness"] = False

            # Overall status
            if all([health_status["database"], health_status["api_access"]]):
                health_status["overall_status"] = "healthy"
            elif health_status["database"]:
                health_status["overall_status"] = "degraded"

            return health_status

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["error"] = str(e)
            return health_status


async def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Football Data Platform Setup")
    parser.add_argument(
        "--action",
        choices=["setup", "verify", "sample", "health"],
        default="setup",
        help="Action to perform",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force setup (recreate schema)"
    )

    args = parser.parse_args()

    setup = DataPlatformSetup()

    if args.action == "setup":
        logger.info("🚀 Starting data platform setup...")

        # Setup database
        if await setup.setup_database():
            logger.info("✅ Database setup completed")
        else:
            logger.error("❌ Database setup failed")
            return 1

        # Verify API access
        if await setup.verify_api_access():
            logger.info("✅ API access verified")
        else:
            logger.warning("⚠️ API access verification failed")

        logger.info("🎉 Data platform setup completed!")

    elif args.action == "verify":
        logger.info("🔍 Verifying data platform...")

        if await setup.verify_api_access():
            logger.info("✅ API access OK")
        else:
            logger.error("❌ API access failed")
            return 1

    elif args.action == "sample":
        logger.info("📊 Creating sample data...")

        if await setup.create_sample_data():
            logger.info("✅ Sample data created")
        else:
            logger.error("❌ Sample data creation failed")
            return 1

    elif args.action == "health":
        logger.info("🏥 Performing health check...")

        health = await setup.health_check()

        print("\n" + "=" * 50)
        print("📊 DATA PLATFORM HEALTH REPORT")
        print("=" * 50)
        print(f"Timestamp: {health['timestamp']}")
        print(f"Database: {'✅' if health['database'] else '❌'}")
        print(f"API Access: {'✅' if health['api_access'] else '❌'}")
        print(f"Data Freshness: {'✅' if health['data_freshness'] else '❌'}")
        print(f"Overall Status: {health['overall_status'].upper()}")

        if "error" in health:
            print(f"Error: {health['error']}")

        print("=" * 50)

        return 0 if health["overall_status"] == "healthy" else 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
