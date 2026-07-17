#!/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

APP_DIR="/opt/ybc-tools"
VENV="$APP_DIR/.venv"
PYTHON="/usr/local/bin/python3.12"

cd "$APP_DIR"

# Git pull
info "拉取最新代码..."
git pull origin main

# Check Python 3.12
if [ ! -f "$PYTHON" ]; then
    error "未找到 $PYTHON，请先安装 Python 3.12"
fi
info "Python: $($PYTHON --version)"

# Install Chrome and dependencies for headless mode
if ! command -v google-chrome &>/dev/null && ! command -v google-chrome-stable &>/dev/null; then
    info "安装 Google Chrome 及无头模式依赖..."
    
    if command -v yum &>/dev/null; then
        # CentOS/RHEL
        yum install -y wget nss atk at-spi2-atk cups-libs libXcomposite libXdamage libXrandr mesa-libgbm pango alsa-lib gtk3 libdrm libxkbcommon
        
        cat > /etc/yum.repos.d/google-chrome.repo << 'REPO'
[google-chrome]
name=google-chrome
baseurl=http://dl.google.com/linux/chrome/rpm/stable/x86_64
enabled=1
gpgcheck=1
gpgkey=https://dl.google.com/linux/linux_signing_key.pub
REPO
        yum install -y google-chrome-stable
        
    elif command -v apt &>/dev/null; then
        # Ubuntu/Debian
        apt update
        apt install -y wget gnupg2 fonts-liberation libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 libxcomposite1 libxdamage1 libxrandr2 xdg-utils
        
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
        echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
        apt update
        apt install -y google-chrome-stable
    fi
    
    if command -v google-chrome &>/dev/null; then
        info "Chrome 已安装: $(google-chrome --version)"
    else
        error "Chrome 安装失败"
    fi
else
    info "Chrome 已安装: $(google-chrome --version 2>/dev/null || google-chrome-stable --version 2>/dev/null)"
fi

# Create venv
info "创建虚拟环境..."
rm -rf "$VENV"
$PYTHON -m venv "$VENV"

# Install dependencies
info "安装依赖..."
$VENV/bin/pip install --upgrade pip
$VENV/bin/pip install -r requirements.txt

# Download ChromeDriver
info "下载 ChromeDriver..."
$VENV/bin/python3 tools/query_tools/chromedriver_manager.py

# Create data dirs
mkdir -p data/uploads data/outputs data/screenshots

# Restart service
info "重启服务..."
if systemctl is-active --quiet ybc-tools; then
    systemctl restart ybc-tools
    info "服务已重启"
else
    info "首次部署，创建 systemd 服务..."
    cat > /etc/systemd/system/ybc-tools.service << SVCEOF
[Unit]
Description=YBC Tools
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
ExecStart=$VENV/bin/gunicorn -c gunicorn.conf.py wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

    systemctl daemon-reload
    systemctl enable ybc-tools
    systemctl start ybc-tools
    info "服务已创建并启动"
fi

sleep 3
if curl -sf http://localhost:5001/health > /dev/null 2>&1; then
    info "部署成功!"
    curl -s http://localhost:5001/health
    echo ""
else
    echo "服务可能还在启动，查看日志: journalctl -u ybc-tools -f"
fi
