# 🚀 部署指南 - Football Prediction System v3.0

> 生产环境部署完整指南

## 🎯 部署概览

### 支持的部署方式

- **Docker Compose** (推荐)
- **Docker Swarm**
- **Kubernetes**
- **云平台** (AWS/Azure/GCP)

### 环境要求

- **Docker**: 20.0+
- **Docker Compose**: 2.0+
- **内存**: 至少 2GB
- **存储**: 至少 10GB

## 🐳 Docker Compose 部署 (推荐)

### 1. 准备环境

```bash
# 克隆项目
git clone https://github.com/xupeng211/football.git
cd football-predict-system

# 创建生产环境配置
cp env.template .env.production
```

### 2. 配置环境变量

```bash
# 编辑生产配置
vim .env.production

# 必须修改的配置
ENV=production
SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://postgres:secure_password@postgres:5432/football_db
REDIS_URL=redis://redis:6379/0
```

### 3. 启动服务

```bash
# 构建镜像
make build

# 启动生产环境
docker-compose --env-file .env.production up -d

# 查看状态
docker-compose ps
```

### 4. 健康检查

```bash
# 检查API健康状态
curl http://localhost:8000/health

# 检查指标
curl http://localhost:8000/metrics
```

## ☸️ Kubernetes 部署

### 1. 准备 Kubernetes 清单

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: football-predict

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: football-predict-api
  namespace: football-predict
spec:
  replicas: 3
  selector:
    matchLabels:
      app: football-predict-api
  template:
    metadata:
      labels:
        app: football-predict-api
    spec:
      containers:
      - name: api
        image: football-predict:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: football-secret
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: football-secret
              key: redis-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: football-predict-service
  namespace: football-predict
spec:
  selector:
    app: football-predict-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### 2. 部署到 Kubernetes

```bash
# 创建命名空间
kubectl apply -f k8s/namespace.yaml

# 创建密钥
kubectl create secret generic football-secret \
  --from-literal=database-url="postgresql://..." \
  --from-literal=redis-url="redis://..." \
  -n football-predict

# 部署应用
kubectl apply -f k8s/

# 查看状态
kubectl get pods -n football-predict
kubectl get services -n football-predict
```

## ☁️ 云平台部署

### AWS ECS

```bash
# 1. 构建并推送镜像到 ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-west-2.amazonaws.com

docker tag football-predict:latest 123456789012.dkr.ecr.us-west-2.amazonaws.com/football-predict:latest
docker push 123456789012.dkr.ecr.us-west-2.amazonaws.com/football-predict:latest

# 2. 创建 ECS 任务定义
# 3. 创建 ECS 服务
# 4. 配置 ALB 负载均衡器
```

### Google Cloud Run

```bash
# 1. 构建镜像
gcloud builds submit --tag gcr.io/PROJECT_ID/football-predict

# 2. 部署到 Cloud Run
gcloud run deploy football-predict \
  --image gcr.io/PROJECT_ID/football-predict \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Container Instances

```bash
# 1. 创建资源组
az group create --name football-predict-rg --location eastus

# 2. 部署容器
az container create \
  --resource-group football-predict-rg \
  --name football-predict-app \
  --image football-predict:latest \
  --dns-name-label football-predict \
  --ports 8000
```

## 🔧 生产配置优化

### 1. 性能配置

```yaml
# docker-compose.production.yml
version: '3.8'
services:
  app:
    image: football-predict:latest
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    environment:
      - WORKERS=4
      - MAX_CONNECTIONS=100
      - TIMEOUT=30
```

### 2. 数据库优化

```sql
-- PostgreSQL 生产配置优化
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

### 3. Redis 配置

```conf
# redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60
```

## 📊 监控和日志

### 1. Prometheus 监控

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'football-predict'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### 2. Grafana 仪表板

```bash
# 启动监控服务
docker-compose --profile monitoring up -d

# 访问 Grafana
open http://localhost:3000
# 用户名: admin
# 密码: admin123
```

### 3. 日志收集

```yaml
# docker-compose.yml 日志配置
version: '3.8'
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
```

## 🔐 安全配置

### 1. SSL/TLS 配置

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/private/privkey.pem;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. 防火墙配置

```bash
# UFW 防火墙配置
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw deny 8000/tcp   # 阻止直接访问应用端口
ufw enable
```

### 3. 密钥管理

```bash
# 使用 Docker Secrets
echo "your-secret-key" | docker secret create db_password -
echo "your-redis-password" | docker secret create redis_password -
```

## 🔄 CI/CD 自动部署

### GitHub Actions 自动部署

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Build and Deploy
      run: |
        docker build -t football-predict:${{ github.sha }} .
        
        # 推送到镜像仓库
        docker tag football-predict:${{ github.sha }} ${{ secrets.REGISTRY }}/football-predict:latest
        docker push ${{ secrets.REGISTRY }}/football-predict:latest
        
        # 部署到生产环境
        ssh ${{ secrets.DEPLOY_HOST }} '
          docker pull ${{ secrets.REGISTRY }}/football-predict:latest
          docker-compose up -d --no-deps app
        '
```

## 🚨 故障排除

### 常见问题

#### 1. 容器启动失败

```bash
# 查看日志
docker-compose logs app

# 检查配置
docker-compose config

# 重启服务
docker-compose restart app
```

#### 2. 数据库连接问题

```bash
# 测试数据库连接
docker-compose exec app python -c "
from src.football_predict_system.core.database import get_database_manager
db = get_database_manager()
print('Database connection:', db.get_engine())
"
```

#### 3. 内存不足

```bash
# 检查内存使用
docker stats

# 优化内存配置
export WORKERS=2
export MAX_CONNECTIONS=50
```

#### 4. 性能问题

```bash
# 查看性能指标
curl http://localhost:8000/metrics

# 分析慢查询
docker-compose exec postgres psql -U postgres -d football_db -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

## 🔄 备份和恢复

### 数据库备份

```bash
# 自动备份脚本
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 备份数据库
docker-compose exec postgres pg_dump -U postgres football_db > "${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql"

# 清理旧备份 (保留7天)
find ${BACKUP_DIR} -name "db_backup_*.sql" -mtime +7 -delete
```

### 恢复数据

```bash
# 恢复数据库
docker-compose exec postgres psql -U postgres football_db < backup.sql

# 恢复Redis数据
docker-compose exec redis redis-cli --rdb dump.rdb
```

## 📋 部署检查清单

### 部署前检查

- [ ] 环境变量已正确配置
- [ ] 密钥已安全存储
- [ ] 数据库已初始化
- [ ] SSL证书已配置
- [ ] 防火墙规则已设置
- [ ] 监控已启用

### 部署后验证

- [ ] 健康检查通过
- [ ] API接口正常
- [ ] 数据库连接正常
- [ ] 缓存工作正常
- [ ] 日志输出正常
- [ ] 监控指标正常

### 性能基准

- [ ] 响应时间 < 100ms
- [ ] 错误率 < 0.1%
- [ ] 可用性 > 99.9%
- [ ] 内存使用 < 80%
- [ ] CPU使用 < 70%

---

*部署成功！🎉 系统现在运行在生产环境中！*
