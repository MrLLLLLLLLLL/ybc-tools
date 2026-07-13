from app import create_app
from version import __version__
import os

app = create_app()


@app.route('/health')
def health():
    """健康检查端点"""
    return {'status': 'ok', 'version': __version__}


if __name__ == '__main__':
    app.run()
