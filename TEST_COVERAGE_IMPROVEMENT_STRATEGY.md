# 测试覆盖率提升策略

## 当前状态分析
- **总体覆盖率**: 71% (目标: 85%+)
- **测试通过**: 211个
- **主要问题**: 依赖缺失、API模块覆盖率低、核心服务测试不足

## 优先级分级策略

### P0 - 关键模块 (目标覆盖率: 90%+)
1. **apps/api/main.py** (当前: 13%)
   - FastAPI应用初始化
   - 中间件配置
   - 路由注册

2. **apps/api/services/prediction_service.py** (当前: 22%)
   - 核心预测服务逻辑
   - 业务流程关键组件

3. **models/predictor.py** (当前: 80% → 95%)
   - 模型预测核心逻辑
   - 异常处理路径

### P1 - 重要模块 (目标覆盖率: 80%+)
1. **apps/api/routers/predictions.py** (当前: 48%)
2. **apps/api/routers/health.py** (当前: 51%)
3. **models/registry.py** (当前: 78%)
4. **data_pipeline/features/build.py** (当前: 71%)

### P2 - 支持模块 (目标覆盖率: 70%+)
1. **apps/api/db.py** (当前: 55%)
2. **data_pipeline/contract_validator.py** (当前: 56%)
3. **trainer/fit_xgb.py** (当前: 66%)

## 实施计划

### 阶段1: 修复依赖和基础设施 ✅
- [x] 安装缺失依赖
- [x] 创建requirements.txt
- [x] 修复导入错误

### 阶段2: P0模块测试增强
1. **API主应用测试**
   - 应用启动测试
   - 中间件功能测试
   - 路由集成测试

2. **预测服务测试**
   - 服务初始化测试
   - 预测流程测试
   - 错误处理测试

### 阶段3: 集成测试和端到端测试
1. **API集成测试**
2. **完整预测流程测试**
3. **数据管道集成测试**

### 阶段4: 高级测试技术
1. **属性测试** (Hypothesis)
2. **变异测试** (Mutmut)
3. **性能测试**

## 测试工具配置

### 覆盖率监控
```bash
# 基础覆盖率
pytest --cov=. --cov-report=term-missing --cov-report=html

# 差异覆盖率
diff-cover coverage.xml --compare-branch=main

# 变异测试
mutmut run
```

### CI/CD集成
- GitHub Actions工作流
- 覆盖率阈值检查
- 自动化报告生成

## 成功指标
- 总体覆盖率: 71% → 85%+
- P0模块覆盖率: 90%+
- 测试通过率: 95%+
- 变异测试分数: 80%+
