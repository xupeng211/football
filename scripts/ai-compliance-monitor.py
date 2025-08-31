#!/usr/bin/env python3
"""
🔍 AI编程工具合规性监控器
监控并阻止AI工具违规行为(如跳过质检)
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class AIComplianceMonitor:
    """AI工具合规性监控器"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.log_file = self.project_root / ".ai-compliance.log"
        self.violations_file = self.project_root / ".ai-violations.json"

    def log_violation(
        self, violation_type: str, command: str, ai_tool: str = "unknown"
    ):
        """记录违规行为"""
        timestamp = datetime.now().isoformat()
        violation = {
            "timestamp": timestamp,
            "type": violation_type,
            "command": command,
            "ai_tool": ai_tool,
            "project": str(self.project_root.name),
        }

        # 记录到日志
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] VIOLATION: {violation_type} - {command}\n")

        # 记录到JSON文件
        violations = []
        if self.violations_file.exists():
            with open(self.violations_file, encoding="utf-8") as f:
                violations = json.load(f)

        violations.append(violation)

        with open(self.violations_file, "w", encoding="utf-8") as f:
            json.dump(violations, f, indent=2, ensure_ascii=False)

        print(f"🚨 违规行为已记录: {violation_type}")

    def check_git_history(self) -> bool:
        """检查Git历史中的违规提交"""
        try:
            # 检查最近的提交是否跳过了hooks
            result = subprocess.run(
                ["git", "log", "--oneline", "-10", "--grep=--no-verify"],
                capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                self.log_violation("GIT_NO_VERIFY", "Found commits with --no-verify")
                return False

            return True
        except Exception as e:
            print(f"检查Git历史时出错: {e}")
            return True

    def check_shell_history(self) -> bool:
        """检查Shell历史中的违规命令"""
        violations_found = False

        # 违规命令模式
        forbidden_patterns = [
            r"git\s+commit\s+.*--no-verify",
            r"git\s+push\s+.*--no-verify",
            r"git\s+commit\s+.*-n\s",
            r"git\s+push\s+.*-n\s",
            r"make\s+quality-gate\s*\|\|\s*true",
            r"pytest\s*\|\|\s*echo.*failed",
            r"ruff\s+check.*\|\|\s*echo.*failed",
        ]

        # 检查bash历史
        history_files = [
            Path.home() / ".bash_history",
            Path.home() / ".zsh_history",
            Path.home() / ".history",
        ]

        for history_file in history_files:
            if not history_file.exists():
                continue

            try:
                with open(history_file, encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()[-100:]  # 只检查最近100条

                for line in lines:
                    for pattern in forbidden_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.log_violation("SHELL_COMMAND", line.strip())
                            violations_found = True

            except Exception as e:
                print(f"检查历史文件 {history_file} 时出错: {e}")

        return not violations_found

    def validate_current_environment(self) -> bool:
        """验证当前环境配置"""
        issues = []

        # 检查pre-commit hooks是否安装
        pre_commit_hook = Path(".git/hooks/pre-commit")
        if not pre_commit_hook.exists():
            issues.append("Pre-commit hook未安装")

        # 检查pre-push hooks是否安装
        pre_push_hook = Path(".git/hooks/pre-push")
        if not pre_push_hook.exists():
            issues.append("Pre-push hook未安装")

        # 检查质检命令是否可用
        try:
            result = subprocess.run(
                ["make", "quality-gate", "--dry-run"], capture_output=True
            )
            if result.returncode != 0:
                issues.append("quality-gate命令不可用")
        except Exception:
            issues.append("Makefile或make命令不可用")

        if issues:
            for issue in issues:
                self.log_violation("ENVIRONMENT_ISSUE", issue)
            return False

        return True

    def generate_compliance_report(self) -> dict:
        """生成合规性报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "project": str(self.project_root.name),
            "checks": {
                "git_history": self.check_git_history(),
                "shell_history": self.check_shell_history(),
                "environment": self.validate_current_environment(),
            },
            "overall_compliance": True,
        }

        # 如果任何检查失败, 整体合规性为False
        if not all(report["checks"].values()):
            report["overall_compliance"] = False

        return report

    def run_monitoring(self) -> bool:
        """运行完整的合规性监控"""
        print("🔍 运行AI编程工具合规性检查...")

        report = self.generate_compliance_report()

        if report["overall_compliance"]:
            print("✅ AI工具合规性检查通过")
            return True
        else:
            print("❌ 发现AI工具违规行为!")
            print("📋 违规详情:")
            for check_name, passed in report["checks"].items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check_name}")

            print(f"\n📄 详细日志: {self.log_file}")
            print(f"📊 违规记录: {self.violations_file}")
            return False


def main():
    """主函数"""
    monitor = AIComplianceMonitor()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "check":
            success = monitor.run_monitoring()
            sys.exit(0 if success else 1)
        elif command == "report":
            report = monitor.generate_compliance_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print("用法: python ai-compliance-monitor.py [check|report]")
            sys.exit(1)
    else:
        # 默认运行检查
        success = monitor.run_monitoring()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
