# 🚀 Developer's Guide to Quality & CI

Welcome to the streamlined development workflow! This guide explains how to use our new automated tools to maintain high code quality, prevent CI failures, and speed up your development process.

## 🎯 Our Goal: Keep CI Green!

The primary goal of this system is to catch errors *before* they are pushed, ensuring that the CI pipeline remains green. This saves time and reduces frustration for everyone.

## 셋팅 1: Initial Environment Setup

If you are new to the project or setting up a new machine, follow these steps:

1.  **Clone the repository.**
2.  **Install project dependencies and tools:**

    ```bash
    make install
    ```

    This single command will:
    *   Create a virtual environment (`.venv`).
    *   Install all necessary Python packages.
    *   **Crucially, it will install the `pre-commit` and `pre-push` git hooks.**

3.  **Activate the virtual environment:**

    ```bash
    source .venv/bin/activate
    ```

4.  **Run an environment health check:**

    ```bash
    make check-env
    ```

    This script verifies that all your tools and dependencies are correctly configured.

## 🔁 2: Day-to-Day Development Workflow

Your daily workflow is now enhanced with automated checks.

### Step 1: Write Your Code

As you write code, your IDE (if configured with the provided `.vscode/settings.json`) will automatically format and lint your code on save.

### Step 2: Commit Your Changes

When you run `git commit`, our **pre-commit hooks** will automatically run. These hooks perform fast checks:

*   **Formatting (`ruff format`)**: Ensures consistent code style.
*   **Linting (`ruff`)**: Catches common errors and style issues.
*   **File checks**: Prevents committing large files, merge conflicts, etc.

If any of these checks fail, the commit will be aborted. Many issues (like formatting) will be fixed automatically. You just need to `git add` the changes and commit again.

### Step 3: Push Your Changes

Before your code is pushed to the remote repository, a **pre-push hook** will trigger a more comprehensive set of checks using our `quality-gate`.

Run this manually at any time with:

```bash
make quality-gate
```

This command runs:
1.  Formatting & Linting
2.  **Type Checking (`mypy`)**: Ensures type safety.
3.  **Security Scans (`bandit`)**: Finds common security vulnerabilities.
4.  **Quick Tests (`pytest`)**: Runs all tests not marked as `slow`.
5.  **Coverage Check**: Ensures test coverage doesn't drop below the threshold.

If this gate fails, your push will be blocked. This is the most important step to prevent CI failures.

## ⚡️ 3: Working with Pull Requests & CI

Our CI pipeline is now faster and smarter.

*   **Static Checks First**: A `lint-and-validate` job runs first, giving you quick feedback on static analysis issues.
*   **Smart Testing**: For Pull Requests, the CI will automatically run `make smart-test`. This script intelligently selects and runs only the tests relevant to your changes, dramatically reducing wait times.
*   **Full Suite on Main/Dev**: When your code is merged into `main` or `dev`, the CI runs the *full* test suite to ensure everything is working together correctly.

## 🔧 Useful Makefile Commands

Here are the key commands you'll use:

*   `make install`: One-time setup for your environment.
*   `make check-env`: Verify your local environment is healthy.
*   `make quality-gate`: Run all pre-push checks. Your most used command before pushing.
*   `make smart-test`: Simulate the PR testing process locally.
*   `make test`: Run the full test suite (useful before merging).
*   `make format`: Manually format the codebase.
*   `make lint`: Manually run the linter.

Use `make help` to see all available commands.

## 🚨 Troubleshooting Common Issues

*   **`pre-commit` fails on formatting**: The hook has likely already fixed the files. Just `git add .` and commit again.
*   **`make quality-gate` fails on tests**: A test is broken. Run `pytest -v` to see the detailed error and debug the failing test.
*   **`make quality-gate` fails on `mypy`**: There's a type error. Run `mypy apps/ data_pipeline/` to see detailed error messages.
*   **Push is rejected**: This means the pre-push `quality-gate` failed. Read the output to see which step failed and fix the issue.

By following this workflow, we can collectively ensure our codebase remains clean, stable, and easy to work with.
