# 📡 API 文档 - Football Prediction System v3.0

> REST API 接口完整指南

## 🎯 API 概览

### 基础信息

- **Base URL**: `http://localhost:8000`
- **API Version**: v1
- **Content-Type**: `application/json`
- **Authentication**: Bearer Token (可选)

### API 特性

- **RESTful 设计**
- **JSON 响应格式**
- **自动文档生成**
- **请求验证**
- **错误处理**
- **速率限制**

## 📚 快速导航

### 核心接口

- [健康检查](#-健康检查) - 系统状态
- [预测接口](#-预测接口) - 比赛预测
- [模型信息](#-模型接口) - 模型管理
- [数据接口](#-数据接口) - 历史数据

### 工具接口

- [监控指标](#-监控接口) - 系统指标
- [API文档](#-文档接口) - 交互式文档

## 🏥 健康检查

### GET /health

系统健康状态检查

```bash
curl -X GET "http://localhost:8000/health"
```

**响应示例**:

```json
{
  "status": "healthy",
  "timestamp": "2025-09-01T14:30:00Z",
  "version": "3.0.0",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "model": "healthy"
  },
  "uptime": 3600.5
}
```

**状态码**:

- `200` - 系统健康
- `503` - 系统异常

## ⚽ 预测接口

### POST /api/v1/predict

足球比赛结果预测

**请求体**:

```json
{
  "home_team": "Liverpool",
  "away_team": "Manchester City",
  "match_date": "2025-09-15T15:00:00Z",
  "league": "Premier League",
  "venue": "Anfield"
}
```

**请求示例**:

```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "home_team": "Liverpool",
    "away_team": "Manchester City",
    "match_date": "2025-09-15T15:00:00Z"
  }'
```

**响应示例**:

```json
{
  "prediction": {
    "result": "home_win",
    "probabilities": {
      "home_win": 0.45,
      "draw": 0.28,
      "away_win": 0.27
    },
    "confidence": 0.82,
    "expected_goals": {
      "home": 2.1,
      "away": 1.3
    }
  },
  "match_info": {
    "home_team": "Liverpool",
    "away_team": "Manchester City",
    "match_date": "2025-09-15T15:00:00Z",
    "league": "Premier League"
  },
  "model_info": {
    "version": "v2.1",
    "training_date": "2025-08-01T00:00:00Z",
    "features_used": 15
  },
  "request_id": "req_123456789",
  "timestamp": "2025-09-01T14:30:00Z"
}
```

### POST /api/v1/predict/batch

批量预测多场比赛

**请求体**:

```json
{
  "matches": [
    {
      "home_team": "Liverpool",
      "away_team": "Manchester City"
    },
    {
      "home_team": "Arsenal",
      "away_team": "Chelsea"
    }
  ]
}
```

**响应示例**:

```json
{
  "predictions": [
    {
      "match_id": 0,
      "prediction": {
        "result": "home_win",
        "probabilities": {
          "home_win": 0.45,
          "draw": 0.28,
          "away_win": 0.27
        }
      }
    },
    {
      "match_id": 1,
      "prediction": {
        "result": "away_win",
        "probabilities": {
          "home_win": 0.22,
          "draw": 0.31,
          "away_win": 0.47
        }
      }
    }
  ],
  "total_predictions": 2,
  "batch_id": "batch_123456789"
}
```

## 🤖 模型接口

### GET /api/v1/models

获取可用模型列表

```bash
curl -X GET "http://localhost:8000/api/v1/models"
```

**响应示例**:

```json
{
  "models": [
    {
      "id": "xgboost_v2.1",
      "name": "XGBoost Predictor v2.1",
      "type": "xgboost",
      "status": "active",
      "accuracy": 0.73,
      "training_date": "2025-08-01T00:00:00Z",
      "features_count": 15
    }
  ],
  "default_model": "xgboost_v2.1"
}
```

### GET /api/v1/models/{model_id}/info

获取特定模型详细信息

```bash
curl -X GET "http://localhost:8000/api/v1/models/xgboost_v2.1/info"
```

**响应示例**:

```json
{
  "model_id": "xgboost_v2.1",
  "name": "XGBoost Predictor v2.1",
  "version": "2.1.0",
  "type": "xgboost",
  "status": "active",
  "metrics": {
    "accuracy": 0.73,
    "precision": 0.71,
    "recall": 0.74,
    "f1_score": 0.72
  },
  "training_info": {
    "training_date": "2025-08-01T00:00:00Z",
    "training_samples": 50000,
    "validation_samples": 12500,
    "features_count": 15
  },
  "feature_importance": [
    {"feature": "home_form", "importance": 0.15},
    {"feature": "away_form", "importance": 0.12},
    {"feature": "head_to_head", "importance": 0.11}
  ]
}
```

## 📊 数据接口

### GET /api/v1/teams

获取支持的球队列表

```bash
curl -X GET "http://localhost:8000/api/v1/teams?league=Premier League"
```

**查询参数**:

- `league` (可选): 联赛名称
- `limit` (可选): 返回数量限制
- `offset` (可选): 分页偏移

**响应示例**:

```json
{
  "teams": [
    {
      "id": "liverpool",
      "name": "Liverpool",
      "league": "Premier League",
      "country": "England",
      "founded": 1892
    },
    {
      "id": "man_city",
      "name": "Manchester City",
      "league": "Premier League",
      "country": "England",
      "founded": 1880
    }
  ],
  "total": 20,
  "limit": 10,
  "offset": 0
}
```

### GET /api/v1/matches/history

获取历史比赛数据

```bash
curl -X GET "http://localhost:8000/api/v1/matches/history?team=Liverpool&limit=10"
```

**查询参数**:

- `team` (可选): 球队名称
- `league` (可选): 联赛名称
- `date_from` (可选): 开始日期
- `date_to` (可选): 结束日期
- `limit` (可选): 返回数量
- `offset` (可选): 分页偏移

**响应示例**:

```json
{
  "matches": [
    {
      "id": "match_123",
      "date": "2025-08-15T15:00:00Z",
      "home_team": "Liverpool",
      "away_team": "Manchester United",
      "score": {
        "home": 2,
        "away": 1
      },
      "result": "home_win",
      "league": "Premier League"
    }
  ],
  "total": 150,
  "limit": 10,
  "offset": 0
}
```

## 📈 监控接口

### GET /metrics

Prometheus 格式指标

```bash
curl -X GET "http://localhost:8000/metrics"
```

**响应示例**:

```
# HELP prediction_requests_total Total prediction requests
# TYPE prediction_requests_total counter
prediction_requests_total{method="POST",endpoint="/api/v1/predict"} 1234

# HELP prediction_duration_seconds Prediction duration
# TYPE prediction_duration_seconds histogram
prediction_duration_seconds_bucket{le="0.1"} 500
prediction_duration_seconds_bucket{le="0.5"} 800
prediction_duration_seconds_bucket{le="1.0"} 950
```

### GET /api/v1/stats

系统统计信息

```bash
curl -X GET "http://localhost:8000/api/v1/stats"
```

**响应示例**:

```json
{
  "predictions": {
    "total": 12345,
    "today": 234,
    "last_hour": 45
  },
  "accuracy": {
    "last_30_days": 0.72,
    "last_7_days": 0.74
  },
  "performance": {
    "avg_response_time": 0.125,
    "p95_response_time": 0.250
  },
  "cache": {
    "hit_rate": 0.85,
    "total_hits": 8500,
    "total_misses": 1500
  }
}
```

## 📖 文档接口

### GET /docs

Swagger UI 交互式文档

访问: `http://localhost:8000/docs`

### GET /redoc

ReDoc 文档

访问: `http://localhost:8000/redoc`

### GET /openapi.json

OpenAPI 规范

```bash
curl -X GET "http://localhost:8000/openapi.json"
```

## 🔐 认证 (可选)

### Bearer Token 认证

```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Liverpool", "away_team": "Chelsea"}'
```

### API Key 认证

```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Liverpool", "away_team": "Chelsea"}'
```

## ⚠️ 错误处理

### 标准错误格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid team name provided",
    "details": {
      "field": "home_team",
      "value": "Unknown Team",
      "constraint": "Team must be in supported list"
    }
  },
  "request_id": "req_123456789",
  "timestamp": "2025-09-01T14:30:00Z"
}
```

### 常见错误码

| 状态码 | 错误码 | 描述 |
|--------|--------|------|
| 400 | `VALIDATION_ERROR` | 请求参数验证失败 |
| 400 | `MISSING_REQUIRED_FIELD` | 缺少必需字段 |
| 401 | `AUTHENTICATION_REQUIRED` | 需要认证 |
| 403 | `PERMISSION_DENIED` | 权限不足 |
| 404 | `RESOURCE_NOT_FOUND` | 资源不存在 |
| 422 | `UNPROCESSABLE_ENTITY` | 数据格式错误 |
| 429 | `RATE_LIMIT_EXCEEDED` | 请求频率超限 |
| 500 | `INTERNAL_SERVER_ERROR` | 服务器内部错误 |
| 503 | `SERVICE_UNAVAILABLE` | 服务不可用 |

## 🚦 速率限制

### 限制规则

- **默认限制**: 100 requests/minute
- **预测接口**: 60 requests/minute
- **批量预测**: 10 requests/minute

### 响应头

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1693574400
```

## 📝 请求示例

### Python 客户端

```python
import requests

# 单次预测
response = requests.post(
    "http://localhost:8000/api/v1/predict",
    json={
        "home_team": "Liverpool",
        "away_team": "Manchester City"
    }
)
prediction = response.json()
print(f"预测结果: {prediction['prediction']['result']}")
```

### JavaScript 客户端

```javascript
// 使用 fetch API
const response = await fetch('http://localhost:8000/api/v1/predict', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        home_team: 'Liverpool',
        away_team: 'Manchester City'
    })
});

const prediction = await response.json();
console.log('预测结果:', prediction.prediction.result);
```

### curl 脚本

```bash
#!/bin/bash
# predict.sh - 快速预测脚本

HOME_TEAM=${1:-Liverpool}
AWAY_TEAM=${2:-Chelsea}

curl -s -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d "{\"home_team\": \"$HOME_TEAM\", \"away_team\": \"$AWAY_TEAM\"}" \
  | jq '.prediction.result'
```

## 🔧 SDK 和工具

### Python SDK

```bash
pip install football-predict-client
```

```python
from football_predict_client import Client

client = Client("http://localhost:8000")
prediction = client.predict("Liverpool", "Manchester City")
```

### Postman Collection

下载: [Football Predict API.postman_collection.json](./Football%20Predict%20API.postman_collection.json)

## 📊 性能基准

### 响应时间

- **健康检查**: < 10ms
- **单次预测**: < 100ms
- **批量预测**: < 500ms (10个预测)
- **历史数据**: < 200ms

### 吞吐量

- **最大 QPS**: 1000 requests/second
- **并发连接**: 500 connections
- **平均延迟**: 50ms

---

## 🤝 支持

### 获取帮助

- **文档**: [开发指南](./DEVELOPMENT.md)
- **Issues**: [GitHub Issues](https://github.com/xupeng211/football/issues)
- **讨论**: [GitHub Discussions](https://github.com/xupeng211/football/discussions)

### API 版本

- **当前版本**: v1
- **支持版本**: v1
- **弃用版本**: 无

---

*Happy Predicting! ⚽🎯*
