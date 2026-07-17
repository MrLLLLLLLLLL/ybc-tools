# -*- coding: utf-8 -*-
"""ChromeDriver 下载与更新管理 - 华为云镜像"""

import json
import os
import re
import shutil
import zipfile
import tempfile
import subprocess
from pathlib import Path
from urllib.request import urlopen, Request

# 华为云镜像
HUAWEI_INDEX_URL = "https://repo.huaweicloud.com/chromedriver/.index.json"
HUAWEI_DOWNLOAD_TEMPLATE = "https://repo.huaweicloud.com/chromedriver/{version}/chromedriver-linux64.zip"

DRIVER_DIR = Path("/app/chromedriver")
DRIVER_PATH = DRIVER_DIR / "chromedriver"


def detect_chrome_version() -> str:
    """检测本机 Chrome 版本"""
    commands = [
        ["google-chrome", "--version"],
        ["google-chrome-stable", "--version"],
        ["chromium", "--version"],
        ["chromium-browser", "--version"],
    ]
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            output = (result.stdout or result.stderr).strip()
            match = re.search(r"(\d+\.\d+\.\d+\.\d+)", output)
            if match:
                return match.group(1)
        except Exception:
            continue
    return ""


def get_local_version() -> str:
    """获取本地 ChromeDriver 版本"""
    if not DRIVER_PATH.exists():
        return ""
    try:
        result = subprocess.run(
            [str(DRIVER_PATH), "--version"],
            capture_output=True, text=True, timeout=10
        )
        output = (result.stdout or result.stderr).strip()
        match = re.search(r"ChromeDriver\s+(\d+\.\d+\.\d+\.\d+)", output)
        return match.group(1) if match else ""
    except Exception:
        return ""


def get_best_version_from_huawei(chrome_version: str) -> str:
    """从华为云索引获取最佳 ChromeDriver 版本"""
    if not chrome_version:
        return ""
    
    chrome_major = chrome_version.split(".")[0]
    
    try:
        print(f"正在读取华为云索引...")
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
        
        # 匹配同主版本
        same_major = [v for v in available if v.startswith(chrome_major + ".")]
        if same_major:
            def version_key(v):
                parts = re.sub(r"[^0-9.]", "", v).split(".")
                return [int(p) for p in parts if p.isdigit()]
            return max(same_major, key=version_key)
        
        def version_key(v):
            parts = re.sub(r"[^0-9.]", "", v).split(".")
            return [int(p) for p in parts if p.isdigit()]
        return max(available, key=version_key)
        
    except Exception as e:
        print(f"读取华为云索引失败: {e}")
        return ""


def download_chromedriver(version: str) -> bool:
    """从华为云下载 ChromeDriver"""
    if not version:
        return False
    
    url = HUAWEI_DOWNLOAD_TEMPLATE.format(version=version)
    print(f"下载 ChromeDriver {version}...")
    print(f"URL: {url}")
    
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
        
        source = chromedriver_files[0]
        shutil.copy2(source, DRIVER_PATH)
        DRIVER_PATH.chmod(0o755)
        
        print(f"ChromeDriver 已安装到: {DRIVER_PATH}")
        return True
        
    except Exception as e:
        print(f"下载失败: {e}")
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def ensure_chromedriver() -> str:
    """确保 ChromeDriver 可用，返回路径"""
    local_ver = get_local_version()
    chrome_ver = detect_chrome_version()
    
    if not chrome_ver:
        print("警告: 未检测到 Chrome 浏览器")
        if local_ver:
            print(f"使用现有 ChromeDriver: {local_ver}")
            return str(DRIVER_PATH)
        print("提示: 华数华大成绩查询功能需要 Chrome 浏览器")
        return ""
    
    print(f"Chrome 版本: {chrome_ver}")
    print(f"本地 ChromeDriver: {local_ver or '未安装'}")
    
    best_ver = get_best_version_from_huawei(chrome_ver)
    if not best_ver:
        if local_ver:
            print("无法获取推荐版本，使用现有版本")
            return str(DRIVER_PATH)
        return ""
    
    print(f"推荐 ChromeDriver: {best_ver}")
    
    if local_ver:
        local_major = local_ver.split(".")[0]
        best_major = best_ver.split(".")[0]
        if local_major == best_major:
            print("版本匹配，无需更新")
            return str(DRIVER_PATH)
    
    if download_chromedriver(best_ver):
        return str(DRIVER_PATH)
    
    if local_ver:
        print("下载失败，使用现有版本")
        return str(DRIVER_PATH)
    
    return ""


if __name__ == "__main__":
    path = ensure_chromedriver()
    if path:
        print(f"\nChromeDriver 路径: {path}")
    else:
        print("\nChromeDriver 不可用，华数华大查询功能将无法使用")
