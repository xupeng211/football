#!/usr/bin/env python3
"""
🎯 脚手架模块管理器
功能：智能模块安装、卸载、升级和依赖解析
版本：v2.0.0
"""

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml


@dataclass
class ModuleInfo:
    """模块信息数据类"""

    name: str
    display_name: str
    version: str
    description: str
    type: str
    required: bool
    dependencies: List[str]
    conflicts: List[str]
    files: List[Dict]
    post_install: Dict
    requirements: Dict
    features: List[str]
    metrics: Dict


class ModuleManager:
    """智能模块管理器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.modules_dir = self.project_root / "scaffold-modules"
        self.packages_dir = self.modules_dir / "packages"
        self.installed_modules_file = self.project_root / ".scaffold-modules.json"

        # 确保目录存在
        self.modules_dir.mkdir(exist_ok=True)
        self.packages_dir.mkdir(exist_ok=True)

        # 加载已安装模块信息
        self.installed_modules = self._load_installed_modules()

    def _load_installed_modules(self) -> Dict:
        """加载已安装模块信息"""
        if self.installed_modules_file.exists():
            with open(self.installed_modules_file, encoding="utf-8") as f:
                return json.load(f)
        return {"modules": {}, "install_history": [], "last_update": None}

    def _save_installed_modules(self) -> None:
        """保存已安装模块信息"""
        self.installed_modules["last_update"] = datetime.now().isoformat()
        with open(self.installed_modules_file, "w", encoding="utf-8") as f:
            json.dump(self.installed_modules, f, indent=2, ensure_ascii=False)

    def _load_module_config(self, module_name: str) -> Optional[ModuleInfo]:
        """加载模块配置"""
        config_file = self.packages_dir / module_name / "module.yaml"
        if not config_file.exists():
            return None

        with open(config_file, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return ModuleInfo(
            name=config["name"],
            display_name=config["display_name"],
            version=config["version"],
            description=config["description"],
            type=config["type"],
            required=config.get("required", False),
            dependencies=config.get("dependencies", []),
            conflicts=config.get("conflicts", []),
            files=config.get("files", []),
            post_install=config.get("post_install", {}),
            requirements=config.get("requirements", {}),
            features=config.get("features", []),
            metrics=config.get("metrics", {}),
        )

    def list_available_modules(self) -> List[ModuleInfo]:
        """列出所有可用模块"""
        modules = []
        for module_dir in self.packages_dir.iterdir():
            if module_dir.is_dir():
                module_info = self._load_module_config(module_dir.name)
                if module_info:
                    modules.append(module_info)
        return modules

    def list_installed_modules(self) -> List[str]:
        """列出已安装模块"""
        return list(self.installed_modules["modules"].keys())

    def resolve_dependencies(self, modules: List[str]) -> Tuple[List[str], List[str]]:
        """
        解析模块依赖关系
        返回：(安装顺序的模块列表, 冲突列表)
        """
        # 收集所有需要的模块（包括依赖）
        all_modules = set()
        conflicts = []

        def add_module_and_deps(module_name: str):
            if module_name in all_modules:
                return

            module_info = self._load_module_config(module_name)
            if not module_info:
                raise ValueError(f"模块 {module_name} 不存在")

            # 检查冲突
            for conflict in module_info.conflicts:
                if conflict in all_modules:
                    conflicts.append(f"{module_name} 与 {conflict} 冲突")

            # 添加当前模块
            all_modules.add(module_name)

            # 递归添加依赖
            for dep in module_info.dependencies:
                add_module_and_deps(dep)

        # 处理所有请求的模块
        for module in modules:
            add_module_and_deps(module)

        # 按依赖关系排序
        ordered_modules = self._topological_sort(list(all_modules))

        return ordered_modules, conflicts

    def _topological_sort(self, modules: List[str]) -> List[str]:
        """拓扑排序模块依赖"""
        # 构建依赖图
        graph = {}
        in_degree = {}

        for module in modules:
            module_info = self._load_module_config(module)
            graph[module] = module_info.dependencies if module_info else []
            in_degree[module] = 0

        # 计算入度
        for module in modules:
            for dep in graph[module]:
                if dep in in_degree:
                    in_degree[dep] += 1

        # 拓扑排序
        queue = [m for m in modules if in_degree[m] == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for neighbor in graph[current]:
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return result

    def install_module(self, module_name: str, force: bool = False) -> bool:
        """安装单个模块"""
        # 检查模块是否已安装
        if module_name in self.installed_modules["modules"] and not force:
            print(f"✅ 模块 {module_name} 已安装")
            return True

        # 加载模块配置
        module_info = self._load_module_config(module_name)
        if not module_info:
            print(f"❌ 模块 {module_name} 不存在")
            return False

        print(f"📦 正在安装模块: {module_info.display_name}")

        try:
            # 复制模块文件
            self._copy_module_files(module_info)

            # 执行安装后命令
            self._execute_post_install(module_info)

            # 记录安装信息
            self.installed_modules["modules"][module_name] = {
                "version": module_info.version,
                "install_date": datetime.now().isoformat(),
                "files": [f["dest"] for f in module_info.files],
            }

            # 添加到安装历史
            self.installed_modules["install_history"].append(
                {
                    "module": module_name,
                    "version": module_info.version,
                    "action": "install",
                    "timestamp": datetime.now().isoformat(),
                }
            )

            self._save_installed_modules()

            print(f"✅ 模块 {module_info.display_name} 安装完成")

            # 显示安装后消息
            for message in module_info.post_install.get("messages", []):
                print(f"💡 {message}")

            return True

        except Exception as e:
            print(f"❌ 安装模块 {module_name} 失败: {e!s}")
            return False

    def _copy_module_files(self, module_info: ModuleInfo):
        """复制模块文件"""
        module_source_dir = self.packages_dir / module_info.name

        for file_info in module_info.files:
            src_path = module_source_dir / file_info["src"]
            dest_path = self.project_root / file_info["dest"]

            # 确保目标目录存在
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            if src_path.exists():
                if src_path.is_file():
                    shutil.copy2(src_path, dest_path)
                else:
                    shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
                print(f"  📄 {file_info['dest']}")
            else:
                # 如果源文件不存在，尝试从项目根目录复制现有文件
                existing_file = self.project_root / file_info["src"]
                if existing_file.exists():
                    if existing_file.is_file():
                        shutil.copy2(existing_file, dest_path)
                    else:
                        shutil.copytree(existing_file, dest_path, dirs_exist_ok=True)
                    print(f"  📄 {file_info['dest']} (从现有文件)")
                else:
                    print(f"  ⚠️  源文件不存在: {file_info['src']}")

    def _execute_post_install(self, module_info: ModuleInfo):
        """执行安装后命令"""
        commands = module_info.post_install.get("commands", [])
        for cmd in commands:
            try:
                print(f"  🔧 执行: {cmd}")
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    print(f"  ⚠️  命令警告: {cmd}")
                    print(f"      {result.stderr}")
            except Exception as e:
                print(f"  ⚠️  命令执行失败: {cmd} - {e!s}")

    def install_modules(self, modules: List[str], force: bool = False) -> bool:
        """安装多个模块（处理依赖关系）"""
        print(f"🎯 开始安装模块: {', '.join(modules)}")

        # 解析依赖关系
        try:
            ordered_modules, conflicts = self.resolve_dependencies(modules)
        except Exception as e:
            print(f"❌ 依赖解析失败: {e!s}")
            return False

        # 检查冲突
        if conflicts:
            print("❌ 发现模块冲突:")
            for conflict in conflicts:
                print(f"  - {conflict}")
            return False

        print(f"📋 安装顺序: {' → '.join(ordered_modules)}")

        # 按顺序安装模块
        for module_name in ordered_modules:
            if not self.install_module(module_name, force):
                print("❌ 安装失败，回滚操作...")
                self._rollback_installation(
                    ordered_modules[: ordered_modules.index(module_name)]
                )
                return False

        print("🎉 所有模块安装完成！")
        return True

    def _rollback_installation(self, installed_modules: List[str]):
        """回滚安装"""
        print("🔄 正在回滚安装...")
        for module_name in reversed(installed_modules):
            self.uninstall_module(module_name, silent=True)

    def uninstall_module(self, module_name: str, silent: bool = False) -> bool:
        """卸载模块"""
        if module_name not in self.installed_modules["modules"]:
            if not silent:
                print(f"⚠️  模块 {module_name} 未安装")
            return True

        if not silent:
            print(f"🗑️  正在卸载模块: {module_name}")

        try:
            # 删除模块文件
            module_files = self.installed_modules["modules"][module_name]["files"]
            for file_path in module_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    if full_path.is_file():
                        full_path.unlink()
                    else:
                        shutil.rmtree(full_path)
                    if not silent:
                        print(f"  🗑️  {file_path}")

            # 从已安装模块中移除
            del self.installed_modules["modules"][module_name]

            # 添加到卸载历史
            self.installed_modules["install_history"].append(
                {
                    "module": module_name,
                    "action": "uninstall",
                    "timestamp": datetime.now().isoformat(),
                }
            )

            self._save_installed_modules()

            if not silent:
                print(f"✅ 模块 {module_name} 卸载完成")

            return True

        except Exception as e:
            if not silent:
                print(f"❌ 卸载模块 {module_name} 失败: {e!s}")
            return False

    def check_updates(self) -> List[str]:
        """检查可更新的模块"""
        updatable = []
        for module_name in self.installed_modules["modules"]:
            module_info = self._load_module_config(module_name)
            if module_info:
                installed_version = self.installed_modules["modules"][module_name][
                    "version"
                ]
                if module_info.version != installed_version:
                    updatable.append(module_name)
        return updatable

    def get_module_status(self) -> Dict:
        """获取模块状态统计"""
        available = self.list_available_modules()
        installed = self.list_installed_modules()
        updatable = self.check_updates()

        return {
            "available_count": len(available),
            "installed_count": len(installed),
            "updatable_count": len(updatable),
            "available_modules": [m.name for m in available],
            "installed_modules": installed,
            "updatable_modules": updatable,
        }


def main():
    """命令行接口"""
    if len(sys.argv) < 2:
        print("Usage: python module-manager.py <command> [args...]")
        print("Commands: list, install, uninstall, status, update")
        return

    manager = ModuleManager(os.getcwd())
    command = sys.argv[1]

    if command == "list":
        modules = manager.list_available_modules()
        print("📦 可用模块:")
        for module in modules:
            status = (
                "✅ 已安装" if module.name in manager.list_installed_modules() else ""
            )
            print(f"  {module.display_name} (v{module.version}) {status}")
            print(f"    {module.description}")

    elif command == "install":
        if len(sys.argv) < 3:
            print("Usage: python module-manager.py install <module1> [module2] ...")
            return
        modules = sys.argv[2:]
        manager.install_modules(modules)

    elif command == "uninstall":
        if len(sys.argv) < 3:
            print("Usage: python module-manager.py uninstall <module>")
            return
        module = sys.argv[2]
        manager.uninstall_module(module)

    elif command == "status":
        status = manager.get_module_status()
        print("📊 模块状态:")
        print(f"  可用模块: {status['available_count']}")
        print(f"  已安装模块: {status['installed_count']}")
        print(f"  可更新模块: {status['updatable_count']}")

    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
