#!/usr/bin/env python3
"""
🩺 CI诊断助手 - 专为AI编程工具设计的CI问题诊断工具

这个脚本帮助AI工具快速识别和诊断CI失败的根本原因，
提供具体的修复建议和解决方案。
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


class CIDiagnostics:
    """CI诊断器 - 分析和诊断CI问题"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues: List[Dict] = []
        self.recommendations: List[str] = []

    def run_diagnosis(self) -> Dict:
        """运行完整的CI诊断流程"""
        print("🩺 开始CI诊断...")

        # 诊断检查项
        checks = [
            ("环境检查", self._check_environment),
            ("依赖检查", self._check_dependencies),
            ("配置文件检查", self._check_configs),
            ("代码质量检查", self._check_code_quality),
            ("测试状态检查", self._check_tests),
            ("Git状态检查", self._check_git_status),
            ("GitHub Actions检查", self._check_github_actions),
        ]

        results = {}
        for name, check_func in checks:
            print(f"🔍 {name}...")
            try:
                result = check_func()
                results[name] = result
                if not result.get('success', True):
                    self.issues.extend(result.get('issues', []))
            except Exception as e:
                results[name] = {
                    'success': False,
                    'error': str(e),
                    'issues': [{
                        'severity': 'error',
                        'message': f"{name}失败: {e}"
                    }]
                }

        return self._generate_report(results)

    def _check_environment(self) -> Dict:
        """检查开发环境"""
        issues = []

        # 检查虚拟环境
        if not (self.project_root / ".venv").exists():
            issues.append({
                'severity': 'critical',
                'message': '虚拟环境不存在',
                'solution': 'poetry install 或 python -m venv .venv'
            })

        # 检查Python版本
        try:
            result = subprocess.run(
                [sys.executable, '--version'],
                capture_output=True, text=True
            )
            python_version = result.stdout.strip()
            if "3.11" not in python_version:
                issues.append({
                    'severity': 'warning',
                    'message': f'Python版本可能不匹配: {python_version}',
                    'solution': '确保使用Python 3.11.x'
                })
        except Exception as e:
            issues.append({
                'severity': 'error',
                'message': f'无法检测Python版本: {e}',
                'solution': '检查Python安装'
            })

        return {'success': len(issues) == 0, 'issues': issues}

    def _check_dependencies(self) -> Dict:
        """检查依赖问题"""
        issues = []

        # 检查poetry.lock存在
        if not (self.project_root / "poetry.lock").exists():
            issues.append({
                'severity': 'critical',
                'message': 'poetry.lock文件缺失',
                'solution': 'poetry lock'
            })

        # 检查requirements.lock同步
        if (self.project_root / "requirements.lock").exists():
            try:
                # 检查requirements.lock是否包含关键依赖
                with open(self.project_root / "requirements.lock") as f:
                    content = f.read()
                    critical_deps = ['pytest', 'mypy', 'ruff', 'bandit']
                    missing_deps = [
                        dep for dep in critical_deps if dep not in content
                    ]
                    if missing_deps:
                        issues.append({
                            'severity': 'critical',
                            'message': (
                                f'requirements.lock缺少关键依赖: '
                                f'{missing_deps}'
                            ),
                            'solution': (
                                'poetry export 或切换到poetry install --with dev'
                            )
                        })
            except Exception as e:
                issues.append({
                    'severity': 'warning',
                    'message': f'无法读取requirements.lock: {e}',
                    'solution': '检查文件权限或重新生成'
                })

        # 尝试导入关键模块
        try:
            import bandit  # noqa: F401 # type: ignore
            import mypy  # noqa: F401 # type: ignore
            import pytest  # noqa: F401 # type: ignore
            import ruff  # noqa: F401 # type: ignore
        except ImportError as e:
            issues.append({
                'severity': 'critical',
                'message': f'关键开发工具缺失: {e}',
                'solution': 'poetry install --with dev'
            })

        return {'success': len(issues) == 0, 'issues': issues}

    def _check_configs(self) -> Dict:
        """检查配置文件"""
        issues = []

        # 检查pyproject.toml语法
        try:
            import tomllib
            with open(self.project_root / "pyproject.toml", 'rb') as f:
                tomllib.load(f)
        except Exception as e:
            issues.append({
                'severity': 'critical',
                'message': f'pyproject.toml语法错误: {e}',
                'solution': '修复TOML语法错误'
            })

        # 检查GitHub Actions配置
        workflows_dir = self.project_root / ".github" / "workflows"
        if workflows_dir.exists():
            try:
                import yaml
                for workflow_file in workflows_dir.glob("*.yml"):
                    with open(workflow_file) as f:
                        yaml.safe_load(f)
            except Exception as e:
                issues.append({
                    'severity': 'critical',
                    'message': f'GitHub Actions配置错误: {e}',
                    'solution': '修复YAML语法错误'
                })

        return {'success': len(issues) == 0, 'issues': issues}

    def _check_code_quality(self) -> Dict:
        """检查代码质量"""
        issues = []

        # 检查格式化
        try:
            result = subprocess.run(
                ['poetry', 'run', 'ruff', 'check', '.'],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode != 0:
                issues.append({
                    'severity': 'warning',
                    'message': 'Ruff检查失败',
                    'solution': 'poetry run ruff check --fix .',
                    'details': result.stdout
                })
        except Exception as e:
            issues.append({
                'severity': 'error',
                'message': f'无法运行ruff检查: {e}',
                'solution': '确保ruff已安装: poetry install --with dev'
            })

        # 检查类型注解
        try:
            result = subprocess.run(
                ['poetry', 'run', 'mypy', 'apps/', 'data_pipeline/'],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode != 0:
                details = result.stdout
                if len(details) > 500:
                    details = details[:500] + "..."
                issues.append({
                    'severity': 'warning',
                    'message': 'MyPy类型检查失败',
                    'solution': '修复类型注解错误',
                    'details': details
                })
        except Exception as e:
            issues.append({
                'severity': 'error',
                'message': f'无法运行mypy检查: {e}',
                'solution': '确保mypy已安装: poetry install --with dev'
            })

        critical_count = len([
            i for i in issues if i['severity'] == 'critical'
        ])
        return {'success': critical_count == 0, 'issues': issues}

    def _check_tests(self) -> Dict:
        """检查测试状态"""
        issues = []

        # 检查是否有测试文件
        test_dirs = [self.project_root / "tests"]
        test_files = []
        for test_dir in test_dirs:
            if test_dir.exists():
                test_files.extend(list(test_dir.rglob("test_*.py")))

        if not test_files:
            issues.append({
                'severity': 'warning',
                'message': '未找到测试文件',
                'solution': '创建测试文件或检查测试目录结构'
            })

        # 运行快速测试
        try:
            result = subprocess.run(
                ['poetry', 'run', 'pytest', '--collect-only', '-q'],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode != 0:
                issues.append({
                    'severity': 'critical',
                    'message': '测试收集失败',
                    'solution': '修复测试导入或语法错误',
                    'details': result.stderr
                })
        except Exception as e:
            issues.append({
                'severity': 'error',
                'message': f'无法运行pytest: {e}',
                'solution': '确保pytest已安装: poetry install --with dev'
            })

        critical_count = len([
            i for i in issues if i['severity'] == 'critical'
        ])
        return {'success': critical_count == 0, 'issues': issues}

    def _check_git_status(self) -> Dict:
        """检查Git状态"""
        issues = []

        try:
            # 检查未提交的更改
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                capture_output=True, text=True, cwd=self.project_root
            )
            if result.stdout.strip():
                issues.append({
                    'severity': 'info',
                    'message': '有未提交的更改',
                    'solution': 'git add . && git commit -m "..." 或 git stash'
                })

            # 检查远程状态
            result = subprocess.run(
                ['git', 'status', '-b', '--porcelain'],
                capture_output=True, text=True, cwd=self.project_root
            )
            if 'ahead' in result.stdout or 'behind' in result.stdout:
                issues.append({
                    'severity': 'info',
                    'message': '本地分支与远程不同步',
                    'solution': 'git pull 或 git push'
                })

        except Exception as e:
            issues.append({
                'severity': 'warning',
                'message': f'Git状态检查失败: {e}',
                'solution': '检查是否在Git仓库中'
            })

        return {'success': True, 'issues': issues}

    def _check_github_actions(self) -> Dict:
        """检查GitHub Actions状态"""
        issues = []

        # 检查是否有.github/workflows目录
        workflows_dir = self.project_root / ".github" / "workflows"
        if not workflows_dir.exists():
            issues.append({
                'severity': 'warning',
                'message': 'GitHub Actions工作流目录不存在',
                'solution': '创建 .github/workflows/ 目录和CI配置'
            })
            return {'success': True, 'issues': issues}

        # 检查工作流文件
        workflow_files = list(workflows_dir.glob("*.yml"))
        if not workflow_files:
            issues.append({
                'severity': 'warning',
                'message': '未找到GitHub Actions工作流文件',
                'solution': '添加CI配置文件如 ci.yml'
            })

        # 尝试获取最近的Actions状态（如果有gh CLI）
        try:
            cmd = [
                'gh', 'run', 'list', '--limit', '5',
                '--json', 'status,conclusion,name'
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0:
                runs = json.loads(result.stdout)
                failed_runs = [
                    r for r in runs if r.get('conclusion') == 'failure'
                ]
                if failed_runs:
                    issues.append({
                        'severity': 'warning',
                        'message': f'检测到 {len(failed_runs)} 个失败的工作流运行',
                        'solution': 'gh run view <run-id> --log 查看详细错误日志'
                    })
        except (subprocess.SubprocessError, FileNotFoundError,
                json.JSONDecodeError):
            # gh CLI不可用或无权限，跳过
            pass

        critical_count = len([
            i for i in issues if i['severity'] == 'critical'
        ])
        return {'success': critical_count == 0, 'issues': issues}

    def _generate_report(self, results: Dict) -> Dict:
        """生成诊断报告"""
        critical_issues = [
            i for i in self.issues if i['severity'] == 'critical'
        ]
        warning_issues = [i for i in self.issues if i['severity'] == 'warning']
        info_issues = [i for i in self.issues if i['severity'] == 'info']

        # 生成修复建议
        recommendations = []
        if critical_issues:
            recommendations.append("🚨 **立即修复关键问题**: 这些问题会阻止CI通过")
            for issue in critical_issues[:3]:  # 只显示前3个最重要的
                recommendations.append(
                    f"  - {issue['message']}: {issue['solution']}"
                )

        if warning_issues:
            recommendations.append("⚠️ **建议修复警告**: 这些问题可能影响代码质量")
            for issue in warning_issues[:2]:  # 只显示前2个
                recommendations.append(
                    f"  - {issue['message']}: {issue['solution']}"
                )

        # 生成快速修复命令
        quick_fixes = []
        if any('依赖' in i['message'] for i in critical_issues):
            quick_fixes.append("poetry install --with dev")
        if any('格式' in i['message'] or 'ruff' in i['message']
               for i in self.issues):
            quick_fixes.append("poetry run ruff check --fix .")
        if any('类型' in i['message'] or 'mypy' in i['message']
               for i in self.issues):
            quick_fixes.append("poetry run mypy apps/ data_pipeline/")

        return {
            'success': len(critical_issues) == 0,
            'summary': {
                'critical': len(critical_issues),
                'warnings': len(warning_issues),
                'info': len(info_issues)
            },
            'issues': self.issues,
            'recommendations': recommendations,
            'quick_fixes': quick_fixes,
            'results': results
        }


def main() -> None:
    """主函数"""
    project_root = Path(__file__).parent.parent
    diagnostics = CIDiagnostics(project_root)

    print("🩺 AI工具CI诊断助手")
    print("=" * 50)

    report = diagnostics.run_diagnosis()

    # 显示摘要
    summary = report['summary']
    print("\n📊 诊断摘要:")
    print(f"  🚨 关键问题: {summary['critical']}")
    print(f"  ⚠️ 警告: {summary['warnings']}")
    print(f"  ℹ️ 信息: {summary['info']}")

    # 显示建议
    if report['recommendations']:
        print("\n💡 修复建议:")
        for rec in report['recommendations']:
            print(f"  {rec}")

    # 显示快速修复命令
    if report['quick_fixes']:
        print("\n🔧 快速修复命令:")
        for fix in report['quick_fixes']:
            print(f"  {fix}")

    # 保存详细报告
    report_file = project_root / "ci-diagnosis-report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n📄 详细报告已保存到: {report_file}")

    # 如果有关键问题，返回非零退出码
    if summary['critical'] > 0:
        print(f"\n❌ 发现 {summary['critical']} 个关键问题，需要立即修复！")
        sys.exit(1)
    elif summary['warnings'] > 0:
        print(f"\n⚠️ 发现 {summary['warnings']} 个警告，建议修复。")
        sys.exit(0)
    else:
        print("\n✅ CI环境健康，未发现问题！")
        sys.exit(0)


if __name__ == "__main__":
    main()
