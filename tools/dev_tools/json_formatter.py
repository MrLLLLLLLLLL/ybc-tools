import json
from tools.registry import register_tool


@register_tool('dev_tools', '开发工具', 'json_formatter', 'JSON 格式化', '格式化、压缩和验证 JSON 数据', icon='braces')
def json_formatter_handler():
    pass


def format_json(json_string, indent=2, sort_keys=False):
    """格式化 JSON 字符串"""
    try:
        parsed = json.loads(json_string)
        formatted = json.dumps(parsed, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
        return {
            'success': True,
            'formatted': formatted,
            'valid': True,
            'keys_count': len(parsed) if isinstance(parsed, (dict, list)) else 0
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'valid': False,
            'error': str(e)
        }


def compress_json(json_string):
    """压缩 JSON（去除空白）"""
    try:
        parsed = json.loads(json_string)
        compressed = json.dumps(parsed, separators=(',', ':'), ensure_ascii=False)
        return {
            'success': True,
            'compressed': compressed,
            'valid': True,
            'original_size': len(json_string),
            'compressed_size': len(compressed)
        }
    except json.JSONDecodeError as e:
        return {'success': False, 'valid': False, 'error': str(e)}
