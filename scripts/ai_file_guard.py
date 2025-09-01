#!/usr/bin/env python3
"""🤖 AI文件操作守护程序 - 防止AI工具创建重复文件"""

import difflib
import os
import sys
from pathlib import Path


class AIFileGuard:
    """AI文件操作守护和引导系统"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.load_config()

    def load_config(self) -> None:
        """加载配置"""
        self.forbidden_suffixes = [
            "_copy",
            "_backup",
            "_new",
            "_old",
            "_temp",
            "_v1",
            "_v2",
        ]
        self.test_locations = ["tests/unit/", "tests/integration/", "tests/e2e/"]
        self.api_locations = ["src/", "api/"]

    def find_similar_files(self, target_path: str) -> list[tuple[str, float]]:
        """查找相似的现有文件"""
        target_name = Path(target_path).name
        similar_files = []

        for root, dirs, files in os.walk(self.project_root):
            # 跳过虚拟环境和缓存目录
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]

            for file in files:
                if file.endswith(".py") and file != target_name:
                    similarity = difflib.SequenceMatcher(
                        None, target_name, file
                    ).ratio()
                    if similarity >= 0.6:
                        file_path = os.path.join(root, file)
                        similar_files.append((file_path, similarity))

        return sorted(similar_files, key=lambda x: x[1], reverse=True)

    def check_file_operation(self, target_path: str) -> dict[str, any]:
        """检查文件操作是否合适"""
        target = Path(target_path)
        result = {
            "allowed": True,
            "warnings": [],
            "suggestions": [],
            "similar_files": [],
        }

        # 检查禁止的后缀
        for suffix in self.forbidden_suffixes:
            if suffix in target.stem:
                result["allowed"] = False
                result["warnings"].append(f"避免使用 '{suffix}' 后缀")
                result["suggestions"].append("使用更明确的文件名")

        # 查找相似文件
        similar_files = self.find_similar_files(target_path)
        result["similar_files"] = similar_files[:3]

        # 检查是否应该修改现有文件
        for file_path, similarity in similar_files[:2]:
            if similarity > 0.8:
                result["warnings"].append(
                    f"发现相似文件: {file_path} ({similarity:.2f})"
                )
                result["suggestions"].append(f"考虑修改 {file_path} 而不是创建新文件")

        return result

    def suggest_paths(self, filename: str) -> list[str]:
        """建议文件路径"""
        suggestions = []

        if filename.startswith("test_"):
            suggestions.extend(
                [f"tests/unit/{filename}", f"tests/integration/{filename}"]
            )
        elif "api" in filename.lower():
            suggestions.extend([f"src/{filename}", f"api/{filename}"])
        else:
            suggestions.append(f"src/{filename}")

        return suggestions


def main():
    """命令行工具"""
    if len(sys.argv) < 2:
        print("用法: python ai_file_guard.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    guard = AIFileGuard()
    result = guard.check_file_operation(file_path)

    print("🤖 AI文件操作检查")
    print("=" * 40)

    _print_warnings(result)
    _print_suggestions(result)
    _print_similar_files(result)
    _print_path_suggestions(guard, file_path)

    print("=" * 40)


def _print_warnings(result):
    """打印警告信息"""
    if not result["allowed"]:
        print("❌ 不建议创建此文件:")
        for warning in result["warnings"]:
            print(f"  • {warning}")

    if result["warnings"]:
        print("⚠️  注意:")
        for warning in result["warnings"]:
            print(f"  • {warning}")


def _print_suggestions(result):
    """打印建议信息"""
    if result["suggestions"]:
        print("💡 建议:")
        for suggestion in result["suggestions"]:
            print(f"  • {suggestion}")


def _print_similar_files(result):
    """打印相似文件"""
    if result["similar_files"]:
        print("📁 相似文件:")
        for file_path, similarity in result["similar_files"]:
            print(f"  • {file_path} ({similarity:.2f})")


def _print_path_suggestions(guard, file_path):
    """打印路径建议"""
    suggestions = guard.suggest_paths(Path(file_path).name)
    if suggestions:
        print("📍 推荐路径:")
        for i, path in enumerate(suggestions[:3], 1):
            print(f"  {i}. {path}")


if __name__ == "__main__":
    main()
