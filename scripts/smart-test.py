#!/usr/bin/env python3
"""智能测试选择器 - 根据Git变更文件选择相关测试"""

import subprocess
import sys

# 颜色定义
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def get_changed_files(compare_branch: str = "main") -> list[str]:
    """获取与目标分支相比发生变更的文件列表"""
    try:
        # 确保我们有最新的目标分支信息
        subprocess.run(
            ["git", "fetch", "origin", compare_branch],
            capture_output=True,
            check=True,
        )

        # 获取变更文件
        result = subprocess.run(
            ["git", "diff", f"origin/{compare_branch}...HEAD", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        changed = result.stdout.strip().split("\n")
        return [f for f in changed if f]  # 过滤空行
    except subprocess.CalledProcessError as e:
        print(f"{RED}❌ Git diff 命令失败: {e.stderr}{NC}")
        print(f"{YELLOW}💡 将运行所有快速测试作为备用方案。{NC}")
        return []  # 返回空列表, 触发默认测试


def select_tests(changed_files: list[str]) -> list[str]:
    """根据变更的文件路径智能选择测试范围"""
    if not changed_files:
        # 如果没有检测到变更或Git命令失败, 运行默认的快速测试
        return ["-m", "not slow", "tests/"]

    test_patterns = set()

    # 定义文件路径到测试标记或路径的映射规则
    mapping = {
        "apps/api/": "api",
        "data_pipeline/": "integration",
        "models/": "model",
        "trainer/": "model",
        "tests/": None,  # 测试文件自身的变更
        "pyproject.toml": "tests/",  # 依赖变更, 最好全跑
        "poetry.lock": "tests/",
        ".github/workflows/": "tests/",  # CI变更, 最好全跑
    }

    for file_path in changed_files:
        found_match = False
        for path_prefix, marker_or_path in mapping.items():
            if file_path.startswith(path_prefix):
                if marker_or_path and marker_or_path.startswith("tests/"):
                    test_patterns.add(marker_or_path)
                elif marker_or_path:
                    test_patterns.add(f"-m {marker_or_path}")
                else:  # 如果是测试文件变更, 直接添加文件路径
                    test_patterns.add(file_path)
                found_match = True
                break

        if not found_match and file_path.endswith(".py"):
            # 对于其他Python文件变更, 运行所有单元测试
            test_patterns.add("-m unit")

    # 如果没有匹配到任何特定测试, 则运行所有快速测试作为保障
    return list(test_patterns) or ["-m", "not slow", "tests/"]


if __name__ == "__main__":
    compare_branch = sys.argv[1] if len(sys.argv) > 1 else "main"

    changed = get_changed_files(compare_branch)
    patterns = select_tests(changed)

    print(
        f"{BLUE}🔍 检测到与 '{compare_branch}' 分支相比有 {len(changed)} 个文件变更。{NC}"
    )
    print(f"{BLUE}📝 将运行以下测试: pytest {' '.join(patterns)}{NC}")

    # 执行选定的测试
    cmd = ["pytest", *patterns, "--tb=short", "-v", "--disable-warnings"]
    try:
        result = subprocess.run(cmd, check=True)
        print(f"{GREEN}✅ 智能测试执行成功!{NC}")
        sys.exit(0)
    except subprocess.CalledProcessError:
        print(f"{RED}❌ 智能测试执行失败。{NC}")
        sys.exit(1)
