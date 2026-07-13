# YBC 工具箱

在线工具箱合集，Flask + Gunicorn，直接部署在 Linux 服务器。

## 本地开发

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 服务器部署

### 首次部署

```bash
# 安装依赖 (CentOS)
yum install -y git python3

# 克隆
cd /opt && git clone <仓库地址> ybc-tools
cd ybc-tools

# 配置
cp .env.example .env
vi .env  # 改 SECRET_KEY

# 一键部署
bash deploy/server.sh
```

### 后续升级

```bash
# 方式1: 服务器上执行
cd /opt/ybc-tools && bash deploy/server.sh

# 方式2: 本地远程执行
ssh root@<IP> "cd /opt/ybc-tools && bash deploy/server.sh"
```

### 1panel 反向代理

1panel -> 网站 -> 创建网站 -> 反向代理 -> `http://127.0.0.1:5001`

## 项目结构

```
├── app.py              # Flask 主应用
├── wsgi.py             # Gunicorn 入口
├── config.py           # 配置
├── version.py          # 版本号
├── requirements.txt    # 依赖
├── gunicorn.conf.py    # Gunicorn 配置
├── deploy/server.sh    # 部署脚本
├── templates/          # HTML 模板
├── static/             # CSS/JS
└── tools/              # 工具实现
```

## 新增工具

1. `tools/<分类>/` 创建模块，用 `@register_tool` 注册
2. `templates/tools/` 创建页面模板
