# 🛠️ Development Tools

This directory contains tools for local development and CI debugging.

## 📁 Contents

- `Dockerfile.ci-test-ubuntu24` - Ubuntu 24.04 CI simulation
- `ci-verify.sh` - Local CI verification script  
- `docker-compose.ci.yml` - Docker compose for CI testing

## 🚀 Usage

```bash
# Run local CI verification
cd dev-tools/
docker build -f Dockerfile.ci-test-ubuntu24 -t football-ci-ubuntu24 ..
docker run --rm -v "$(pwd)/..:/workspace" football-ci-ubuntu24

# Or use docker-compose
docker-compose -f docker-compose.ci.yml up ci-test
```
