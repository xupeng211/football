# Zero-Redlights CI Guide (Delta)

## 常用命令

make install     # 本地依赖（uv 优先，与 CI 一致）
make format && make lint
make type        # 若有分阶段策略，核心阻塞，其它非阻塞
make cov         # 覆盖率门槛由 COV_MIN 控制（默认 15）
make local-ci    # 本地一次性跑完整 CI

## 原则

- 依赖以 uv.lock 为准；不要手改锁文件
- 配置集中在 pyproject.toml；避免重复风格文件
- 测试默认禁网；确需联网请用 @pytest.mark.allow_network

## 渐进收紧

Week1: COV_MIN=15；gitleaks/mypy 非阻塞
Week2: COV_MIN=20；gitleaks 阻塞（已启用），mypy 对核心目录阻塞
Week3+: 逐步提升 COV_MIN 并扩大 mypy 阻塞范围
