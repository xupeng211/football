# Zero-Redlights CI Guide (Delta)

## 常用命令

make install     # 本地依赖（uv 优先，与 CI 一致）
make format && make lint
make type        # 若有分阶段策略，核心阻塞，其它非阻塞
make cov         # 覆盖率门槛由 COV_MIN 控制（默认 15）
make diffcov     # 改动行覆盖率检查（仅对 PR 改动行要求 ≥ 75%）
make local-ci    # 本地一次性跑完整 CI

## 原则

- 依赖以 uv.lock 为准；不要手改锁文件
- 配置集中在 pyproject.toml；避免重复风格文件
- 测试默认禁网；确需联网请用 @pytest.mark.allow_network

## 渐进收紧

Week1: COV_MIN=15；gitleaks/mypy 非阻塞
Week2: COV_MIN=20；gitleaks 阻塞（已启用），mypy 对核心目录阻塞，DIFF_COV_MIN 提至 80
Week3+: 逐步提升 COV_MIN 并扩大 mypy 阻塞范围

## 改动行覆盖率门禁

CI 在 PR 上执行 diff-cover，默认阈值 75（变量 DIFF_COV_MIN 可调）。

**本地预检**：`make diffcov BASE=main`

**配置说明**：

- 仅对 PR 改动的代码行要求覆盖率 ≥ DIFF_COV_MIN%
- 阈值可通过仓库变量 `DIFF_COV_MIN` 配置（默认 75）
- 避免对历史代码的大规模返工，渐进式提升代码质量

## 产物与版本控制策略
- **版本库中仅保留**：`reports/CI_GATES_REPORT.md`（人读摘要）。
- **不纳入版本控制**：覆盖率与改动行可视化产物（`htmlcov/**`, `coverage.xml/json`, `diff-coverage.html/md`）。
  - 本地查看：`make diffcov BASE=main`
  - 远端查看：在 PR 的 Actions **Artifacts** 中下载 `diff-coverage.html/md`。
