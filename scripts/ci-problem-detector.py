#!/usr/bin/env python3
"""
CI问题检测和预防工具

全面检测可能导致CI失败的各种问题,并提供自动修复建议
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


class CIProblemDetector:
    """CI问题检测器"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.problems = []
        self.critical_problems = []

    def run_comprehensive_check(self) -> Dict[str, Any]:
        """运行全面的CI问题检测"""
        print("🔍 开始全面CI问题检测...")

        results = {
            "file_problems": self.detect_problematic_files(),
            "dependency_problems": self.detect_dependency_issues(),
            "security_problems": self.detect_security_issues(),
            "config_problems": self.detect_config_issues(),
            "git_problems": self.detect_git_issues(),
            "template_problems": self.detect_template_pollution(),
        }

        self.generate_prevention_rules(results)
        return results

    def detect_problematic_files(self) -> List[Dict[str, Any]]:
        """检测有问题的文件"""
        print("📁 检测问题文件...")
        problems = []

        # 检测不应该存在的文件
        problematic_patterns = [
            ("*_report.json", "敏感报告文件"),
            ("bandit_report.json", "Bandit安全报告"),
            ("security_report.json", "安全扫描报告"),
            ("src/aiculture-kit/", "模板文件目录"),
            ("templates/", "模板目录"),
            ("temp/", "临时目录"),
            ("tmp/", "临时目录"),
            ("*.pyc", "编译后的Python文件"),
            ("__pycache__/", "Python缓存目录"),
            (".mypy_cache/", "MyPy缓存"),
            (".ruff_cache/", "Ruff缓存"),
        ]

        for pattern, description in problematic_patterns:
            matches = list(self.project_root.glob(f"**/{pattern}"))
            for match in matches:
                if self.should_ignore_path(match):
                    continue

                problems.append(
                    {
                        "type": "problematic_file",
                        "path": str(match),
                        "description": description,
                        "severity": (
                            "high"
                            if any(
                                x in pattern
                                for x in ["report", "security", "templates"]
                            )
                            else "medium"
                        ),
                        "solution": f"删除文件: rm -rf {match}",
                    }
                )

        return problems

    def detect_template_pollution(self) -> List[Dict[str, Any]]:
        """检测模板文件污染"""
        print("🧹 检测模板文件污染...")
        problems = []

        # 检测模板语法
        template_patterns = [
            (r"\{\{.*\}\}", "Jinja2模板语法"),
            (r"<%.*%>", "ERB模板语法"),
            (r"@\{.*\}", "其他模板语法"),
        ]

        for file_path in self.project_root.rglob("*.py"):
            if self.should_ignore_path(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                for pattern, desc in template_patterns:
                    if re.search(pattern, content):
                        problems.append(
                            {
                                "type": "template_pollution",
                                "path": str(file_path),
                                "description": f"包含{desc}",
                                "severity": "high",
                                "solution": f"检查并清理文件: {file_path}",
                            }
                        )
                        break
            except (UnicodeDecodeError, PermissionError):
                continue

        return problems

    def detect_security_issues(self) -> List[Dict[str, Any]]:
        """检测安全问题"""
        print("🔒 检测安全问题...")
        problems = []

        # 检测硬编码的敏感信息
        sensitive_patterns = [
            (r"password\s*=\s*['\"][^'\"]+['\"]", "硬编码密码"),
            (r"secret\s*=\s*['\"][^'\"]+['\"]", "硬编码密钥"),
            (r"api_key\s*=\s*['\"][^'\"]+['\"]", "硬编码API密钥"),
            (r"token\s*=\s*['\"][^'\"]+['\"]", "硬编码令牌"),
        ]

        for file_path in self.project_root.rglob("*.py"):
            if self.should_ignore_path(file_path):
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
                for pattern, desc in sensitive_patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        problems.append(
                            {
                                "type": "security_issue",
                                "path": str(file_path),
                                "line": content[: match.start()].count("\n") + 1,
                                "description": desc,
                                "severity": "critical",
                                "solution": "使用环境变量或配置文件",
                            }
                        )
            except (UnicodeDecodeError, PermissionError):
                continue

        return problems

    def detect_dependency_issues(self) -> List[Dict[str, Any]]:
        """检测依赖问题"""
        print("📦 检测依赖问题...")
        problems = []

        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            try:
                # 快速检测已知问题模式
                result = subprocess.run(  # nosec B603,B607
                    ["pip", "install", "--dry-run", "-r", str(requirements_file)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode != 0:
                    problems.append(
                        {
                            "type": "dependency_conflict",
                            "description": "依赖冲突检测到问题",
                            "severity": "high",
                            "details": result.stderr[:500],
                            "solution": "运行 python scripts/dependency-conflict-detector.py",
                        }
                    )
            except subprocess.TimeoutExpired:
                problems.append(
                    {
                        "type": "dependency_timeout",
                        "description": "依赖解析超时",
                        "severity": "medium",
                        "solution": "检查网络连接和依赖文件",
                    }
                )
            except Exception as e:
                problems.append(
                    {
                        "type": "dependency_error",
                        "description": f"依赖检测错误: {e}",
                        "severity": "medium",
                        "solution": "手动检查requirements.txt",
                    }
                )

        return problems

    def detect_config_issues(self) -> List[Dict[str, Any]]:
        """检测配置问题"""
        print("⚙️ 检测配置问题...")
        problems = []

        # 检测CI配置文件
        ci_files = [
            ".github/workflows/ci.yml",
            ".pre-commit-config.yaml",
            "pyproject.toml",
            ".gitleaks.toml",
        ]

        for ci_file in ci_files:
            file_path = self.project_root / ci_file
            if file_path.exists():
                problems.extend(self.validate_config_file(file_path))

        return problems

    def validate_config_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """验证配置文件"""
        problems = []

        try:
            content = file_path.read_text(encoding="utf-8")

            # 检测YAML语法问题
            if file_path.suffix in [".yml", ".yaml"]:
                import yaml

                try:
                    yaml.safe_load(content)
                except yaml.YAMLError as e:
                    problems.append(
                        {
                            "type": "config_syntax_error",
                            "path": str(file_path),
                            "description": f"YAML语法错误: {e}",
                            "severity": "critical",
                            "solution": "修复YAML语法",
                        }
                    )

            # 检测TOML语法问题
            elif file_path.suffix == ".toml":
                import tomllib

                try:
                    tomllib.loads(content)
                except tomllib.TOMLDecodeError as e:
                    problems.append(
                        {
                            "type": "config_syntax_error",
                            "path": str(file_path),
                            "description": f"TOML语法错误: {e}",
                            "severity": "critical",
                            "solution": "修复TOML语法",
                        }
                    )

        except Exception as e:
            problems.append(
                {
                    "type": "config_read_error",
                    "path": str(file_path),
                    "description": f"配置文件读取错误: {e}",
                    "severity": "medium",
                    "solution": "检查文件权限和编码",
                }
            )

        return problems

    def detect_git_issues(self) -> List[Dict[str, Any]]:
        """检测Git问题"""
        print("🔄 检测Git问题...")
        problems = []

        try:
            # 检测未跟踪的大文件
            result = subprocess.run(  # nosec B603,B607
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            for line in result.stdout.split("\n"):
                if line.startswith("??"):  # 未跟踪文件
                    file_path = Path(line[3:])
                    if (
                        file_path.exists()
                        and file_path.stat().st_size > 10 * 1024 * 1024
                    ):  # 10MB
                        problems.append(
                            {
                                "type": "large_untracked_file",
                                "path": str(file_path),
                                "description": f"大型未跟踪文件 ({file_path.stat().st_size / 1024 / 1024:.1f}MB)",
                                "severity": "medium",
                                "solution": "添加到.gitignore或删除",
                            }
                        )

        except subprocess.CalledProcessError:
            pass

        return problems

    def should_ignore_path(self, path: Path) -> bool:
        """检查路径是否应该被忽略"""
        ignore_patterns = [
            ".git/",
            ".venv/",
            "venv/",
            "__pycache__/",
            ".mypy_cache/",
            ".pytest_cache/",
            ".ruff_cache/",
            "node_modules/",
            ".idea/",
            ".vscode/",
        ]

        path_str = str(path)
        return any(pattern in path_str for pattern in ignore_patterns)

    def generate_prevention_rules(self, results: Dict[str, Any]) -> None:
        """生成预防规则"""
        print("🛡️ 生成预防规则...")

        prevention_rules = {
            "pre_commit_hooks": [
                "check-added-large-files",
                "check-case-conflict",
                "check-merge-conflict",
                "trailing-whitespace",
                "end-of-file-fixer",
            ],
            "gitignore_additions": [
                "*_report.json",
                "bandit_report.json",
                "security_report.json",
                "src/aiculture-kit/",
                "templates/",
                "temp/",
                "tmp/",
            ],
            "ci_checks": [
                "dependency-conflict-check",
                "security-scan",
                "template-pollution-check",
                "large-file-check",
            ],
        }

        with open("CI_PREVENTION_RULES.json", "w") as f:
            json.dump(prevention_rules, f, indent=2, ensure_ascii=False)

    def apply_fixes(self, problems: List[Dict[str, Any]]) -> bool:
        """应用自动修复"""
        print("🔧 应用自动修复...")

        success_count = 0
        for problem in problems:
            if problem["severity"] == "critical":
                continue  # 关键问题需要手动处理

            if problem["type"] == "problematic_file":
                try:
                    file_path = Path(problem["path"])
                    if file_path.exists():
                        if file_path.is_dir():
                            import shutil

                            shutil.rmtree(file_path)
                        else:
                            file_path.unlink()
                        success_count += 1
                        print(f"  ✅ 删除: {file_path}")
                except Exception as e:
                    print(f"  ❌ 删除失败 {problem['path']}: {e}")

        return success_count > 0

    def generate_report(self, results: Dict[str, Any]) -> str:
        """生成检测报告"""
        all_problems = []
        for _category, problems in results.items():
            all_problems.extend(problems)

        critical_count = sum(1 for p in all_problems if p.get("severity") == "critical")
        high_count = sum(1 for p in all_problems if p.get("severity") == "high")
        medium_count = sum(1 for p in all_problems if p.get("severity") == "medium")

        report = f"""
# 🔍 CI问题检测报告

## 📊 问题统计
- 🚨 关键问题: {critical_count}
- ⚠️ 高级问题: {high_count}
- 📝 中级问题: {medium_count}
- 📋 总计: {len(all_problems)}

## 📋 详细问题列表
"""

        for category, problems in results.items():
            if problems:
                report += f"\n### {category.replace('_', ' ').title()}\n"
                for _, problem in enumerate(problems, 1):
                    severity_emoji = {
                        "critical": "🚨",
                        "high": "⚠️",
                        "medium": "📝",
                    }.get(problem.get("severity", ""), "i")
                    report += f"• {severity_emoji} **{problem['description']}**\n"
                    if "path" in problem:
                        report += f"   - 路径: `{problem['path']}`\n"
                    if "solution" in problem:
                        report += f"   - 解决方案: {problem['solution']}\n"
                    report += "\n"

        return report


def main():
    """主函数"""
    print("🔍 CI问题检测和预防工具启动")
    print("=" * 60)

    detector = CIProblemDetector()

    # 运行全面检测
    results = detector.run_comprehensive_check()

    # 统计问题
    all_problems = []
    for problems in results.values():
        all_problems.extend(problems)

    if not all_problems:
        print("✅ 未发现CI问题!")
        return 0

    # 生成报告
    report = detector.generate_report(results)
    print(report)

    # 保存报告
    with open("CI_PROBLEMS_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)

    # 询问是否自动修复
    critical_problems = [p for p in all_problems if p.get("severity") == "critical"]
    if critical_problems:
        print(f"🚨 发现 {len(critical_problems)} 个关键问题,需要手动处理!")
        return 1

    auto_fixable = [p for p in all_problems if p["type"] == "problematic_file"]
    if auto_fixable:
        response = input(
            f"\n🔧 发现 {len(auto_fixable)} 个可自动修复的问题,是否修复?(y/N): "
        )
        if response.lower() == "y":
            if detector.apply_fixes(auto_fixable):
                print("✅ 自动修复完成!")
            else:
                print("❌ 自动修复失败!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
