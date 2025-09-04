#!/usr/bin/env python3
"""
📡 实时CI监控系统 - GitHub Actions状态监控
============================================

功能:
1. 实时监控GitHub Actions运行状态
2. 智能预警和通知
3. 自动触发修复流程
4. 性能趋势分析
"""

import asyncio
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class CIRun:
    """CI运行记录"""

    run_id: str
    status: str  # "queued", "in_progress", "completed", "failure"
    conclusion: str | None  # "success", "failure", "cancelled"
    started_at: str
    completed_at: str | None
    duration_seconds: int | None
    commit_sha: str
    commit_message: str


@dataclass
class CIMetrics:
    """CI指标"""

    success_rate: float
    average_duration: float
    failure_patterns: dict[str, int]
    performance_trend: str  # "improving", "stable", "degrading"


class GitHubActionsMonitor:
    """GitHub Actions实时监控器"""

    def __init__(self, repo_owner: str, repo_name: str, token: str | None = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token
        self.runs_history: list[CIRun] = []
        self.monitoring = False

    def get_latest_runs(self, limit: int = 10) -> list[CIRun]:
        """获取最新的CI运行记录"""
        try:
            # 使用gh CLI获取运行记录
            cmd = f"gh run list --repo {self.repo_owner}/{self.repo_name} --limit {limit} --json databaseId,status,conclusion,createdAt,updatedAt,headSha,headBranch,displayTitle"

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"❌ 获取运行记录失败: {result.stderr}")
                return []

            runs_data = json.loads(result.stdout)
            ci_runs = []

            for run_data in runs_data:
                started_at = run_data.get("createdAt", "")
                completed_at = run_data.get("updatedAt", "")

                # 计算运行时间
                duration = None
                if (
                    started_at
                    and completed_at
                    and run_data.get("status") == "completed"
                ):
                    start_time = datetime.fromisoformat(
                        started_at.replace("Z", "+00:00")
                    )
                    end_time = datetime.fromisoformat(
                        completed_at.replace("Z", "+00:00")
                    )
                    duration = int((end_time - start_time).total_seconds())

                ci_run = CIRun(
                    run_id=str(run_data.get("databaseId", "")),
                    status=run_data.get("status", "unknown"),
                    conclusion=run_data.get("conclusion"),
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_seconds=duration,
                    commit_sha=run_data.get("headSha", "")[:8],
                    commit_message=run_data.get("displayTitle", "")[:50],
                )
                ci_runs.append(ci_run)

            return ci_runs

        except Exception as e:
            print(f"❌ 获取运行记录异常: {e}")
            return []

    def calculate_metrics(self, runs: list[CIRun]) -> CIMetrics:
        """计算CI性能指标"""
        if not runs:
            return CIMetrics(0.0, 0.0, {}, "unknown")

        # 计算成功率
        completed_runs = [r for r in runs if r.status == "completed"]
        if completed_runs:
            successful_runs = [r for r in completed_runs if r.conclusion == "success"]
            success_rate = len(successful_runs) / len(completed_runs)
        else:
            success_rate = 0.0

        # 计算平均运行时间
        durations = [r.duration_seconds for r in runs if r.duration_seconds]
        average_duration = sum(durations) / len(durations) if durations else 0.0

        # 分析失败模式
        failed_runs = [r for r in completed_runs if r.conclusion == "failure"]
        failure_patterns = {}
        for run in failed_runs:
            # 这里可以扩展为分析具体的失败原因
            pattern = f"failure_{run.commit_sha}"
            failure_patterns[pattern] = failure_patterns.get(pattern, 0) + 1

        # 分析性能趋势
        trend = self._analyze_performance_trend(runs)

        return CIMetrics(
            success_rate=success_rate,
            average_duration=average_duration,
            failure_patterns=failure_patterns,
            performance_trend=trend,
        )

    def _analyze_performance_trend(self, runs: list[CIRun]) -> str:
        """分析性能趋势"""
        if len(runs) < 3:
            return "insufficient_data"

        # 简单的趋势分析:比较最近3次和之前的成功率
        recent_runs = runs[:3]
        older_runs = runs[3:6] if len(runs) >= 6 else runs[3:]

        if not older_runs:
            return "stable"

        recent_success = len(
            [r for r in recent_runs if r.conclusion == "success"]
        ) / len(recent_runs)
        older_success = len([r for r in older_runs if r.conclusion == "success"]) / len(
            older_runs
        )

        if recent_success > older_success + 0.1:
            return "improving"
        elif recent_success < older_success - 0.1:
            return "degrading"
        else:
            return "stable"

    async def start_monitoring(self, interval_seconds: int = 60):
        """开始实时监控"""
        print(f"📡 开始监控GitHub Actions ({self.repo_owner}/{self.repo_name})")
        print(f"⏱️ 监控间隔: {interval_seconds}秒")
        print("=" * 50)

        self.monitoring = True
        previous_runs = []

        while self.monitoring:
            try:
                # 获取最新运行记录
                current_runs = self.get_latest_runs(20)

                if current_runs:
                    # 检查是否有新的运行或状态变化
                    new_or_changed = self._detect_changes(previous_runs, current_runs)

                    if new_or_changed:
                        await self._handle_status_changes(new_or_changed)

                    # 计算并显示指标
                    metrics = self.calculate_metrics(current_runs)
                    self._display_metrics(
                        metrics, current_runs[0] if current_runs else None
                    )

                    previous_runs = current_runs

                await asyncio.sleep(interval_seconds)

            except KeyboardInterrupt:
                print("\n⏹️ 监控已停止")
                self.monitoring = False
                break
            except Exception as e:
                print(f"❌ 监控异常: {e}")
                await asyncio.sleep(interval_seconds)

    def _detect_changes(
        self, previous: list[CIRun], current: list[CIRun]
    ) -> list[CIRun]:
        """检测运行状态变化"""
        if not previous:
            return current[:1]  # 返回最新的一个运行

        # 创建之前运行的映射
        prev_map = {run.run_id: run for run in previous}

        changes = []
        for run in current:
            prev_run = prev_map.get(run.run_id)
            if not prev_run or prev_run.status != run.status:
                changes.append(run)

        return changes

    async def _handle_status_changes(self, changed_runs: list[CIRun]):
        """处理状态变化"""
        for run in changed_runs:
            timestamp = datetime.now().strftime("%H:%M:%S")

            if run.status == "queued":
                print(f"[{timestamp}] 🔄 新的CI运行已排队: {run.commit_message}")
            elif run.status == "in_progress":
                print(f"[{timestamp}] ⚡ CI运行开始: {run.commit_message}")
            elif run.status == "completed":
                if run.conclusion == "success":
                    print(f"[{timestamp}] ✅ CI运行成功: {run.commit_message}")
                elif run.conclusion == "failure":
                    print(f"[{timestamp}] ❌ CI运行失败: {run.commit_message}")
                    await self._handle_failure(run)
                elif run.conclusion == "cancelled":
                    print(f"[{timestamp}] ⏹️ CI运行取消: {run.commit_message}")

    async def _handle_failure(self, failed_run: CIRun):
        """处理CI失败"""
        print(f"🚨 检测到CI失败 (Run ID: {failed_run.run_id})")

        # 自动触发智能诊断
        try:
            print("🧠 启动智能诊断...")
            diagnostic_cmd = (
                f"python scripts/ci_smart_diagnostic.py {failed_run.run_id}"
            )

            # 异步执行诊断
            process = await asyncio.create_subprocess_shell(
                diagnostic_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                print("✅ 智能诊断完成")
            else:
                print(f"⚠️ 智能诊断失败: {stderr.decode()}")

        except Exception as e:
            print(f"❌ 智能诊断异常: {e}")

    def _display_metrics(self, metrics: CIMetrics, latest_run: CIRun | None):
        """显示CI指标"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n📊 CI指标更新 ({timestamp})")
        print("-" * 40)
        print(f"✅ 成功率: {metrics.success_rate:.1%}")
        print(f"⏱️ 平均运行时间: {metrics.average_duration:.0f}秒")
        print(f"📈 性能趋势: {metrics.performance_trend}")

        if latest_run:
            status_emoji = {
                "queued": "🔄",
                "in_progress": "⚡",
                "completed": "✅" if latest_run.conclusion == "success" else "❌",
            }
            print(
                f"🔄 最新运行: {status_emoji.get(latest_run.status, '❓')} {latest_run.status}"
            )
            print(f"💬 提交信息: {latest_run.commit_message}")

        print()

    def save_monitoring_report(self, output_path: Path):
        """保存监控报告"""
        runs = self.get_latest_runs(50)
        metrics = self.calculate_metrics(runs)

        report = {
            "timestamp": datetime.now().isoformat(),
            "repository": f"{self.repo_owner}/{self.repo_name}",
            "metrics": asdict(metrics),
            "recent_runs": [asdict(run) for run in runs[:10]],
            "summary": {
                "total_runs_analyzed": len(runs),
                "recommendations": self._generate_recommendations(metrics),
            },
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def _generate_recommendations(self, metrics: CIMetrics) -> list[str]:
        """生成改进建议"""
        recommendations = []

        if metrics.success_rate < 0.8:
            recommendations.append("成功率偏低,建议加强本地CI检查")

        if metrics.average_duration > 600:  # 10分钟
            recommendations.append("CI运行时间过长,考虑优化测试并行度")

        if metrics.performance_trend == "degrading":
            recommendations.append("性能趋势下降,需要分析最近的变更")

        if len(metrics.failure_patterns) > 3:
            recommendations.append("失败模式多样,建议系统性分析失败原因")

        return recommendations


async def main():
    """主函数"""
    print("📡 GitHub Actions实时监控系统")
    print("=" * 40)

    # 从环境或配置获取仓库信息
    repo_owner = "your-username"  # 需要根据实际情况修改
    repo_name = "football-predict-system"

    monitor = GitHubActionsMonitor(repo_owner, repo_name)

    try:
        # 生成初始报告
        print("📊 生成监控报告...")
        report_path = Path("data/ci_monitoring_report.json")
        report_path.parent.mkdir(exist_ok=True)
        monitor.save_monitoring_report(report_path)
        print(f"✅ 报告已保存: {report_path}")

        # 开始实时监控
        await monitor.start_monitoring(interval_seconds=30)

    except KeyboardInterrupt:
        print("\n👋 监控已停止")
    except Exception as e:
        print(f"❌ 监控失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
