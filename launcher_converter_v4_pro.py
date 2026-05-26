import ctypes
import os
import shutil
import subprocess
import sys


def show_error(message: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(0, message, "启动失败", 0x10)
    except Exception:
        pass


def find_python_executable(base_dir: str) -> str | None:
    candidates = [
        os.path.join(base_dir, "pythonw.exe"),
        os.path.join(base_dir, "python.exe"),
        r"D:\anaconda3\pythonw.exe",
        r"D:\anaconda3\python.exe",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path

    for cmd in ("pythonw", "python"):
        found = shutil.which(cmd)
        if found:
            return found
    return None


def main() -> None:
    base_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
    target_script = os.path.join(base_dir, "converter_v4_pro.py")

    if not os.path.isfile(target_script):
        show_error(f"未找到脚本文件:\n{target_script}")
        return

    python_exe = find_python_executable(base_dir)
    if not python_exe:
        show_error("未找到 Python 解释器。\n请安装 Python，或把 pythonw.exe 放到同目录。")
        return

    try:
        subprocess.Popen([python_exe, target_script], cwd=base_dir)
    except Exception as exc:
        show_error(f"启动失败:\n{exc}")


if __name__ == "__main__":
    main()
