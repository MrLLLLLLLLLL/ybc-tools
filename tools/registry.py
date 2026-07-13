TOOL_REGISTRY = {}


def register_tool(category_id, category_name, name, title, description, icon='box'):
    """工具注册装饰器

    Usage:
        @register_tool('dev_tools', '开发工具', 'json_formatter', 'JSON 格式化', '格式化和验证 JSON 数据', icon='braces')
        def json_formatter():
            ...
    """
    def decorator(func):
        if category_id not in TOOL_REGISTRY:
            TOOL_REGISTRY[category_id] = {
                'id': category_id,
                'name': category_name,
                'tools': []
            }

        TOOL_REGISTRY[category_id]['tools'].append({
            'name': name,
            'title': title,
            'description': description,
            'icon': icon,
            'url': f'/tool/{name}',
            'handler': func
        })
        return func
    return decorator


_tools_loaded = False


def _ensure_tools_loaded():
    """Lazily import all tool modules to trigger registration (avoids circular imports)."""
    global _tools_loaded
    if _tools_loaded:
        return
    _tools_loaded = True
    import importlib
    import pkgutil
    import tools as tools_pkg

    for _importer, modname, _ispkg in pkgutil.walk_packages(
        tools_pkg.__path__, prefix='tools.'
    ):
        try:
            importlib.import_module(modname)
        except Exception as e:
            print(f'Warning: Failed to import {modname}: {e}')


def get_all_tools():
    """获取所有已注册工具（不含 handler）"""
    _ensure_tools_loaded()
    result = {}
    for cat_id, cat_data in TOOL_REGISTRY.items():
        result[cat_id] = {
            'id': cat_data['id'],
            'name': cat_data['name'],
            'tools': [{
                'name': t['name'],
                'title': t['title'],
                'description': t['description'],
                'icon': t['icon'],
                'url': t['url']
            } for t in cat_data['tools']]
        }
    return result


def get_tool_by_name(tool_name):
    """根据名称查找工具"""
    _ensure_tools_loaded()
    for cat_data in TOOL_REGISTRY.values():
        for tool in cat_data['tools']:
            if tool['name'] == tool_name:
                return {
                    'name': tool['name'],
                    'title': tool['title'],
                    'description': tool['description'],
                    'icon': tool['icon'],
                    'url': tool['url'],
                    'category': cat_data['name']
                }
    return None
