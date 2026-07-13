import os
from pathlib import Path


class FileBase:
    """文件处理基类"""

    def __init__(self, upload_dir='uploads', output_dir='outputs'):
        self.upload_dir = upload_dir
        self.output_dir = output_dir
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

    def get_file_info(self, file_path):
        path = Path(file_path)
        stat = path.stat()
        return {
            'name': path.name,
            'size': stat.st_size,
            'size_human': self._human_size(stat.st_size),
            'extension': path.suffix,
            'modified': stat.st_mtime
        }

    @staticmethod
    def _human_size(size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} TB'
