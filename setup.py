from setuptools import find_packages, setup

setup(
    name="football-predictor",
    version="0.1.0",
    description="足球赛果预测系统",
    author="Development Team",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "asyncpg>=0.29.0",
        "sqlalchemy[asyncio]>=2.0.23",
        "alembic>=1.13.1",
        "xgboost>=2.0.2",
        "scikit-learn>=1.3.2",
        "pandas>=2.1.4",
        "numpy>=1.25.2",
        "prefect>=2.14.21",
        "httpx>=0.25.2",
        "beautifulsoup4>=4.12.2",
        "lxml>=4.9.3",
        "prometheus-client>=0.19.0",
        "structlog>=23.2.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "ruff>=0.1.6",
            "mypy>=1.7.1",
            "bandit>=1.8.0",
        ]
    },
)
