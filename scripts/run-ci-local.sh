#!/bin/bash
set -e

# --- Configuration ---
IMAGE_NAME="football-ci-local"
CONTAINER_NAME="football-ci-runner"
DB_CONTAINER_NAME="football-db-local"
NETWORK_NAME="football-net-local"

# --- Cleanup Function ---
cleanup() {
    echo "\[CI] Cleaning up..."
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker stop "$DB_CONTAINER_NAME" >/dev/null 2>&1 || true
    docker rm "$DB_CONTAINER_NAME" >/dev/null 2>&1 || true
    docker network rm "$NETWORK_NAME" >/dev/null 2>&1 || true
    echo "\[CI] Cleanup complete."
}

# Register cleanup function to run on exit, error or interrupt
trap cleanup EXIT HUP INT QUIT TERM

# --- Build Docker Image ---
echo "\[CI] Building Docker image: $IMAGE_NAME..."
docker build -t "$IMAGE_NAME" .

# --- Setup Network and Database ---
echo "\[CI] Pulling PostgreSQL image..."
docker pull postgres:15

echo "\[CI] Setting up Docker network and database..."
docker network create "$NETWORK_NAME" >/dev/null 2>&1 || true
docker run -d --name "$DB_CONTAINER_NAME" \
    --network "$NETWORK_NAME" \
    -e POSTGRES_DB=football_test \
    -e POSTGRES_USER=football \
    -e POSTGRES_PASSWORD=football \
    postgres:15

# --- Wait for Database ---
echo "\[CI] Waiting for database to be ready..."
retries=10
while ! docker exec "$DB_CONTAINER_NAME" pg_isready -U football -d football_test >/dev/null 2>&1; do
    retries=$((retries-1))
    if [ $retries -eq 0 ]; then
        echo "\[CI] Database failed to start in time."
        exit 1
    fi
    sleep 2
done
echo "\[CI] Database is ready."

# --- Run CI Container ---
echo "\[CI] Starting CI container to run tests..."
docker run --name "$CONTAINER_NAME" \
    --network "$NETWORK_NAME" \
    -e DATABASE_URL="postgresql://football:football@$DB_CONTAINER_NAME:5432/football_test" \
    -e CI=true \
    "$IMAGE_NAME" \
    -c "
        set -e; \
        echo '--- Running Lint & Validate ---'; \
        make format; \
        make lint; \
        make type; \
        make security; \
        make validate; \
        echo '--- Running Tests ---'; \
        PGPASSWORD=football psql -h $DB_CONTAINER_NAME -U football -d football_test -f sql/schema.sql; \
        make test; \
    "

echo "\[CI] Local CI run completed successfully!"
