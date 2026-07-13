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

# Always recreate venv to ensure correct Python version
info "创建虚拟环境..."
rm -rf "$VENV"
$PYTHON -m venv "$VENV"

# Upgrade pip first, then install dependencies
info "安装依赖..."
$VENV/bin/pip install --upgrade pip
$VENV/bin/pip install -r requirements.txt

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
