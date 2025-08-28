#!/usr/bin/env python3
"""
依赖冲突检测和自动修复工具

检测requirements.txt中的包版本冲突并提供自动修复建议
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


def print_banner() -> None:
    """打印工具横幅"""
    print("=" * 60)
    print("🔍 依赖冲突检测和修复工具")
    print("=" * 60)


class DependencyConflictDetector:
    """依赖冲突检测器"""

    def __init__(self, requirements_file: str = "requirements.txt"):
        self.requirements_file = requirements_file
        self.known_conflicts = {
            "pycodestyle": {
                "description": "autopep8需要pycodestyle>=2.12.0",
                "solution": "pycodestyle>=2.12.0",
            },
            "flake8": {
                "description": "flake8版本与pycodestyle/pyflakes不兼容",
                "solution": "flake8>=7.3.0",
            },
            "isort": {
                "description": "pylint需要isort!=5.13.0",
                "solution": "isort>=5.12.0,!=5.13.0",
            },
            "safety": {
                "description": "safety需要pydantic>=2.0兼容",
                "solution": "safety>=3.2.0",
            },
            "pyflakes": {
                "description": "flake8需要pyflakes>=3.4.0,<3.5.0",
                "solution": "pyflakes>=3.4.0,<3.5.0",
            },
        }

    def get_requirements_dict(self) -> Dict[str, str]:
        """解析requirements.txt文件"""
        requirements: Dict[str, str] = {}
        try:
            with open(self.requirements_file) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and not line.startswith("-"):
                        # 提取包名和版本约束
                        if "==" in line:
                            name, version = line.split("==", 1)
                            requirements[name] = f"=={version}"
                        elif ">=" in line:
                            name = line.split(">=")[0]
                            requirements[name] = line[len(name) :]
                        elif ">" in line:
                            name = line.split(">")[0]
                            requirements[name] = line[len(name) :]
                        elif "<=" in line:
                            name = line.split("<=")[0]
                            requirements[name] = line[len(name) :]
                        elif "<" in line:
                            name = line.split("<")[0]
                            requirements[name] = line[len(name) :]
                        else:
                            requirements[line] = ""
        except FileNotFoundError:
            print(f"❌ 找不到文件: {self.requirements_file}")
            sys.exit(1)
        return requirements

    def detect_conflicts_via_pip(self) -> List[Dict[str, Any]]:
        """使用pip检测依赖冲突"""
        conflicts: List[Dict[str, Any]] = []
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as tmp_file:
                tmp_path = tmp_file.name

            # 使用pip的依赖解析器检测冲突
            result = subprocess.run(  # nosec B603 B607
                [
                    "pip",
                    "install",
                    "--dry-run",
                    "--report",
                    tmp_path,
                    "-r",
                    self.requirements_file,
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                # 解析pip输出中的冲突信息
                current_conflict: Optional[Dict[str, Any]] = None
                for line in result.stderr.split("\n"):
                    if "requires" in line and "but" in line:
                        if current_conflict:
                            conflicts.append(current_conflict)
                        current_conflict = {
                            "type": "version_conflict",
                            "description": line.strip(),
                            "details": [],
                        }
                    elif current_conflict and line.strip():
                        current_conflict["details"].append(line)

                    # 冲突结束,保存
                    elif current_conflict and line.startswith("To fix this"):
                        conflicts.append(current_conflict)
                        current_conflict = None

            Path(tmp_path).unlink(missing_ok=True)

        except subprocess.TimeoutExpired:
            print("⚠️ pip检测超时,使用已知冲突模式检测")
        except Exception as e:
            print(f"⚠️ pip检测失败: {e}")

        return conflicts

    def detect_known_conflicts(self) -> List[Dict[str, Any]]:
        """检测已知的依赖冲突模式"""
        conflicts = []
        requirements = self.get_requirements_dict()

        for package, conflict_info in self.known_conflicts.items():
            if package in requirements:
                current_spec = requirements[package]
                suggested_spec = conflict_info["solution"]

                if current_spec != suggested_spec:
                    conflicts.append(
                        {
                            "type": "known_conflict",
                            "package": package,
                            "current": current_spec,
                            "suggested": suggested_spec,
                            "description": conflict_info["description"],
                            "solution": (
                                f"sed -i 's/{package}{current_spec}/"
                                f"{suggested_spec}/g' {self.requirements_file}"
                            ),
                        }
                    )

        return conflicts

    def generate_solutions(
        self, conflicts: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """为冲突生成解决方案"""
        solutions = []

        for conflict in conflicts:
            if conflict["type"] == "known_conflict":
                # 生成sed命令来修复
                package = conflict["package"]
                current = conflict["current"]
                suggested = conflict["suggested"]

                # 转义特殊字符
                current_esc = current.replace("/", r"\/").replace(".", r"\.")
                suggested_esc = suggested.replace("/", r"\/")

                cmd = (
                    f"sed -i 's/{package}{current_esc}/"
                    f"{suggested_esc}/g' {self.requirements_file}"
                )
                solutions.append(
                    {
                        "type": "sed_fix",
                        "package": package,
                        "description": (f"修复 {package}: {current} -> {suggested}"),
                        "command": cmd,
                    }
                )

        return solutions

    def apply_solutions(self, solutions: List[Dict[str, str]]) -> bool:
        """应用解决方案"""
        print("\n🔧 应用修复方案...")

        for solution in solutions:
            print(f"   {solution['description']}")
            try:
                # 执行修复命令  # nosec B602
                result = subprocess.run(  # nosec B602
                    solution["command"], shell=True, capture_output=True, text=True
                )

                if result.returncode == 0:
                    print(f"   ✅ {solution['package']} 修复成功")
                else:
                    print(f"   ❌ {solution['package']} 修复失败: {result.stderr}")
                    return False

            except Exception as e:
                print(f"   ❌ 执行修复失败: {e}")
                return False

        return True

    def validate_fix(self) -> bool:
        """验证修复是否成功"""
        print("\n🔍 验证修复效果...")
        try:
            # 尝试解析依赖
            result = subprocess.run(  # nosec B603 B607
                ["pip", "install", "--dry-run", "-r", self.requirements_file],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                print("🎉 所有依赖冲突已解决!")
                return True
            else:
                print(f"❌ 仍有依赖问题:\n{result.stderr}")
                return False

        except Exception as e:
            print(f"❌ 验证失败: {e}")
            return False

    def run_detection_and_fix(self) -> bool:
        """运行完整的检测和修复流程"""
        print(f"📁 检查文件: {self.requirements_file}")

        # 1. 检测已知冲突
        print("\n🔍 检测已知依赖冲突...")
        known_conflicts = self.detect_known_conflicts()

        if known_conflicts:
            print(f"发现 {len(known_conflicts)} 个已知冲突:")
            for conflict in known_conflicts:
                print(f"  • {conflict['package']}: {conflict['description']}")

            # 2. 生成解决方案
            solutions = self.generate_solutions(known_conflicts)

            # 3. 应用修复
            if self.apply_solutions(solutions):
                # 4. 验证修复
                if self.validate_fix():
                    print("\n🎉 依赖冲突全部解决!可以安全推送代码。")
                    return True
                else:
                    print("\n⚠️ 修复后仍有问题,需要手动检查。")
                    return False
            else:
                print("\n❌ 修复应用失败")
                return False
        else:
            print("✅ 未发现已知依赖冲突")
            return True


def main() -> None:
    """主函数"""
    print_banner()

    if len(sys.argv) > 1:
        requirements_file = sys.argv[1]
    else:
        requirements_file = "requirements.txt"

    detector = DependencyConflictDetector(requirements_file)

    if detector.run_detection_and_fix():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
