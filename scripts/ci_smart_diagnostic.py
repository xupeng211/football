#!/usr/bin/env python3
"""
🧠 智能CI诊断工具 - 分析GitHub Actions失败
============================================

独立工具,可以:
1. 分析GitHub Actions失败日志
2. 提供智能解决方案
3. 自动生成修复建议
4. 预测潜在问题
"""

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class DiagnosticResult:
    """诊断结果"""

    issue_type: str
    confidence: float
    error_pattern: str
    suggested_solutions: list[str]
    auto_fix_commands: list[str]
    priority: str  # "high", "medium", "low"


class GitHubActionsDiagnostic:
    """GitHub Actions智能诊断器"""

    def __init__(self):
        self.diagnostic_rules = {
            "module_import_error": {
                "patterns": [
                    r"ModuleNotFoundError: No module named '(.+)'",
                    r"ImportError: cannot import name '(.+)'",
                    r"ImportError: No module named '(.+)'",
                ],
                "solutions": [
                    "检查模块是否在requirements.txt中",
                    "验证PYTHONPATH设置",
                    "确认__init__.py文件存在",
                    "检查模块安装是否成功",
                ],
                "auto_fix": [
                    "uv add {module_name}",
                    "export PYTHONPATH=$PYTHONPATH:./src",
                ],
                "priority": "high",
            },
            "database_connection_error": {
                "patterns": [
                    r"connection to server .+ refused",
                    r"could not connect to server",
                    r"database .+ does not exist",
                    r"role .+ does not exist",
                ],
                "solutions": [
                    "等待数据库服务完全启动",
                    "检查数据库连接字符串",
                    "验证数据库用户权限",
                    "确认数据库已创建",
                ],
                "auto_fix": [
                    "docker-compose up -d postgres",
                    "sleep 10",
                    "PGPASSWORD=test_pass createdb -h localhost -U test_user test_football_db",
                ],
                "priority": "high",
            },
            "jwt_token_expired": {
                "patterns": [
                    r"ExpiredSignatureError: Signature has expired",
                    r"Token expired",
                    r"jwt.exceptions.ExpiredSignatureError",
                ],
                "solutions": [
                    "增加JWT token有效期",
                    "Mock时间相关函数",
                    "跳过时间敏感测试",
                    "使用固定的测试时间",
                ],
                "auto_fix": [
                    "@pytest.mark.skip(reason='JWT timing issue in CI')",
                    "Mock datetime.utcnow()",
                ],
                "priority": "medium",
            },
            "cache_manager_attribute_error": {
                "patterns": [
                    r"AttributeError: .+ object has no attribute '_serialize_value'",
                    r"AttributeError: .+ object has no attribute '_deserialize_value'",
                    r"AttributeError: .+ 'CacheManager' object has no attribute",
                ],
                "solutions": [
                    "检查CacheManager API变更",
                    "更新测试以匹配新的接口",
                    "跳过已废弃的内部方法测试",
                    "使用公共API替代私有方法",
                ],
                "auto_fix": ["@pytest.mark.skip(reason='CacheManager API changed')"],
                "priority": "medium",
            },
            "pydantic_validation_error": {
                "patterns": [
                    r"pydantic_core._pydantic_core.ValidationError",
                    r"validation error for (.+)",
                    r"Field required \[type=missing,",
                ],
                "solutions": [
                    "检查模型字段定义",
                    "添加缺失的required字段",
                    "验证数据类型匹配",
                    "更新测试数据格式",
                ],
                "auto_fix": ["添加缺失字段到模型实例", "检查字段类型匹配"],
                "priority": "high",
            },
            "timeout_error": {
                "patterns": [
                    r"TimeoutError",
                    r"timeout.*exceeded",
                    r"Operation timed out",
                ],
                "solutions": [
                    "增加超时时间设置",
                    "优化测试执行效率",
                    "检查网络连接稳定性",
                    "分解长时间运行的测试",
                ],
                "auto_fix": ["增加pytest超时设置", "使用--timeout参数"],
                "priority": "medium",
            },
        }

    def analyze_log(self, log_content: str) -> list[DiagnosticResult]:
        """分析日志内容并返回诊断结果"""
        results = []

        for issue_type, config in self.diagnostic_rules.items():
            for pattern in config["patterns"]:
                matches = re.finditer(
                    pattern, log_content, re.MULTILINE | re.IGNORECASE
                )

                for match in matches:
                    confidence = self._calculate_confidence(pattern, log_content)

                    result = DiagnosticResult(
                        issue_type=issue_type,
                        confidence=confidence,
                        error_pattern=match.group(0),
                        suggested_solutions=config["solutions"],
                        auto_fix_commands=config["auto_fix"],
                        priority=config["priority"],
                    )
                    results.append(result)

        # 按优先级和置信度排序
        results.sort(key=lambda x: (x.priority == "high", x.confidence), reverse=True)
        return results

    def _calculate_confidence(self, pattern: str, log_content: str) -> float:
        """计算诊断置信度"""
        matches = len(re.findall(pattern, log_content, re.MULTILINE | re.IGNORECASE))

        # 基于匹配次数计算置信度
        if matches >= 3:
            return 0.95
        elif matches == 2:
            return 0.80
        elif matches == 1:
            return 0.65
        else:
            return 0.0

    def get_github_actions_logs(self, run_id: str | None = None) -> str:
        """获取GitHub Actions日志"""
        try:
            if run_id:
                cmd = f"gh run view {run_id} --log"
            else:
                cmd = "gh run list --limit 1 --json databaseId --jq '.[0].databaseId' | xargs gh run view --log"

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout
            else:
                print(f"❌ 获取日志失败: {result.stderr}")
                return ""
        except Exception as e:
            print(f"❌ 获取日志异常: {e}")
            return ""

    def generate_fix_script(self, diagnostics: list[DiagnosticResult]) -> str:
        """生成自动修复脚本"""
        script_lines = [
            "#!/bin/bash",
            "# 🔧 自动生成的CI修复脚本",
            "# 基于智能诊断结果",
            "",
            "echo '🔧 执行CI问题自动修复...'",
            "",
        ]

        for i, diagnostic in enumerate(diagnostics[:5]):  # 只处理前5个高优先级问题
            script_lines.extend(
                [
                    f"# 修复问题 {i + 1}: {diagnostic.issue_type}",
                    f"# 置信度: {diagnostic.confidence:.2f}",
                    f"echo '修复: {diagnostic.issue_type}...'",
                    "",
                ]
            )

            for cmd in diagnostic.auto_fix_commands:
                script_lines.append(f"{cmd}")

            script_lines.append("")

        script_lines.extend(
            [
                "echo '✅ 自动修复完成'",
                "echo '🧪 重新运行测试验证修复效果...'",
                "make ci-check",
            ]
        )

        return "\n".join(script_lines)

    def save_diagnostic_report(
        self, diagnostics: list[DiagnosticResult], output_path: Path
    ):
        """保存诊断报告"""
        report = {
            "timestamp": str(Path.cwd()),
            "total_issues": len(diagnostics),
            "high_priority": len([d for d in diagnostics if d.priority == "high"]),
            "diagnostics": [asdict(d) for d in diagnostics],
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    print("🧠 智能CI诊断工具")
    print("=" * 40)

    diagnostic = GitHubActionsDiagnostic()

    # 获取最新的GitHub Actions日志
    print("📥 获取GitHub Actions日志...")
    log_content = diagnostic.get_github_actions_logs()

    if not log_content:
        print("⚠️ 无法获取日志,使用本地错误模拟...")
        # 可以在这里添加本地错误日志分析
        return

    # 分析日志
    print("🔍 分析失败原因...")
    diagnostics = diagnostic.analyze_log(log_content)

    if not diagnostics:
        print("✅ 未发现明显问题")
        return

    # 显示诊断结果
    print(f"\n🎯 发现 {len(diagnostics)} 个问题:")
    print("-" * 40)

    for i, diag in enumerate(diagnostics[:5], 1):
        print(f"\n{i}. {diag.issue_type}")
        print(f"   优先级: {diag.priority.upper()}")
        print(f"   置信度: {diag.confidence:.2f}")
        print(f"   错误模式: {diag.error_pattern[:80]}...")
        print("   建议解决方案:")
        for solution in diag.suggested_solutions[:2]:
            print(f"     • {solution}")

    # 生成修复脚本
    print("\n🔧 生成自动修复脚本...")
    fix_script = diagnostic.generate_fix_script(diagnostics)

    fix_script_path = Path("scripts/auto_fix_ci.sh")
    fix_script_path.write_text(fix_script)
    fix_script_path.chmod(0o755)

    print(f"✅ 修复脚本已生成: {fix_script_path}")
    print("💡 运行: ./scripts/auto_fix_ci.sh")

    # 保存诊断报告
    report_path = Path("data/ci_diagnostic_report.json")
    report_path.parent.mkdir(exist_ok=True)
    diagnostic.save_diagnostic_report(diagnostics, report_path)
    print(f"📊 诊断报告已保存: {report_path}")


if __name__ == "__main__":
    main()
