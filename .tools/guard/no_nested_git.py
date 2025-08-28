#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# 允许名单通过环境变量 ALLOW_NESTED_GIT 指定
ALLOW = (
    set(os.getenv("ALLOW_NESTED_GIT", "").split(","))
    if os.getenv("ALLOW_NESTED_GIT")
    else set()
)
ROOT = Path(".").resolve()

bad = []
for d, subdirs, _files in os.walk(ROOT):
    d_path = Path(d)
    if d_path.name == ".git":
        # 找到 .git 的父目录
        repo_dir = d_path.parent
        # 跳过仓库根目录的 .git
        if repo_dir == ROOT:
            continue
        # 其余视为嵌套仓库
        rel = repo_dir.relative_to(ROOT)
        # 允许名单(如 external/ 某些特例)可以通过 ALLOW_NESTED_GIT 指定
        if str(rel) not in ALLOW:
            bad.append(str(rel))
        # 不再深搜该路径
        subdirs[:] = []
# 输出结果
if bad:
    print("❌ Nested Git repositories detected:")
    for p in bad:
        print(" -", p)
    print(
        "提示: 请移除或改为 submodule/subtree, 并避免放在 src/ 目录; "
        "或在 ALLOW_NESTED_GIT 中显式豁免。"
    )
    sys.exit(2)
else:
    print("✅ No nested Git repositories.")
