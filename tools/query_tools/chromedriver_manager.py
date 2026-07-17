# -*- coding: utf-8 -*-
"""ChromeDriver 下载与更新管理 - 华为云镜像

容器环境中优先使用系统预装的 chromium-driver（/usr/bin/chromedriver），
仅在系统无 chromedriver 时才从华为云下载。
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

# 华为云镜像
HUAWEI_INDEX_URL = "https://repo.huaweicloud.com/chromedriver/.index.json"
HUAWEI_DOWNLOAD_TEMPLATE = "https://repo.huaweicloud.com/chromedriver/{version}/chromedriver-linux64.zip"

DRIVER_DIR = Path("/app/chromedriver")
DRIVER_PATH = DRIVER_DIR / "chromedriver"


def _run(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return (r.stdout or r.stderr).strip()
    except Exception:
        return ""


def detect_chrome_version() -> str:
    """检测本机 Chrome/Chromium 版本"""
    for cmd in [
        ["google-chrome", "--version"],
        ["google-chrome-stable", "--version"],
        ["chromium", "--version"],
        ["chromium-browser", "--version"],
    ]:
        m = re.search(r"(\d+\.\d+\.\d+\.\d+)", _run(cmd))
        if m:
            return m.group(1)
    return ""


def find_system_chromedriver() -> str:
    """查找系统预装的 chromedriver（apt install chromium-driver 安装的）"""
    for p in ["/usr/bin/chromedriver", "/usr/local/bin/chromedriver"]:
        if Path(p).exists():
            return p
    which = shutil.which("chromedriver")
    if which:
        return which
    return ""


def get_local_version() -> str:
    """获取本地 ChromeDriver 版本"""
    path = str(DRIVER_PATH) if DRIVER_PATH.exists() else find_system_chromedriver()
    if not path:
        return ""
    m = re.search(r"ChromeDriver\s+(\d+\.\d+\.\d+\.\d+)", _run([path, "--version"]))
    return m.group(1) if m else ""


def get_best_version_from_huawei(chrome_version: str) -> str:
    """从华为云索引获取最佳 ChromeDriver 版本"""
    if not chrome_version:
        return ""
    chrome_major = chrome_version.split(".")[0]
    try:
        print("正在读取华为云索引...")
        req = Request(HUAWEI_INDEX_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        index = data.get("chromedriver", {})
        available = []
        for ver, info in index.items():
            files = info.get("files", []) if isinstance(info, dict) else []
            if any("chromedriver-linux64.zip" in str(f) for f in files):
                available.append(ver)
        if not available:
            return ""
        same_major = [v for v in available if v.startswith(chrome_major + ".")]
        key = lambda v: [int(p) for p in re.sub(r"[^0-9.]", "", v).split(".") if p.isdigit()]
        return max(same_major or available, key=key)
    except Exception as e:
        print(f"读取华为云索引失败: {e}")
        return ""


def download_chromedriver(version: str) -> bool:
    """从华为云下载 ChromeDriver"""
    if not version:
        return False
    url = HUAWEI_DOWNLOAD_TEMPLATE.format(version=version)
    print(f"下载 ChromeDriver {version}...\nURL: {url}")
    DRIVER_DIR.mkdir(parents=True, exist_ok=True)
    tmp_dir = Path(tempfile.mkdtemp(prefix="chromedriver_"))
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=120) as resp:
            data = resp.read()
        if not data:
            print("下载内容为空")
            return False
        print(f"下载完成，大小: {len(data) / 1024 / 1024:.2f} MB")
        zip_path = tmp_dir / "chromedriver.zip"
        zip_path.write_bytes(data)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(tmp_dir)
        chromedriver_files = list(tmp_dir.rglob("chromedriver"))
        if not chromedriver_files:
            print("压缩包中未找到 chromedriver")
            return False
        shutil.copy2(chromedriver_files[0], DRIVER_PATH)
        DRIVER_PATH.chmod(0o755)
        print(f"ChromeDriver 已安装到: {DRIVER_PATH}")
        return True
    except Exception as e:
        print(f"下载失败: {e}")
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def ensure_chromedriver() -> str:
    """确保 ChromeDriver 可用，返回路径。不会抛出异常。"""
    # 1) 系统预装的 chromedriver 优先（apt install chromium-driver）
    system_driver = find_system_chromedriver()
    chrome_ver = detect_chrome_version()

    if system_driver:
        local_ver = get_local_version()
        print(f"Chrome: {chrome_ver or '未检测到'}, 系统 ChromeDriver: {local_ver or system_driver}")
        if chrome_ver and local_ver:
            if local_ver.split(".")[0] == chrome_ver.split(".")[0]:
                print("版本匹配，使用系统 ChromeDriver")
                return system_driver
            # 主版本不匹配，尝试下载
            best = get_best_version_from_huawei(chrome_ver)
            if best and download_chromedriver(best):
                return str(DRIVER_PATH)
        return system_driver

    # 2) 没有系统 chromedriver，尝试自管理
    local_ver = get_local_version()
    if not chrome_ver:
        print("警告: 未检测到 Chrome/Chromium 浏览器")
        if local_ver or DRIVER_PATH.exists():
            print(f"使用现有 ChromeDriver: {DRIVER_PATH}")
            return str(DRIVER_PATH)
        print("提示: 成绩查询功能需要 Chrome/Chromium 浏览器")
        return ""

    print(f"Chrome: {chrome_ver}, 本地 ChromeDriver: {local_ver or '未安装'}")
    best = get_best_version_from_huawei(chrome_ver)
    if not best:
        return str(DRIVER_PATH) if local_ver or DRIVER_PATH.exists() else ""
    print(f"推荐 ChromeDriver: {best}")
    if local_ver and local_ver.split(".")[0] == best.split(".")[0]:
        print("版本匹配，无需更新")
        return str(DRIVER_PATH)
    if download_chromedriver(best):
        return str(DRIVER_PATH)
    return str(DRIVER_PATH) if local_ver or DRIVER_PATH.exists() else ""


if __name__ == "__main__":
    path = ensure_chromedriver()
    if path:
        print(f"\nChromeDriver 路径: {path}")
    else:
        print("\nChromeDriver 不可用，成绩查询功能将无法使用")
