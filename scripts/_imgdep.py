# -*- coding: utf-8 -*-
"""读图脚本的依赖引导：保证 numpy / Pillow 在场，否则换一个装了它们的解释器重跑。

为什么需要它
------------
本仓库的数据类闸门（verify_data / check_site / check_urls）只用标准库，默认的
`python` 就能跑。但读图脚本要用 numpy + Pillow 解析 600 dpi 页面图。默认解释器
（WorkBuddy 隔离运行时）里没有这两个包，直接 `python scripts/verify_calibration.py`
会以 ModuleNotFoundError 退出——看起来像"标定没过"，其实是环境问题，会误导判读。

做法
----
1. 当前解释器已装 numpy + Pillow → 什么都不做。
2. 没装 → 依次尝试 $APOCA_IMG_PY、以及本机已知装了这两个包的解释器，用子进程把同一个
   脚本连同原参数重跑一遍，输出直通终端、退出码原样回传。
3. 都找不到 → 打印确切的安装命令并以退出码 2 中止（不是 1：把环境问题与"标定偏差"
   区分开，闸门判读时不会混淆）。

这不改变任何读数逻辑；换解释器只是换运行环境。
"""
from __future__ import annotations

import os
import subprocess
import sys

# 只在"当前解释器缺包"时才用到；可用环境变量覆盖。
_CANDIDATES = (
    os.environ.get("APOCA_IMG_PY", ""),
    r"C:\Users\lin\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe",
)


def _has(path: str) -> bool:
    if not path or not os.path.exists(path):
        return False
    # 用 subprocess 而不是 os.spawnv：Windows 上 spawnv 用空格拼参数，
    # "-c import numpy, PIL" 会被拆成三段（SyntaxError: invalid syntax），假阴性。
    r = subprocess.run([path, "-c", "import numpy, PIL"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0


def ensure() -> None:
    try:
        import numpy  # noqa: F401
        import PIL  # noqa: F401

        return
    except ModuleNotFoundError:
        pass

    script = str(os.path.abspath(sys.argv[0]))
    for cand in _CANDIDATES:
        if os.path.normcase(cand) == os.path.normcase(sys.executable):
            continue
        if _has(cand):
            sys.stderr.write(f"[imgdep] {os.path.basename(sys.executable)} 缺 numpy/Pillow，"
                             f"改用 {cand}\n")
            sys.stderr.flush()
            # 用子进程而不是 os.execv：Windows 上 execv 换成新进程后，父进程的输出
            # 与退出码传递都不可靠（实测：负例应该 exit 1，实际 exit 0 且无输出）。
            # 子进程原样继承 stdout/stderr 与参数，退出码逐字回传。
            raise SystemExit(subprocess.call([cand, script] + sys.argv[1:]))

    sys.exit(
        "缺 numpy / Pillow，且没找到可用的替代解释器。\n"
        "装到隔离 venv 后再跑：\n"
        r"  C:\Users\lin\.workbuddy\binaries\python\versions\3.13.12\python.exe -m venv "
        r"C:\Users\lin\.workbuddy\binaries\python\envs\default" "\n"
        r"  <venv>\Scripts\pip install numpy pillow" "\n"
        "或用 APOCA_IMG_PY=<装了 numpy+pillow 的 python.exe> 指定解释器。"
    )
