#!/usr/bin/env python3
"""
🔍 上下文验证工具 - 确保AI工具获得准确和及时的项目信息

这个脚本验证项目文档、架构信息和上下文数据的时效性,
确保AI工具始终获得最新和准确的项目状态。
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class ContextValidator:
    """上下文验证器 - 检查项目信息的准确性和时效性"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[Dict] = []
        self.warnings: List[Dict] = []
        self.info: List[Dict] = []

    def validate_all(self) -> Dict:
        """运行完整的上下文验证"""
        print("🔍 开始上下文验证...")

        validations = [
            ("文档时效性", self._validate_documentation_freshness),
            ("架构一致性", self._validate_architecture_consistency),
            ("依赖同步性", self._validate_dependency_sync),
            ("任务状态", self._validate_task_status),
            ("Git状态", self._validate_git_state),
            ("上下文完整性", self._validate_context_completeness),
        ]

        results = {}
        for name, validator in validations:
            print(f"🔍 验证{name}...")
            try:
                result = validator()
                results[name] = result
                self._categorize_issues(result.get("issues", []))
            except Exception as e:
                self.issues.append(
                    {
                        "type": "validation_error",
                        "message": f"{name}验证失败: {e}",
                        "fix": "检查验证逻辑或项目结构",
                    }
                )

        return self._generate_validation_report(results)

    def _categorize_issues(self, issues: List[Dict]) -> None:
        """分类问题到不同严重级别"""
        for issue in issues:
            severity = issue.get("severity", "info")
            if severity == "critical":
                self.issues.append(issue)
            elif severity == "warning":
                self.warnings.append(issue)
            else:
                self.info.append(issue)

    def _validate_documentation_freshness(self) -> Dict:
        """验证文档的时效性"""
        issues = []

        # 检查关键文档的最后修改时间
        key_docs = [
            "README.md",
            "docs/ARCHITECTURE.md",
            "docs/TASKS.md",
            "AI_DEVELOPMENT_GUIDELINES.md",
            "DEVELOPER_GUIDE.md",
        ]

        now = datetime.now()
        for doc_path in key_docs:
            file_path = self.project_root / doc_path
            if file_path.exists():
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                days_old = (now - mtime).days

                if days_old > 30:
                    issues.append(
                        {
                            "severity": "warning",
                            "type": "stale_documentation",
                            "message": f"{doc_path} 超过{days_old}天未更新",
                            "fix": "检查文档内容是否需要更新",
                        }
                    )
                elif days_old > 7:
                    issues.append(
                        {
                            "severity": "info",
                            "type": "aging_documentation",
                            "message": f"{doc_path} {days_old}天未更新",
                            "fix": "确认内容是否仍然准确",
                        }
                    )
            else:
                issues.append(
                    {
                        "severity": "critical",
                        "type": "missing_documentation",
                        "message": f"关键文档缺失: {doc_path}",
                        "fix": f"创建 {doc_path} 文档",
                    }
                )

        critical_count = len([i for i in issues if i["severity"] == "critical"])
        return {"success": critical_count == 0, "issues": issues}

    def _validate_architecture_consistency(self) -> Dict:
        """验证架构文档与实际代码结构的一致性"""
        issues = []

        # 读取架构文档中描述的模块
        arch_file = self.project_root / "docs/ARCHITECTURE.md"
        if arch_file.exists():
            content = arch_file.read_text(encoding="utf-8")

            # 提取文档中提到的目录结构
            documented_modules = []
            # 简单的正则匹配,查找类似 "apps/api", "data_pipeline/" 的模式
            module_patterns = re.findall(r"`([^`]+/[^`]*)`", content)
            documented_modules.extend(module_patterns)

            # 检查实际目录结构
            actual_modules = []
            for item in self.project_root.iterdir():
                if item.is_dir() and not item.name.startswith("."):
                    actual_modules.append(item.name)

            # 检查文档中提到但不存在的模块
            for module in documented_modules:
                module_path = self.project_root / module
                if not module_path.exists():
                    issues.append(
                        {
                            "severity": "warning",
                            "type": "missing_documented_module",
                            "message": f"架构文档提到的模块不存在: {module}",
                            "fix": f"创建 {module} 目录或更新文档",
                        }
                    )

        else:
            issues.append(
                {
                    "severity": "critical",
                    "type": "missing_architecture_doc",
                    "message": "架构文档缺失",
                    "fix": "创建 docs/ARCHITECTURE.md",
                }
            )

        critical_count = len([i for i in issues if i["severity"] == "critical"])
        return {"success": critical_count == 0, "issues": issues}

    def _validate_dependency_sync(self) -> Dict:
        """验证依赖文件的同步性"""
        issues = []

        # 检查 pyproject.toml vs poetry.lock 的同步
        pyproject_file = self.project_root / "pyproject.toml"
        poetry_lock = self.project_root / "poetry.lock"

        if pyproject_file.exists() and poetry_lock.exists():
            pyproject_mtime = pyproject_file.stat().st_mtime
            lock_mtime = poetry_lock.stat().st_mtime

            if pyproject_mtime > lock_mtime:
                issues.append(
                    {
                        "severity": "warning",
                        "type": "dependency_desync",
                        "message": "pyproject.toml 比 poetry.lock 更新",
                        "fix": "poetry lock 重新生成锁定文件",
                    }
                )

        # 检查 requirements.lock 是否过时
        requirements_lock = self.project_root / "requirements.lock"
        if requirements_lock.exists():
            req_mtime = requirements_lock.stat().st_mtime
            if pyproject_file.exists():
                pyproject_mtime = pyproject_file.stat().st_mtime
                if pyproject_mtime > req_mtime:
                    issues.append(
                        {
                            "severity": "info",
                            "type": "requirements_outdated",
                            "message": "requirements.lock 可能过时",
                            "fix": "重新生成 requirements.lock 文件",
                        }
                    )

        return {"success": True, "issues": issues}

    def _validate_task_status(self) -> Dict:
        """验证任务文档的状态准确性"""
        issues = []

        tasks_file = self.project_root / "docs/TASKS.md"
        if tasks_file.exists():
            content = tasks_file.read_text(encoding="utf-8")

            # 统计不同状态的任务
            todo_count = content.count("- [ ]")
            done_count = content.count("- [x]")

            if todo_count == 0 and done_count > 0:
                issues.append(
                    {
                        "severity": "info",
                        "type": "all_tasks_complete",
                        "message": "所有任务已完成,考虑添加新任务",
                        "fix": "更新任务列表或归档已完成任务",
                    }
                )
            elif todo_count > 10:
                issues.append(
                    {
                        "severity": "warning",
                        "type": "too_many_pending_tasks",
                        "message": f"待办任务过多 ({todo_count}项)",
                        "fix": "优先级排序或分解大任务",
                    }
                )

            # 检查任务文档的更新时间
            mtime = datetime.fromtimestamp(tasks_file.stat().st_mtime)
            days_old = (datetime.now() - mtime).days
            if days_old > 7:
                issues.append(
                    {
                        "severity": "info",
                        "type": "stale_task_list",
                        "message": f"任务列表 {days_old} 天未更新",
                        "fix": "更新任务状态或添加新任务",
                    }
                )

        return {"success": True, "issues": issues}

    def _validate_git_state(self) -> Dict:
        """验证Git状态对AI工具的影响"""
        issues = []

        try:
            # 检查是否有大量未跟踪文件
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                if result.stdout.strip():
                    lines = result.stdout.strip().split("\n")
                else:
                    lines = []
                untracked_files = [line for line in lines if line.startswith("??")]

                if len(untracked_files) > 10:
                    issues.append(
                        {
                            "severity": "warning",
                            "type": "too_many_untracked_files",
                            "message": (f"未跟踪文件过多 ({len(untracked_files)}个)"),
                            "fix": "添加到 .gitignore 或提交重要文件",
                        }
                    )

                # 检查是否有冲突文件
                conflict_files = [line for line in lines if "UU" in line[:2]]
                if conflict_files:
                    issues.append(
                        {
                            "severity": "critical",
                            "type": "merge_conflicts",
                            "message": f"存在合并冲突文件: {len(conflict_files)}个",
                            "fix": "解决合并冲突",
                        }
                    )

        except subprocess.SubprocessError:
            issues.append(
                {
                    "severity": "warning",
                    "type": "git_check_failed",
                    "message": "Git状态检查失败",
                    "fix": "确保在Git仓库中运行",
                }
            )

        critical_count = len([i for i in issues if i["severity"] == "critical"])
        return {"success": critical_count == 0, "issues": issues}

    def _validate_context_completeness(self) -> Dict:
        """验证上下文包的完整性"""
        issues = []

        context_file = self.project_root / "context/_pack.md"
        if context_file.exists():
            content = context_file.read_text(encoding="utf-8")

            # 检查是否包含关键章节
            required_sections = ["ARCHITECTURE.md", "TASKS.md", "dev_log.md"]

            missing_sections = []
            for section in required_sections:
                section_marker1 = f"=== {section} ==="
                section_marker2 = f"docs/{section}"
                if section_marker1 not in content and section_marker2 not in content:
                    missing_sections.append(section)

            if missing_sections:
                issues.append(
                    {
                        "severity": "warning",
                        "type": "incomplete_context_pack",
                        "message": f"上下文包缺少章节: {missing_sections}",
                        "fix": "make regen.context 重新生成上下文包",
                    }
                )

            # 检查内容长度,过短可能不完整
            if len(content) < 1000:
                issues.append(
                    {
                        "severity": "warning",
                        "type": "thin_context_pack",
                        "message": "上下文包内容过少",
                        "fix": "检查源文档或重新生成",
                    }
                )
        else:
            issues.append(
                {
                    "severity": "critical",
                    "type": "missing_context_pack",
                    "message": "上下文包文件不存在",
                    "fix": "make regen.context 生成上下文包",
                }
            )

        critical_count = len([i for i in issues if i["severity"] == "critical"])
        return {"success": critical_count == 0, "issues": issues}

    def _generate_validation_report(self, results: Dict) -> Dict:
        """生成验证报告"""
        total_issues = len(self.issues)
        total_warnings = len(self.warnings)
        total_info = len(self.info)

        # 生成修复建议
        recommendations = []
        if self.issues:
            recommendations.append("🚨 **关键问题需要立即修复**:")
            for issue in self.issues[:3]:
                recommendations.append(f"  - {issue['message']}: {issue['fix']}")

        if self.warnings:
            recommendations.append("⚠️ **建议修复警告**:")
            for warning in self.warnings[:3]:
                recommendations.append(f"  - {warning['message']}: {warning['fix']}")

        # 生成健康度评分
        total_checks = sum(len(r.get("issues", [])) for r in results.values()) or 1
        healthy_checks = total_checks - total_issues - total_warnings
        health_score = int((healthy_checks / total_checks) * 100)

        return {
            "success": total_issues == 0,
            "health_score": health_score,
            "summary": {
                "critical": total_issues,
                "warnings": total_warnings,
                "info": total_info,
            },
            "all_issues": self.issues + self.warnings + self.info,
            "recommendations": recommendations,
            "results": results,
        }


