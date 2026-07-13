from .base import FileBase
from tools.registry import register_tool
import json
import csv
import xml.etree.ElementTree as ET


@register_tool('file_tools', '文件处理', 'file_converter', '文件格式转换', '支持 JSON/CSV/XML 之间的格式转换', icon='file-text')
class FileConverter(FileBase):
    """文件格式转换工具"""

    def json_to_csv(self, json_path, csv_path):
        """JSON 转 CSV"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list) or len(data) == 0:
                return {'success': False, 'error': 'JSON 数据必须是非空数组'}

            headers = set()
            for item in data:
                if isinstance(item, dict):
                    headers.update(item.keys())

            headers = sorted(headers)

            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                for item in data:
                    if isinstance(item, dict):
                        writer.writerow({k: str(v) for k, v in item.items()})

            return {'success': True, 'rows': len(data), 'columns': len(headers)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def csv_to_json(self, csv_path, json_path):
        """CSV 转 JSON"""
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                data = list(reader)

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return {'success': True, 'rows': len(data)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def xml_to_json(self, xml_path, json_path):
        """XML 转 JSON"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            def element_to_dict(element):
                result = {}
                if element.attrib:
                    result['@attributes'] = element.attrib

                children = list(element)
                if not children:
                    result['#text'] = element.text or ''
                    if len(result) == 1 and '#text' in result:
                        return result['#text']
                    return result

                for child in children:
                    child_data = element_to_dict(child)
                    if child.tag in result:
                        if not isinstance(result[child.tag], list):
                            result[child.tag] = [result[child.tag]]
                        result[child.tag].append(child_data)
                    else:
                        result[child.tag] = child_data
                return result

            data = {root.tag: element_to_dict(root)}

            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}
