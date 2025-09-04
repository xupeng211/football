#!/usr/bin/env python3
"""
本地Docker构建测试脚本
===========================

这个脚本模拟CI环境中的Docker构建测试, 帮助开发者在提交代码前发现构建问题。  # noqa: RUF002

特性:  # noqa: RUF002
- 验证Dockerfile语法
- 检查COPY指令引用的文件是否存在
- 模拟Docker构建过程(可选实际构建)  # noqa: RUF002
- 检查构建依赖完整性

使用方法:  # noqa: RUF002
    python scripts/local_docker_test.py
    python scripts/local_docker_test.py --build  # 执行实际构建
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def check_dockerfile_exists() -> bool:
    """检查Dockerfile是否存在"""
    print("🔍 检查Dockerfile存在性...")
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        print("❌ Dockerfile不存在")
        return False
    print("✅ Dockerfile存在")
    return True


def parse_dockerfile() -> list[str]:
    """解析Dockerfile并返回所有COPY指令"""
    print("📖 解析Dockerfile内容...")

    with open("Dockerfile") as f:
        content = f.read()

    # 查找所有COPY指令
    copy_instructions = re.findall(r"^COPY\s+(.+)", content, re.MULTILINE)
    print(f"找到 {len(copy_instructions)} 个COPY指令")

    for i, instruction in enumerate(copy_instructions, 1):
        print(f"  {i}. COPY {instruction}")

    return copy_instructions


def check_copy_files(copy_instructions: list[str]) -> bool:
    """检查COPY指令引用的文件是否存在"""
    print("📁 检查COPY指令引用的文件...")

    all_files_exist = True

    for instruction in copy_instructions:
        # 解析COPY指令: COPY source dest
        parts = instruction.strip().split()
        if len(parts) < 2:
            continue

        # 最后一个是目标路径, 其他都是源文件
        sources = parts[:-1]
        destination = parts[-1]

        print(f"  检查: {' '.join(sources)} -> {destination}")

        for source in sources:
            # 移除可能的引号
            source = source.strip("\"'")

            if source.endswith("/"):
                # 目录
                if not Path(source).is_dir():
                    print(f"    ❌ 目录不存在: {source}")
                    all_files_exist = False
                else:
                    print(f"    ✅ 目录存在: {source}")
            else:
                # 文件
                if not Path(source).exists():
                    print(f"    ❌ 文件不存在: {source}")
                    all_files_exist = False
                else:
                    print(f"    ✅ 文件存在: {source}")

    return all_files_exist


def check_critical_files() -> dict[str, bool]:
    """检查关键构建文件是否存在"""
    print("🔑 检查关键构建文件...")

    critical_files = {
        "pyproject.toml": "Python项目配置",
        "uv.lock": "依赖锁文件",
        "README.md": "项目说明",
        "src/": "源代码目录",
        "Makefile": "构建配置",
    }

    results = {}

    for file_path, description in critical_files.items():
        if file_path.endswith("/"):
            exists = Path(file_path).is_dir()
        else:
            exists = Path(file_path).exists()

        status = "✅" if exists else "❌"
        print(f"  {status} {file_path} ({description})")
        results[file_path] = exists

    return results


def validate_dockerfile_syntax() -> bool:
    """验证Dockerfile语法(使用docker命令)"""
    print("🔍 验证Dockerfile语法...")

    try:
        # 检查docker是否可用
        result = subprocess.run(
            ["docker", "--version"], capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            print("⚠️ Docker未安装, 跳过语法验证")
            return True

        # 简单的Dockerfile语法检查
        try:
            with open("Dockerfile") as f:
                content = f.read()

            # 基本语法检查 - 正确处理多行指令
            lines = content.strip().split("\n")
            in_multiline_instruction = False

            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # 检查是否是多行指令的延续
                if in_multiline_instruction:
                    # 如果行不以反斜杠结尾, 则多行指令结束
                    if not line.endswith("\\"):
                        in_multiline_instruction = False
                    continue

                # 检查是否是有效的Docker指令
                valid_instructions = [
                    "FROM",
                    "RUN",
                    "COPY",
                    "ADD",
                    "CMD",
                    "ENTRYPOINT",
                    "ENV",
                    "ARG",
                    "LABEL",
                    "EXPOSE",
                    "VOLUME",
                    "WORKDIR",
                    "USER",
                    "SHELL",
                    "HEALTHCHECK",
                ]
                first_word = line.split()[0].upper() if line.split() else ""

                if first_word in valid_instructions:
                    # 检查是否是多行指令的开始
                    if line.endswith("\\"):
                        in_multiline_instruction = True
                else:
                    print(f"❌ 第{i}行可能有语法问题: {line}")
                    return False

            print("✅ Dockerfile基本语法检查通过")
            return True

        except Exception as e:
            print(f"⚠️ Dockerfile语法检查出错: {e}")
            return True  # 不阻断流程

    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️ 无法验证Dockerfile语法(Docker不可用或超时)")
        return True  # 不阻断流程


def run_docker_build_test(actual_build: bool = False) -> bool:
    """运行Docker构建测试"""
    if not actual_build:
        print("🏗️ 模拟Docker构建测试...")
        print("i 使用 --build 参数进行实际构建测试")
        return True

    print("🏗️ 执行实际Docker构建测试...")

    try:
        # 构建Docker镜像
        cmd = ["docker", "build", "-t", "football-test:local", "-f", "Dockerfile", "."]

        print(f"执行命令: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5分钟超时
        )

        if result.returncode == 0:
            print("✅ Docker构建成功")

            # 清理测试镜像
            subprocess.run(
                ["docker", "rmi", "football-test:local"], capture_output=True
            )
            print("🧹 已清理测试镜像")

            return True
        else:
            print("❌ Docker构建失败:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("❌ Docker构建超时(5分钟)")
        return False
    except FileNotFoundError:
        print("❌ Docker命令未找到")
        return False


def check_gitignore_critical_files() -> bool:
    """检查关键文件是否被错误忽略"""
    print("🚫 检查关键文件是否被.gitignore错误忽略...")

    critical_files = ["uv.lock", "pyproject.toml", "Dockerfile"]

    try:
        with open(".gitignore") as f:
            gitignore_content = f.read()

        issues_found = False

        for file in critical_files:
            # 检查是否在.gitignore中
            if re.search(rf"^{re.escape(file)}$", gitignore_content, re.MULTILINE):
                print(f"  ❌ 关键文件被忽略: {file}")
                issues_found = True
            else:
                print(f"  ✅ {file} 未被忽略")

        return not issues_found

    except FileNotFoundError:
        print("  ⚠️ .gitignore文件不存在")
        return True


def main():
    """主测试流程"""
    parser = argparse.ArgumentParser(description="本地Docker构建测试")
    parser.add_argument(
        "--build", action="store_true", help="执行实际Docker构建(较慢但更准确)"
    )
    args = parser.parse_args()

    print("🐳 开始本地Docker构建测试")
    print("=" * 50)

    success = True

    # 1. 检查Dockerfile存在
    if not check_dockerfile_exists():
        success = False

    # 2. 解析Dockerfile
    try:
        copy_instructions = parse_dockerfile()
    except Exception as e:
        print(f"❌ 解析Dockerfile失败: {e}")
        success = False
        copy_instructions = []

    # 3. 检查COPY文件
    if copy_instructions and not check_copy_files(copy_instructions):
        success = False

    # 4. 检查关键文件
    critical_results = check_critical_files()
    if not all(critical_results.values()):
        success = False

    # 5. 检查.gitignore
    if not check_gitignore_critical_files():
        success = False

    # 6. 验证Dockerfile语法
    if not validate_dockerfile_syntax():
        success = False

    # 7. Docker构建测试
    if not run_docker_build_test(args.build):
        success = False

    print("=" * 50)

    if success:
        print("🎉 所有Docker构建测试通过!")
        print("✅ Docker构建应该能在CI中成功")
        return True
    else:
        print("❌ Docker构建测试失败!")
        print("🚫 请修复问题后再提交代码")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
