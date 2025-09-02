# 🚀 本地CI系统快速设置指南

## ⚡ 5分钟快速部署

### 1️⃣ 环境检查 (30秒)

```bash
# 检查所需工具
make ci.doctor
```

**必需工具**：

- ✅ Docker (用于CI容器)
- ✅ Python 3.11+ (项目环境)
- ✅ uv (依赖管理)
- ✅ make (任务执行)

### 2️⃣ 构建CI镜像 (2-3分钟)

```bash
# 构建本地CI Docker镜像
make ci.docker.build
```

### 3️⃣ 测试系统 (1分钟)

```bash
# 测试Docker CI
make ci.docker.new

# 测试本地CI (备用)
make ci.enhanced
```

### 4️⃣ 验证Hook (30秒)

```bash
# 确认pre-push hook已更新
ls -la .git/hooks/pre-push

# 测试推送触发
echo "test" >> README.md
git add README.md
git commit -m "test: CI hook测试"
git push  # 应该触发CI检查
```

## 📋 验证清单

- [ ] `make ci.doctor` 显示所有工具正常
- [ ] `make ci.docker.build` 成功构建镜像
- [ ] `make ci.docker.new` 运行完整CI通过
- [ ] `git push` 自动触发pre-push hook
- [ ] CI失败时正确阻止推送
- [ ] CI成功时允许推送

## 🔧 常用命令速查

```bash
# === 日常使用 ===
git push                    # 自动触发CI
make docker-ci             # 手动运行Docker CI
make ci.fix                 # 自动修复问题

# === 维护管理 ===
make ci.doctor             # 健康检查
make ci.docker.rebuild     # 重建镜像
make ci.docker.clean       # 清理资源

# === 应急方案 ===
SKIP_CI=true git push      # 跳过CI
git push --no-verify       # 跳过所有hook
make ci.enhanced           # 本地轻量CI
```

## ❌ 常见错误及解决

### Docker相关

```bash
# Docker daemon未运行
sudo systemctl start docker

# 权限问题
sudo usermod -aG docker $USER
# 然后重新登录

# 镜像构建失败
make ci.docker.clean
make ci.docker.build
```

### Hook相关

```bash
# Hook没有执行权限
chmod +x .git/hooks/pre-push

# Hook脚本不存在
# 重新运行项目的hook设置
```

### CI检查失败

```bash
# 查看详细错误
cat /tmp/ci-output.log

# 自动修复
make ci.fix

# 手动修复后重试
make ci.docker.new
```

## 🎯 成功标志

当看到以下输出时，表示系统工作正常：

```
🚦 Pre-Push Hook - 本地CI演练启动
=======================================
📍 项目路径: /path/to/project
📅 时间: 2024-XX-XX XX:XX:XX

🐳 使用Docker化CI演练 (与远程环境100%一致)
🔄 启动Docker化本地CI演练
✅ CI检查完成 (耗时: XX秒)

🎉 所有CI检查通过！
🚀 继续推送到远程仓库...
```

## 📞 获取帮助

如果设置过程中遇到问题：

1. **诊断工具**：`make ci.doctor`
2. **详细文档**：查看 `docs/LOCAL_CI_SYSTEM.md`
3. **日志分析**：`cat /tmp/ci-output.log`
4. **社区支持**：提交Issue或联系团队

---

**🎉 完成设置后，您的每次推送都将自动经过严格的CI检查，确保远程CI必定成功！**
