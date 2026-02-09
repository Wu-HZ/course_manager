#!/usr/bin/env python3
"""
排课系统便携包打包脚本
"""

import os
import sys
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

# 配置
PYTHON_VERSION = "3.11.9"
PYTHON_EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

def main():
    print("=" * 50)
    print("       排课系统便携包打包工具")
    print("=" * 50)
    print()

    # 获取项目根目录
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    os.chdir(project_dir)

    output_dir = project_dir / "portable_build"
    portable_dir = output_dir / "排课系统"

    # 清理旧目录
    if output_dir.exists():
        print("[清理] 删除旧的构建目录...")
        shutil.rmtree(output_dir)

    # 创建目录
    (portable_dir / "python").mkdir(parents=True)
    (portable_dir / "data").mkdir(parents=True)

    # 1. 下载 Python
    print("\n[1/6] 下载 Python 嵌入式版本...")
    python_zip = output_dir / "python-embed.zip"
    urllib.request.urlretrieve(PYTHON_EMBED_URL, python_zip)
    print(f"       已下载: {python_zip}")

    # 2. 解压 Python
    print("\n[2/6] 解压 Python...")
    with zipfile.ZipFile(python_zip, 'r') as zf:
        zf.extractall(portable_dir / "python")

    # 配置 ._pth 文件以支持 pip
    print("       配置 pip 支持...")
    pth_file = portable_dir / "python" / "python311._pth"
    pth_file.write_text("python311.zip\n.\nLib\\site-packages\nimport site\n", encoding='utf-8')

    # 3. 安装 pip
    print("\n[3/6] 安装 pip...")
    get_pip_path = portable_dir / "python" / "get-pip.py"
    urllib.request.urlretrieve(GET_PIP_URL, get_pip_path)

    python_exe = portable_dir / "python" / "python.exe"
    subprocess.run([str(python_exe), str(get_pip_path), "--no-warn-script-location"], check=True)
    get_pip_path.unlink()

    # 4. 安装依赖
    print("\n[4/6] 安装 Python 依赖...")
    requirements = project_dir / "backend" / "requirements.txt"
    subprocess.run([
        str(python_exe), "-m", "pip", "install",
        "--no-warn-script-location", "-r", str(requirements)
    ], check=True)

    # 5. 构建前端
    print("\n[5/6] 构建前端...")
    frontend_dir = project_dir / "frontend"
    subprocess.run(["npm", "install"], cwd=frontend_dir, shell=True, check=True)
    subprocess.run(["npm", "run", "build"], cwd=frontend_dir, shell=True, check=True)

    # 6. 复制文件
    print("\n[6/6] 复制文件...")

    # 复制后端
    shutil.copytree(
        project_dir / "backend",
        portable_dir / "backend",
        ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'db.sqlite3', 'staticfiles')
    )

    # 复制前端构建
    shutil.copytree(frontend_dir / "dist", portable_dir / "frontend" / "dist")

    # 复制启动脚本
    shutil.copy(script_dir / "启动.bat", portable_dir)
    shutil.copy(script_dir / "停止.bat", portable_dir)
    shutil.copy(script_dir / "使用说明.txt", portable_dir)

    # 创建 ZIP
    print("\n[打包] 创建 ZIP 压缩包...")
    zip_path = output_dir / "排课系统.zip"
    shutil.make_archive(str(output_dir / "排课系统"), 'zip', output_dir, "排课系统")

    # 清理临时文件
    python_zip.unlink()

    # 计算大小
    zip_size = zip_path.stat().st_size / (1024 * 1024)
    folder_size = sum(f.stat().st_size for f in portable_dir.rglob('*') if f.is_file()) / (1024 * 1024)

    print()
    print("=" * 50)
    print(" 打包完成！")
    print(f" 输出目录: {output_dir}")
    print(f" - 排课系统/     ({folder_size:.1f} MB)")
    print(f" - 排课系统.zip  ({zip_size:.1f} MB)")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[错误] {e}")
        sys.exit(1)