def main() -> None:
    """主函数"""
    project_root = Path(__file__).parent.parent
    validator = ContextValidator(project_root)

    print("🔍 AI工具上下文验证器")
    print("=" * 50)

    report = validator.validate_all()

    # 显示健康度评分
    health_score = report["health_score"]
    if health_score >= 90:
        health_icon = "🟢"
        health_status = "优秀"
    elif health_score >= 80:
        health_icon = "🟡"
        health_status = "良好"
    elif health_score >= 70:
        health_icon = "🟠"
        health_status = "合格"
    else:
        health_icon = "🔴"
        health_status = "需改进"

    print(f"\n📊 上下文健康度: {health_icon} {health_score}/100 ({health_status})")

    # 显示摘要
    summary = report["summary"]
    print("\n📈 验证摘要:")
    print(f"  🚨 关键问题: {summary['critical']}")
    print(f"  ⚠️ 警告: {summary['warnings']}")
    print(f"  🟦 信息: {summary['info']}")

    # 显示建议
    if report["recommendations"]:
        print("\n💡 修复建议:")
        for rec in report["recommendations"]:
            print(f"  {rec}")

    # 保存详细报告
    report_file = project_root / "context-validation-report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n📄 详细报告已保存到: {report_file}")

    # 根据结果设置退出码
    if summary["critical"] > 0:
        msg = f"\n❌ 发现 {summary['critical']} 个关键问题,AI工具可能获得过时信息!"
        print(msg)
        sys.exit(1)
    elif summary["warnings"] > 3:
        msg = f"\n⚠️ 警告较多 ({summary['warnings']}个),建议优化上下文质量。"
        print(msg)
        sys.exit(0)
    else:
        print("\n✅ 上下文信息健康,AI工具可获得准确信息!")
        sys.exit(0)


if __name__ == "__main__":
    main()
