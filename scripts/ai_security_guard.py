#!/usr/bin/env python3
"""
AI安全编程守护程序

功能:
1. 检测安全反模式
2. 验证配置安全性
3. 扫描依赖漏洞
4. 生成安全建议
5. 自动修复建议
"""

import ast
import json
import re
import secrets
import sys
from pathlib import Path
from typing import Any


class SecurityIssue:
    """安全问题类"""

    def __init__(
        self,
        severity: str,
        category: str,
        description: str,
        file_path: str,
        line_number: int = 0,
        suggestion: str = "",
        auto_fix: str = "",
    ):
        self.severity = severity  # CRITICAL, HIGH, MEDIUM, LOW
        self.category = category  # INJECTION, CRYPTO, CONFIG, etc.
        self.description = description
        self.file_path = file_path
        self.line_number = line_number
        self.suggestion = suggestion
        self.auto_fix = auto_fix


class AISecurityGuard:
    """AI安全守护程序"""

    def __init__(self, rules_file: str = "ai_security_rules.json"):
        self.rules_file = Path(rules_file)
        self.rules = self._load_rules()
        self.issues: list[SecurityIssue] = []

    def _load_rules(self) -> dict[str, Any]:
        """加载安全规则"""
        if not self.rules_file.exists():
            print(f"❌ 规则文件不存在: {self.rules_file}")
            return {}

        with open(self.rules_file, encoding="utf-8") as f:
            return json.load(f)

    def scan_file(self, file_path: str) -> list[SecurityIssue]:
        """扫描单个文件"""
        issues = []
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            return issues

        # 读取文件内容
        try:
            with open(file_path_obj, encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()
        except Exception as e:
            print(f"⚠️ 无法读取文件 {file_path}: {e}")
            return issues

        # 检查禁止的导入
        issues.extend(self._check_forbidden_imports(content, file_path, lines))

        # 检查代码模式
        issues.extend(self._check_code_patterns(content, file_path, lines))

        # 检查文件内容
        issues.extend(self._check_file_contents(content, file_path, lines))

        # 检查Python AST (如果是Python文件)
        if file_path_obj.suffix == ".py":
            issues.extend(self._check_python_ast(content, file_path))

        return issues

    def _check_forbidden_imports(
        self, content: str, file_path: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """检查禁止的导入"""
        issues = []
        forbidden_imports = (
            self.rules.get("security_rules", {})
            .get("forbidden_patterns", {})
            .get("imports", [])
        )

        for line_num, line in enumerate(lines, 1):
            for pattern in forbidden_imports:
                if pattern in line:
                    # 获取安全替代方案
                    alternatives = self._get_alternatives(pattern)

                    severity = "HIGH" if "pickle" in pattern else "MEDIUM"
                    category = (
                        "INJECTION"
                        if any(x in pattern for x in ["exec", "eval"])
                        else "DESERIALIZATION"
                    )

                    issue = SecurityIssue(
                        severity=severity,
                        category=category,
                        description=f"检测到禁止的导入: {pattern}",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=f"建议使用: {alternatives}",
                        auto_fix=self._generate_auto_fix(pattern, line),
                    )
                    issues.append(issue)

        return issues

    def _check_code_patterns(
        self, content: str, file_path: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """检查代码模式"""
        issues = []
        code_patterns = (
            self.rules.get("security_rules", {})
            .get("forbidden_patterns", {})
            .get("code_patterns", [])
        )

        for line_num, line in enumerate(lines, 1):
            for pattern in code_patterns:
                if re.search(pattern, line):
                    severity = self._determine_severity(pattern)
                    category = self._determine_category(pattern)

                    issue = SecurityIssue(
                        severity=severity,
                        category=category,
                        description=f"检测到不安全的代码模式: {pattern}",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion=self._get_pattern_suggestion(pattern),
                        auto_fix=self._generate_pattern_fix(pattern, line),
                    )
                    issues.append(issue)

        return issues

    def _check_file_contents(
        self, content: str, file_path: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """检查文件内容"""
        issues = []
        forbidden_contents = (
            self.rules.get("security_rules", {})
            .get("forbidden_patterns", {})
            .get("file_contents", [])
        )

        for line_num, line in enumerate(lines, 1):
            for forbidden in forbidden_contents:
                if forbidden.lower() in line.lower():
                    issue = SecurityIssue(
                        severity="HIGH",
                        category="HARDCODED_SECRET",
                        description=f"检测到硬编码的敏感信息: {forbidden}",
                        file_path=file_path,
                        line_number=line_num,
                        suggestion="使用环境变量或密钥管理系统",
                        auto_fix=self._generate_secret_fix(forbidden, line),
                    )
                    issues.append(issue)

        return issues

    def _check_python_ast(self, content: str, file_path: str) -> list[SecurityIssue]:
        """检查Python AST"""
        issues = []

        try:
            tree = ast.parse(content)
            issues.extend(self._check_dangerous_calls(tree, file_path))
            issues.extend(self._check_hardcoded_secrets(tree, file_path))
        except SyntaxError:
            # 忽略语法错误文件
            pass

        return issues

    def _check_dangerous_calls(self, tree: ast.AST, file_path: str) -> list[SecurityIssue]:
        """检查危险函数调用"""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name in ["exec", "eval", "compile"]:
                    issue = SecurityIssue(
                        severity="CRITICAL",
                        category="CODE_INJECTION",
                        description=f"检测到危险函数调用: {func_name}",
                        file_path=file_path,
                        line_number=node.lineno,
                        suggestion="避免使用exec/eval,考虑使用ast.literal_eval",
                        auto_fix=f"# 替换 {func_name} 为安全的替代方案",
                    )
                    issues.append(issue)
        return issues

    def _check_hardcoded_secrets(self, tree: ast.AST, file_path: str) -> list[SecurityIssue]:
        """检查硬编码密钥"""
        issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if self._is_secret_assignment(target, node):
                        issue = self._create_weak_key_issue(target, node, file_path)
                        if issue:
                            issues.append(issue)
        return issues

    def _is_secret_assignment(self, target: ast.expr, node: ast.Assign) -> bool:
        """检查是否为密钥赋值"""
        return (isinstance(target, ast.Name)
                and "secret" in target.id.lower()
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
                and len(node.value.value) < 32)

    def _create_weak_key_issue(self, target: ast.Name, node: ast.Assign, file_path: str) -> SecurityIssue | None:
        """创建弱密钥问题"""
        if not isinstance(node.value, ast.Constant):
            return None

        auto_fix = f"{target.id} = os.environ.get('{target.id.upper()}')"
        return SecurityIssue(
            severity="HIGH",
            category="WEAK_CRYPTO",
            description="检测到弱密钥 (长度不足)",
            file_path=file_path,
            line_number=node.lineno,
            suggestion="使用至少32字符的强密钥",
            auto_fix=auto_fix,
        )

    def _get_alternatives(self, pattern: str) -> str:
        """获取安全替代方案"""
        secure_alts = self.rules.get("security_rules", {}).get(
            "secure_alternatives", {}
        )

        for key, alt_info in secure_alts.items():
            if key in pattern:
                return ", ".join(alt_info.get("alternatives", []))

        return "查看安全最佳实践文档"

    def _determine_severity(self, pattern: str) -> str:
        """确定严重性级别"""
        if any(x in pattern for x in ["password", "secret", "api_key"]):
            return "HIGH"
        elif "debug.*True" in pattern:
            return "MEDIUM"
        elif "0\\.0\\.0\\.0" in pattern:
            return "MEDIUM"
        else:
            return "LOW"

    def _determine_category(self, pattern: str) -> str:
        """确定问题类别"""
        if any(x in pattern for x in ["password", "secret", "api_key", "token"]):
            return "HARDCODED_SECRET"
        elif "debug" in pattern:
            return "INFO_DISCLOSURE"
        elif "host" in pattern:
            return "NETWORK_CONFIG"
        elif "cors" in pattern:
            return "ACCESS_CONTROL"
        else:
            return "MISC"

    def _get_pattern_suggestion(self, pattern: str) -> str:
        """获取模式建议"""
        templates = self.rules.get("ai_guidance_templates", {})

        if "password" in pattern or "secret" in pattern:
            return templates.get("hardcoded_secret", "使用环境变量")
        elif "debug" in pattern:
            return templates.get("debug_in_prod", "生产环境应关闭debug")
        elif "0\\.0\\.0\\.0" in pattern:
            return templates.get("insecure_binding", "使用具体IP地址")
        elif "cors" in pattern:
            return templates.get("cors_wildcard", "指定具体域名")
        else:
            return "查看安全最佳实践"

    def _generate_auto_fix(self, pattern: str, line: str) -> str:
        """生成自动修复建议"""
        if "pickle" in pattern:
            return "# 替换为: import json  # 或 import joblib (for ML models)"
        elif "exec" in pattern:
            return "# 替换为: ast.literal_eval() 或其他安全方法"
        else:
            return "# 查看安全最佳实践文档"

    def _generate_pattern_fix(self, pattern: str, line: str) -> str:
        """生成模式修复建议"""
        if "password.*=" in pattern:
            return "password = os.environ.get('DB_PASSWORD')"
        elif "secret.*=" in pattern:
            return "secret_key = os.environ.get('SECRET_KEY')"
        elif "debug.*=.*True" in pattern:
            return "debug = False  # 或使用环境变量控制"
        elif "0\\.0\\.0\\.0" in pattern:
            return "host = '127.0.0.1'  # 或具体的内网IP"
        else:
            return "# 参考安全配置最佳实践"

    def _generate_secret_fix(self, forbidden: str, line: str) -> str:
        """生成密钥修复建议"""
        # 生成新的安全密钥
        new_secret = secrets.token_urlsafe(32)
        return (
            f"# 使用环境变量: os.environ.get('SECRET_KEY')  # 生成的密钥: {new_secret}"
        )

    def scan_project(self, project_path: str = ".") -> list[SecurityIssue]:
        """扫描整个项目"""
        all_issues = []
        project_path_obj = Path(project_path)

        # 扫描Python文件
        for py_file in project_path_obj.rglob("*.py"):
            # 跳过虚拟环境和缓存目录
            if any(part in str(py_file) for part in [".venv", "__pycache__", ".git"]):
                continue

            issues = self.scan_file(str(py_file))
            all_issues.extend(issues)

        # 扫描配置文件
        config_files = ["*.env", "*.yaml", "*.yml", "*.toml", "*.ini"]
        for pattern in config_files:
            for config_file in project_path_obj.rglob(pattern):
                if ".git" not in str(config_file):
                    issues = self.scan_file(str(config_file))
                    all_issues.extend(issues)

        self.issues = all_issues
        return all_issues

    def generate_report(self, format: str = "text") -> str:
        """生成安全报告"""
        if format == "json":
            return self._generate_json_report()
        else:
            return self._generate_text_report()

    def _generate_text_report(self) -> str:
        """生成文本报告"""
        if not self.issues:
            return "✅ 未发现安全问题!"

        report = ["🔒 AI安全扫描报告", "=" * 50, ""]

        # 按严重性分组
        by_severity = {}
        for issue in self.issues:
            by_severity.setdefault(issue.severity, []).append(issue)

        severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        severity_icons = {"CRITICAL": "🚨", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🔵"}

        for severity in severity_order:
            if severity in by_severity:
                issues = by_severity[severity]
                report.append(
                    f"{severity_icons[severity]} {severity} 级别问题 ({len(issues)}个)"
                )
                report.append("-" * 30)

                for i, issue in enumerate(issues, 1):
                    report.append(f"{i}. {issue.description}")
                    report.append(f"   📁 文件: {issue.file_path}:{issue.line_number}")
                    report.append(f"   💡 建议: {issue.suggestion}")
                    if issue.auto_fix:
                        report.append(f"   🔧 修复: {issue.auto_fix}")
                    report.append("")

        # 总结
        total = len(self.issues)
        critical = len(by_severity.get("CRITICAL", []))
        high = len(by_severity.get("HIGH", []))

        report.extend(
            [
                "📊 总结",
                "=" * 20,
                f"总问题数: {total}",
                f"致命问题: {critical}",
                f"高危问题: {high}",
                "",
            ]
        )

        if critical > 0:
            report.append("⚠️  建议: 立即修复致命问题!")
        elif high > 0:
            report.append("⚠️  建议: 优先修复高危问题")
        else:
            report.append("✅ 当前风险可控")

        return "\n".join(report)

    def _generate_json_report(self) -> str:
        """生成JSON报告"""
        issues_data = []
        for issue in self.issues:
            issues_data.append(
                {
                    "severity": issue.severity,
                    "category": issue.category,
                    "description": issue.description,
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "suggestion": issue.suggestion,
                    "auto_fix": issue.auto_fix,
                }
            )

        report = {
            "scan_summary": {
                "total_issues": len(self.issues),
                "by_severity": self._count_by_severity(),
                "scan_time": str(__import__("datetime").datetime.now()),
            },
            "issues": issues_data,
        }

        return json.dumps(report, indent=2, ensure_ascii=False)

    def _count_by_severity(self) -> dict[str, int]:
        """按严重性统计"""
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for issue in self.issues:
            counts[issue.severity] += 1
        return counts

    def fix_issue(self, issue: SecurityIssue) -> bool:
        """自动修复问题"""
        try:
            # 这里可以实现自动修复逻辑
            # 目前只是打印修复建议
            print(f"🔧 修复建议: {issue.auto_fix}")
            return True
        except Exception as e:
            print(f"❌ 自动修复失败: {e}")
            return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python ai_security_guard.py <command> [options]")
        print("命令:")
        print("  scan [path]     - 扫描项目或文件")
        print("  check <file>    - 检查单个文件")
        print("  report [json]   - 生成报告")
        return

    command = sys.argv[1]
    guard = AISecurityGuard()

    if command == "scan":
        path = sys.argv[2] if len(sys.argv) > 2 else "."
        print(f"🔍 扫描路径: {path}")
        guard.scan_project(path)
        print(guard.generate_report())

    elif command == "check":
        if len(sys.argv) < 3:
            print("❌ 请指定要检查的文件")
            return

        file_path = sys.argv[2]
        issues = guard.scan_file(file_path)

        if not issues:
            print(f"✅ 文件 {file_path} 未发现安全问题")
        else:
            print(f"🔍 文件 {file_path} 发现 {len(issues)} 个问题:")
            for issue in issues:
                print(f"  - {issue.description} (行 {issue.line_number})")
                print(f"    💡 {issue.suggestion}")

    elif command == "report":
        format_type = sys.argv[2] if len(sys.argv) > 2 else "text"
        guard.scan_project()
        print(guard.generate_report(format_type))

    else:
        print(f"❌ 未知命令: {command}")


if __name__ == "__main__":
    main()
