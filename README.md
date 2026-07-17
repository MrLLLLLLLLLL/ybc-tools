# YBC 工具箱

本地 Flask 工具合集，提供各类实用在线工具。

## 快速启动

```bash
cd /Volumes/Data-111/YBC
source .venv/bin/activate
python app.py
```

打开浏览器访问 http://localhost:5001

## 已有工具

- **JSON 格式化** - 格式化和验证 JSON 数据
- **网页截图** - 输入 URL 截取网页截图
- **文件格式转换** - JSON/CSV/XML 互转
- **华数华大成绩查询** - 单个/批量查询比赛成绩

## 添加新工具

1. 在 `tools/` 对应分类目录下创建工具文件
2. 用 `@register_tool` 装饰器注册
3. 在 `templates/tools/` 下创建对应 HTML 页面
4. 重启应用，首页自动显示新工具

## 目录结构

```
YBC/
  app.py              # 主程序入口
  config.py            # 配置
  requirements.txt     # 依赖
  tools/               # 工具代码
  templates/           # HTML 模板
  static/              # CSS / JS / 图片
  data/                # 上传 / 输出 / 截图
```
