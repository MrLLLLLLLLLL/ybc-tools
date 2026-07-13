#!/bin/bash
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

APP_DIR="/opt/ybc-tools"
VENV="$APP_DIR/.venv"

cd "$APP_DIR"

# Git pull
info "拉取最新代码..."
git pull origin main

# Check Python version (need 3.8+)
PYTHON_CMD=""
for cmd in python3.11 python3.10 python3.9 python3; do
    if command -v "$cmd" &>/dev/null; then
        version=$($cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

# Install Python 3.11 if needed
if [ -z "$PYTHON_CMD" ]; then
    warn "未找到 Python 3.8+，正在安装 Python 3.11..."
    
    # Detect package manager
    if command -v apt &>/dev/null; then
        apt update
        apt install -y software-properties-common
        add-apt-repository -y ppa:deadsnakes/ppa
        apt update
        apt install -y python3.11 python3.11-venv python3.11-dev
        PYTHON_CMD="python3.11"
    elif command -v yum &>/dev/null; then
        yum install -y epel-release
        yum install -y python3.11 python3.11-pip python3.11-devel
        PYTHON_CMD="python3.11"
    elif command -v dnf &>/dev/null; then
        dnf install -y epel-release
        dnf install -y python3.11 python3.11-pip python3.11-devel
        PYTHON_CMD="python3.11"
    else
        error "无法安装 Python，请手动安装 Python 3.8+"
    fi
fi

info "使用 Python: $PYTHON_CMD ($($PYTHON_CMD --version))"

# Create venv if not exists
if [ ! -d "$VENV" ]; then
    info "创建虚拟环境..."
    $PYTHON_CMD -m venv "$VENV"
fi

# Upgrade pip and install dependencies
info "安装依赖..."
$VENV/bin/pip install --upgrade pip -q
$VENV/bin/pip install -r requirements.txt -q

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

# Health check
sleep 3
if curl -sf http://localhost:5001/health > /dev/null 2>&1; then
    info "部署成功!"
    curl -s http://localhost:5001/health
    echo ""
else
    warn "服务可能还在启动中..."
    systemctl status ybc-tools --no-pager | head -10
    echo ""
    info "查看日志: journalctl -u ybc-tools -f"
fi
