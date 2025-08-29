"""
Generate OpenAPI schema for the FastAPI application.
"""

import json
from pathlib import Path

from apps.api.main import app


def generate_openapi_schema() -> None:
    """Generates and saves the OpenAPI schema."""
    schema = app.openapi()

    # Define the output path
    output_dir = Path("docs/api")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "openapi.json"

    # Write the schema to the file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"✅ OpenAPI schema generated at {output_path}")


if __name__ == "__main__":
    generate_openapi_schema()
