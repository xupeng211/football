## 📝 PR 标题
[CI 修复] + 工程优化（依赖锁定、日志增强）

## 📌 变更内容
- 修复 CI 红灯问题，确保 pipeline 全绿
- 依赖版本锁定（新增 requirements-lock.txt）
- 优化 FastAPI 日志 & 请求追踪
- 新增 Makefile 任务：ci.test / ci.lint / ci.full
- 更新 .gitleaks.toml，减少误报

## ✅ 验收标准
- [ ] CI 全绿 ✅
- [ ] pytest 全部通过
- [ ] lint 无报错
- [ ] 日志追踪功能可用
- [ ] requirements-lock.txt 可复现安装

## 📊 测试覆盖率
- 修复前覆盖率: xx%
- 修复后覆盖率: xx%
- 增加/修改测试文件: xxx

## 🔒 安全性
- 确保敏感信息未被提交（已更新 gitleaks 配置）

## 🚀 下一步计划
- 引入更严格的门禁规则
- 增加 CI 缓存加速
- 持续优化测试覆盖率
