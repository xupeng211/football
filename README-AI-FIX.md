# 📘 AI 自动修复增强系统 - 使用说明书

本文档旨在帮助开发者理解和使用本项目集成的AI自动修复增强系统。该系统旨在通过自动化测试、智能追踪和AI驱动的修复流程，提升Bug修复的效率和准确性。

---

## 1. 系统架构图 (文字版)

系统的核心理念是将AI能力深度集成到DevOps生命周期中，形成一个从问题发现到自动修复、再到人工审核和持续优化的闭环。

```
[开发者] <--> [GitHub: PR/Commit] <--> [GitHub Actions: CI/CD]
    ^
    | (5. 反馈)
    v
[Slack/企业微信] (通知)

CI/CD 流程:
1.  代码提交 -> pre-commit hooks (Ruff, Mypy)
2.  创建PR -> 自动化测试 (Unit, Integration, Regression, E2E)
3.  测试失败 -> (未来) 触发AI修复流程

AI 修复与可观测性:
+-------------------------+      +-------------------------+
|      Prefect            |      |      Jaeger             |
| (AI修复验证流程)        | <--> | (分布式追踪)            |
+-------------------------+      +-------------------------+
    |                                  ^
    | (4. 自动创建PR)                  | (API请求/错误)
    v                                  |
[GitHub Actions: AI-Fix PR]        [FastAPI App]

模型持续优化:
+-------------------------+      +-------------------------+
|      MLflow             |      |      Bug Fix Data       |
| (模型训练与评估)        | <--> | (data/bug_fixes/)       |
+-------------------------+      +-------------------------+
```

## 2. 如何运行测试

我们使用 `pytest` 作为测试框架，并已定义了多种测试类型。所有测试都可以通过 `Makefile` 中的命令方便地运行。

- **运行所有测试** (推荐在提交代码前完整运行):
  ```bash
  make test-all
  ```

- **运行特定类型的测试**:
  ```bash
  # 运行单元测试 (快速，高频使用)
  make test-unit

  # 运行集成测试
  make test-integration

  # 运行回归测试 (确保旧Bug不复现)
  make test-regression

  # 运行端到端测试 (模拟用户真实操作)
  make test-e2e
  ```

- **查看测试覆盖率**:
  运行任何测试后，覆盖率报告会自动生成在 `htmlcov/` 目录下。
  ```bash
  open htmlcov/index.html
  ```

## 3. 如何触发 AI 修复流程

AI 修复流程由 Prefect 和 GitHub Actions 协同工作。

1.  **修复验证流程 (Prefect)**:
    我们已经创建了一个名为 `ai_fix_validation_flow` 的 Prefect 流程，用于模拟AI生成、验证和选择最佳修复方案。

    - **启动 Prefect 服务** (需要先启动 Docker 环境):
      ```bash
      docker-compose up prefect
      ```
    - **运行流程**:
      在本地环境中，你可以通过运行以下命令来触发一个演示流程：
      ```bash
      python flows/ai_fix_validation_flow.py
      ```
    - **查看流程**:
      在浏览器中打开 `http://localhost:4200` 查看 Prefect UI。

2.  **自动创建PR (GitHub Actions)**:
    当一个最佳修复方案被选定后（在真实场景中，Prefect 流程的最后一步），可以调用 `ai-fix-pr.yml` workflow 来自动创建 PR。

    - **触发方式**: 通过 GitHub API 或 UI 手动触发 `AI-Fix Create PR` workflow。
    - **需要参数**:
      - `bug_description`: Bug 的文字描述。
      - `fix_patch`: Base64 编码后的代码补丁 (`.patch` 文件内容)。

## 4. 如何查看 Jaeger 追踪与日志

我们集成了 OpenTelemetry 和 Jaeger 来实现分布式追踪，帮助你快速定位请求链路中的问题。

1.  **启动环境**:
    确保 Jaeger 和 API 服务正在运行。
    ```bash
    docker-compose up -d jaeger api
    ```

2.  **查看 Jaeger UI**:
    在浏览器中打开 `http://localhost:16686`。

3.  **生成追踪数据**:
    通过访问 API 的端点（例如，使用 `curl` 或浏览器访问 `http://localhost:8000/`）来产生一些请求流量。

4.  **分析追踪**:
    在 Jaeger UI 中，你应该能看到名为 `football-predict-api` 的服务。点击它可以查看请求的完整链路，包括数据库查询、Redis 缓存访问等操作的耗时和元数据。

5.  **查看日志**:
    所有服务的日志都将统一输出到 Docker Compose。你可以通过以下命令查看：
    ```bash
    docker-compose logs -f api
    ```
    同时，我们创建了 `logs/` 目录，未来可以将日志文件统一存储于此。

## 5. 如何查看静态分析报告

我们在 `pre-commit` hook 和 CI 流程中集成了 `Ruff`, `Mypy` 和 `Bandit` 来保证代码质量。

- **本地检查 (自动)**:
  当你 `git commit` 时，`.pre-commit-config.yaml` 中定义的钩子会自动运行。如果发现问题，提交将被中止，并提示你修复。

- **手动运行检查**:
  你可以使用 `Makefile` 中的命令随时手动运行所有检查：
  ```bash
  # 运行所有质量检查 (lint, type, security)
  make quality-gate
  ```

- **在 CI 中查看**:
  每次向 PR 推送代码时，`Lint & Validate` job 都会运行这些检查。你可以在 GitHub Actions 的日志中查看详细的输出报告。

## 6. 如何接收 AI 修复反馈

我们通过 Webhook 将 AI 相关的 PR 状态变更实时推送到协作工具中（如 Slack 或企业微信）。

1.  **配置 Webhook**:
    项目的管理员需要在 `Settings > Secrets and variables > Actions` 中创建一个名为 `WEBHOOK_URL` 的 secret，并填入你的机器人 Webhook 地址。

2.  **自动通知**:
    一旦配置完成，当一个带有 `ai-fix` 标签的 PR 被创建、合并或关闭时，`.github/workflows/notify-pr-status.yml` workflow 将会自动触发，并发送一条格式化的消息到指定的频道。

3.  **提供反馈**:
    开发者在审查 PR 后，可以将对 AI 修复质量的反馈（例如，修复是否有效、代码风格是否良好等）整理并存放到 `data/feedback/` 目录中。这些数据是未来优化模型的重要输入。

## 7. 如何扩展 AI 修复模型

我们已经为未来的模型训练和迭代奠定了基础。

1.  **数据收集**:
    - `data/bug_fixes/`: 存储与 Bug 相关的上下文数据（如代码片段、错误日志、测试用例）。
    - `data/feedback/`: 存储人工对 AI 修复方案的评估数据。

2.  **训练脚本**:
    `scripts/train_ai_fix_model.py` 是一个模型训练的入门脚本。你可以：
    - 修改 `load_data` 函数来解析真实的数据格式。
    - 在 `train_model` 中替换为你自己的模型和训练逻辑。

3.  **实验跟踪 (MLflow)**:
    我们预留了 `mlflow/` 目录。未来，你可以在训练脚本中集成 MLflow Tracking，以记录和比较不同实验的参数、指标和产出的模型，从而系统化地管理模型迭代过程。
