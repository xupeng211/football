# 环境配置指南

## 📋 快速配置

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑配置文件
vim .env  # 或使用您喜欢的编辑器

# 3. 验证配置
make validate-config
```

## 🔑 必需配置项

### 数据库配置
```bash
# PostgreSQL 连接信息
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=football_predict
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here
```

### 足球数据 API
```bash
# 申请地址: https://www.football-data.org/client/register
FOOTBALL_DATA_API_KEY=your_api_key_here
```

## 🌍 环境特定配置

### 开发环境 (development)
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
API_RELOAD=true
```

### 测试环境 (staging)
```bash
ENVIRONMENT=staging
DEBUG=false
LOG_LEVEL=INFO
API_RELOAD=false
```

### 生产环境 (production)
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
API_RELOAD=false
SECURITY_SCAN_ENABLED=true
```

## 🔒 安全最佳实践

### 密钥管理
- 所有密钥至少32字符
- 生产环境使用外部密钥管理服务
- 定期轮换API密钥

### 数据库安全
- 使用强密码
- 限制数据库访问权限
- 启用SSL连接（生产环境）

## 📊 监控配置

### Prometheus 指标
```bash
ENABLE_METRICS=true
METRICS_PORT=9090
METRICS_ENDPOINT=/metrics
```

### 日志配置
```bash
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json         # json, console
LOG_FILE_PATH=./logs/app.log
```

## 🧪 测试配置

### 测试数据库
```bash
# 使用独立的测试数据库避免污染开发数据
TEST_DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/football_predict_test
```

### 覆盖率配置
```bash
COVERAGE_THRESHOLD=80
PYTEST_WORKERS=auto
```

## 🚨 常见问题

### Q: 数据库连接失败
```bash
# 检查数据库是否运行
make docker-up
docker-compose ps

# 检查连接配置
psql $DATABASE_URL -c "SELECT 1;"
```

### Q: API密钥配置问题
```bash
# 验证API密钥
curl -H "X-Auth-Token: $FOOTBALL_DATA_API_KEY" \
     https://api.football-data.org/v4/competitions

# 检查配额
curl -I -H "X-Auth-Token: $FOOTBALL_DATA_API_KEY" \
     https://api.football-data.org/v4/competitions
```

### Q: Redis连接问题
```bash
# 测试Redis连接
redis-cli -u $REDIS_URL ping
```

## 🔄 配置验证

运行以下命令验证配置：

```bash
# 验证所有配置
make validate-config

# 验证数据库连接
make test-db-connection

# 验证API密钥
make test-api-keys
```
