#!/usr/bin/env python3
"""
🤖 AI工具自动初始化脚本

当AI编程工具进入项目时，自动执行以下操作：
1. 获取完整项目上下文
2. 诊断CI/开发环境状态  
3. 验证上下文信息时效性
4. 生成AI工具工作准备报告

这确保AI工具始终以最佳状态开始工作，无需人工提醒。
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict


class AIAutoInitializer:
    """AI工具自动初始化器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.reports = {}
        self.ready_status = {
            'environment': False,
            'context': False,
            'diagnostics': False,
            'recommendations': []
        }

    def run_auto_initialization(self) -> Dict:
        """运行完整的AI工具自动初始化流程"""
        print("🤖 AI工具自动初始化中...")
        print("=" * 60)
        print("🎯 目标: 为AI工具准备最佳工作环境和上下文")
        print("=" * 60)

        # 初始化步骤
        steps = [
            ("🔍 检查项目环境", self._check_environment),
            ("📚 加载项目上下文", self._load_project_context),
            ("🩺 运行环境诊断", self._run_diagnostics),
            ("🔍 验证上下文质量", self._validate_context),
            ("📊 生成工作准备报告", self._generate_readiness_report),
        ]

        start_time = time.time()

        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            try:
                result = step_func()
                self.reports[step_name] = result
                if result.get('success', True):
                    print(f"  ✅ {step_name} 完成")
                else:
                    print(f"  ⚠️ {step_name} 有问题，但继续执行")
            except Exception as e:
                print(f"  ❌ {step_name} 失败: {e}")
                self.reports[step_name] = {'success': False, 'error': str(e)}

        elapsed = time.time() - start_time
        print(f"\n⏱️ 初始化耗时: {elapsed:.2f}秒")

        return self._finalize_initialization()

    def _check_environment(self) -> Dict:
        """检查基础开发环境"""
        checks = {
            'venv_active': 'VIRTUAL_ENV' in os.environ,
            'poetry_available': self._command_exists('poetry'),
            'git_repo': (self.project_root / '.git').exists(),
            'pyproject_exists': (
                self.project_root / 'pyproject.toml'
            ).exists(),
        }

        all_good = all(checks.values())
        if all_good:
            self.ready_status['environment'] = True

        return {
            'success': all_good,
            'checks': checks,
            'message': '✅ 环境就绪' if all_good else '⚠️ 环境可能有问题'
        }

    def _load_project_context(self) -> Dict:
        """加载完整项目上下文"""
        try:
            # 检查上下文文件是否存在
            context_file = self.project_root / "context/_pack.md"

            if not context_file.exists():
                print("  📦 上下文包不存在，正在生成...")
                result = subprocess.run(
                    ['make', 'regen.context'],
                    capture_output=True, text=True,
                    cwd=self.project_root
                )
                if result.returncode != 0:
                    return {
                        'success': False,
                        'error': f'上下文生成失败: {result.stderr}'
                    }

            # 读取上下文内容
            if context_file.exists():
                context_content = context_file.read_text(encoding='utf-8')
                context_size = len(context_content)

                # 分析上下文质量
                has_architecture = 'ARCHITECTURE.md' in context_content
                has_tasks = 'TASKS.md' in context_content
                has_ci_knowledge = 'CI_KNOWLEDGE_BASE.md' in context_content
                has_dev_guide = 'DEVELOPER_GUIDE.md' in context_content

                quality_score = sum([
                    has_architecture, has_tasks,
                    has_ci_knowledge, has_dev_guide,
                    context_size > 5000  # 内容充实度
                ]) / 5 * 100

                self.ready_status['context'] = quality_score >= 80

                return {
                    'success': True,
                    'context_size': context_size,
                    'quality_score': quality_score,
                    'sections': {
                        'architecture': has_architecture,
                        'tasks': has_tasks,
                        'ci_knowledge': has_ci_knowledge,
                        'dev_guide': has_dev_guide
                    },
                    'message': f'📚 上下文已加载 (质量: {quality_score:.0f}%)'
                }
            else:
                return {
                    'success': False,
                    'error': '无法生成或读取上下文文件'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'上下文加载失败: {e}'
            }

    def _run_diagnostics(self) -> Dict:
        """运行环境诊断"""
        try:
            result = subprocess.run(
                ['make', 'diagnose-ci'],
                capture_output=True, text=True,
                cwd=self.project_root
            )

            # 解析诊断结果
            success = result.returncode == 0

            # 尝试读取诊断报告
            report_file = self.project_root / "ci-diagnosis-report.json"
            if report_file.exists():
                with open(report_file, encoding='utf-8') as f:
                    diagnosis_data = json.load(f)

                critical_count = diagnosis_data['summary']['critical']
                warning_count = diagnosis_data['summary']['warnings']

                # 如果没有关键问题，认为诊断通过
                self.ready_status['diagnostics'] = critical_count == 0

                # 收集修复建议
                if critical_count > 0:
                    self.ready_status['recommendations'].extend(
                        diagnosis_data.get('quick_fixes', [])
                    )

                return {
                    'success': critical_count == 0,
                    'critical_issues': critical_count,
                    'warnings': warning_count,
                    'quick_fixes': diagnosis_data.get('quick_fixes', []),
                    'message': (
                        f'🩺 诊断完成: {critical_count}个关键问题, '
                        f'{warning_count}个警告'
                    )
                }
            else:
                return {
                    'success': success,
                    'message': '🩺 诊断运行完成，但无详细报告'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'诊断失败: {e}'
            }

    def _validate_context(self) -> Dict:
        """验证上下文质量"""
        try:
            result = subprocess.run(
                ['make', 'validate-context'],
                capture_output=True, text=True,
                cwd=self.project_root
            )

            # 尝试读取验证报告
            report_file = self.project_root / "context-validation-report.json"
            if report_file.exists():
                with open(report_file, encoding='utf-8') as f:
                    validation_data = json.load(f)

                health_score = validation_data.get('health_score', 0)
                critical_count = validation_data['summary']['critical']

                return {
                    'success': critical_count == 0,
                    'health_score': health_score,
                    'critical_issues': critical_count,
                    'message': f'🔍 上下文健康度: {health_score}%'
                }
            else:
                return {
                    'success': result.returncode == 0,
                    'message': '🔍 上下文验证完成'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'上下文验证失败: {e}'
            }

    def _generate_readiness_report(self) -> Dict:
        """生成AI工具工作准备报告"""
        overall_ready = all([
            self.ready_status['environment'],
            self.ready_status['context'],
            self.ready_status['diagnostics']
        ])

        # 计算准备度评分
        readiness_score = 0
        if self.ready_status['environment']:
            readiness_score += 30
        if self.ready_status['context']:
            readiness_score += 40
        if self.ready_status['diagnostics']:
            readiness_score += 30

        return {
            'success': True,
            'overall_ready': overall_ready,
            'readiness_score': readiness_score,
            'status': self.ready_status,
            'message': f'📊 AI工具准备度: {readiness_score}%'
        }

    def _finalize_initialization(self) -> Dict:
        """完成初始化并生成最终报告"""
        readiness_report = self.reports.get('📊 生成工作准备报告', {})
        readiness_score = readiness_report.get('readiness_score', 0)

        print("\n🎯 AI工具初始化完成!")
        print("=" * 60)

        # 显示准备度状态
        if readiness_score >= 90:
            status_icon = "🟢"
            status_text = "完全就绪"
            advice = "AI工具可以高效工作！"
        elif readiness_score >= 70:
            status_icon = "🟡"
            status_text = "基本就绪"
            advice = "有一些小问题，但不影响基本工作。"
        else:
            status_icon = "🔴"
            status_text = "需要修复"
            advice = "建议先解决关键问题再开始工作。"

        print(f"📊 整体状态: {status_icon} {status_text} ({readiness_score}%)")
        print(f"💡 建议: {advice}")

        # 显示修复建议
        if self.ready_status['recommendations']:
            print("\n🔧 快速修复命令:")
            for cmd in self.ready_status['recommendations'][:3]:
                print(f"  {cmd}")

        # 显示快速开始指南
        print("\n🚀 AI工具快速开始:")
        print("  📚 查看完整上下文: make show.context")
        print("  🩺 诊断问题: make diagnose-ci")
        print("  🔍 验证环境: make validate-context")
        print("  🛠️ 查看所有命令: make help")

        return {
            'success': readiness_score >= 70,
            'readiness_score': readiness_score,
            'status': self.ready_status,
            'recommendations': self.ready_status['recommendations'],
            'reports': self.reports
        }

    def _command_exists(self, command: str) -> bool:
        """检查命令是否存在"""
        try:
            subprocess.run(
                [command, '--version'],
                capture_output=True, check=True
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False


def main() -> None:
    """主函数"""
    project_root = Path(__file__).parent.parent

    print("🤖 欢迎使用足球预测系统!")
    print("🔧 正在为AI工具准备最佳工作环境...")

    initializer = AIAutoInitializer(project_root)
    result = initializer.run_auto_initialization()

    # 保存初始化报告
    report_file = project_root / "ai-initialization-report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n📄 详细初始化报告: {report_file}")

    # 设置退出码
    if result['success']:
        print("\n✅ AI工具已准备就绪，可以开始高效工作！")
        sys.exit(0)
    else:
        print("\n⚠️ 初始化完成，但有一些问题需要注意。")
        sys.exit(1)


if __name__ == "__main__":
    import os
    main()
