# ===== YBC 工具箱 Gunicorn 配置 =====
import multiprocessing
import os

# 绑定地址
bind = "0.0.0.0:5001"

# 工作进程数
cpu_count = multiprocessing.cpu_count()
workers = int(os.getenv('SERVER_WORKERS', min(cpu_count * 2 + 1, 8)))

# 工作进程类型
worker_class = "sync"

# 超时时间 (秒)
timeout = 120

# 最大请求数 (防内存泄漏)
max_requests = 1000
max_requests_jitter = 50

# 日志
accesslog = "-"  # 输出到 stdout
errorlog = "-"   # 输出到 stderr
loglevel = "info"

# 进程名
proc_name = "ybc-tools"

# 预加载
preload_app = True
