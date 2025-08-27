# CI Gates Report

- 生成时间：2025-08-27 14:18:53
- 基线分支：origin/main

## 总览
| Gate | Result | Details |
|---|:--:|---|
| Ruff Lint | ✅ PASS | exit=0 |
| mypy (advisory) | ✅ PASS | exit=0 |
| Gitleaks | ✅ PASS | exit=0（命中不一定是生产风险，详见 `.gitleaks.toml` allowlist） |
| Pytest + Coverage | ✅ PASS | exit=0；覆盖率文件：coverage.xml/html/json |
| 总覆盖率门禁（COV_MIN=15%） | ✅ PASS | 实测≈40.97% |
| 改动行覆盖率（DIFF_COV_MIN=75%） | ✅ PASS | 实测≈N/A% |

## 产物（本地生成）
- `coverage.xml` / `coverage.json` / `htmlcov/`
- `diff-coverage.html` / `diff-coverage.md`
- 本报告：`reports/CI_GATES_REPORT.md`

## 建议与下一步
- 如 **改动行覆盖率** 未达标：为本次 PR 改动补 1–2 个小用例（冒烟+失败路径），再运行 `make diffcov BASE=<基线>`。
- 如 **总覆盖率** 接近阈值：先补测试再提交；主干稳定一周后将 `COV_MIN` 从 15% 提到 20%。
- 若为纯文档/清单 PR：CI 中已配置**智能豁免**（diff-cover 步骤会跳过）。
