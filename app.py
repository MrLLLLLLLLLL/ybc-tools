from flask import Flask
from config import Config
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure upload/output directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SCREENSHOT_FOLDER'], exist_ok=True)

    # Import and register tool routes
    from tools.registry import get_all_tools

    @app.route('/health')
    def health():
        return {'status': 'ok'}

    @app.context_processor
    def inject_tools():
        return dict(all_tools=get_all_tools())

    # Register blueprints
    from app import main_bp
    app.register_blueprint(main_bp)

    return app


from flask import Blueprint, render_template, request, jsonify, send_file
import json
import os
import time

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """首页"""
    from tools.registry import get_all_tools
    tools = get_all_tools()
    return render_template('index.html', tools=tools)


@main_bp.route('/tool/<tool_name>')
def tool_page(tool_name):
    """工具详情页面"""
    from tools.registry import get_tool_by_name
    tool = get_tool_by_name(tool_name)
    if tool is None:
        return render_template('404.html'), 404
    return render_template(f'tools/{tool_name}.html', tool=tool)


# ---- API: JSON 格式化 ----
@main_bp.route('/api/devtools/json-format', methods=['POST'])
def api_json_format():
    data = request.json
    if not data:
        return jsonify({'code': 400, 'message': '请提供 JSON 数据'}), 400

    json_string = data.get('json_string', '')
    indent = data.get('indent', 2)
    sort_keys = data.get('sort_keys', False)

    try:
        parsed = json.loads(json_string)
        formatted = json.dumps(parsed, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
        return jsonify({
            'code': 200,
            'data': {
                'formatted': formatted,
                'valid': True,
                'keys_count': len(parsed) if isinstance(parsed, dict) else len(parsed) if isinstance(parsed, list) else 0
            }
        })
    except json.JSONDecodeError as e:
        return jsonify({
            'code': 400,
            'data': {
                'formatted': '',
                'valid': False,
                'error': str(e)
            },
            'message': '无效的 JSON 格式'
        }), 400


# ---- API: Selenium 截图 ----
@main_bp.route('/api/selenium/screenshot', methods=['POST'])
def api_screenshot():
    data = request.json
    if not data or not data.get('url'):
        return jsonify({'code': 400, 'message': '请提供 URL'}), 400

    url = data['url']
    width = data.get('width', 1920)
    height = data.get('height', 1080)
    full_page = data.get('full_page', True)

    try:
        from tools.selenium_tools.screenshot import ScreenshotTool
        from flask import current_app
        tool = ScreenshotTool()
        filename = f'screenshot_{int(time.time())}.png'
        output_path = os.path.join(current_app.config['SCREENSHOT_FOLDER'], filename)
        result = tool.capture(url, output_path, width=width, height=height, full_page=full_page)

        if result['success']:
            return jsonify({
                'code': 200,
                'data': {
                    'image_url': f'/static/screenshots/{filename}',
                    'size': result.get('size', {})
                },
                'message': '截图成功'
            })
        else:
            return jsonify({'code': 500, 'message': result.get('error', '截图失败')}), 500
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


# ---- API: 文件格式转换 ----
@main_bp.route('/api/file/convert', methods=['POST'])
def api_file_convert():
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '请上传文件'}), 400

    file = request.files['file']
    target_format = request.form.get('format', '')

    if file.filename == '':
        return jsonify({'code': 400, 'message': '未选择文件'}), 400

    if not target_format:
        return jsonify({'code': 400, 'message': '请指定目标格式'}), 400

    try:
        from config import allowed_file
        if not allowed_file(file.filename):
            return jsonify({'code': 400, 'message': '不支持的文件格式'}), 400

        from flask import current_app
        from tools.file_tools.converter import FileConverter

        # Save uploaded file
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
        file.save(upload_path)

        converter = FileConverter()
        base_name = os.path.splitext(file.filename)[0]
        output_filename = f'{base_name}.{target_format}'
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)

        source_ext = file.filename.rsplit('.', 1)[1].lower()

        if source_ext == 'json' and target_format == 'csv':
            result = converter.json_to_csv(upload_path, output_path)
        elif source_ext == 'csv' and target_format == 'json':
            result = converter.csv_to_json(upload_path, output_path)
        elif source_ext == 'xml' and target_format == 'json':
            result = converter.xml_to_json(upload_path, output_path)
        else:
            return jsonify({'code': 400, 'message': f'不支持 {source_ext} -> {target_format} 的转换'}), 400

        if result.get('success'):
            return send_file(output_path, as_attachment=True, download_name=output_filename)
        else:
            return jsonify({'code': 500, 'message': result.get('error', '转换失败')}), 500
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


# ---- API: 工具列表 ----
@main_bp.route('/api/tools')
def api_tools():
    from tools.registry import get_all_tools
    return jsonify({'code': 200, 'data': get_all_tools()})


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5001)


# ---- API: 华数华大成绩查询 ----
@main_bp.route('/api/query/hswh/single', methods=['POST'])
def api_hswh_single():
    """单个账号查询"""
    data = request.json
    if not data:
        return jsonify({'code': 400, 'success': False, 'error': '请提供查询数据'}), 400

    mobile = data.get('mobile', '').strip()
    password = data.get('password', '').strip()
    if not mobile or not password:
        return jsonify({'code': 400, 'success': False, 'error': '请输入账号和密码'}), 400

    try:
        from tools.query_tools.hswh_score import HswhScoreQuery
        from flask import current_app
        query = HswhScoreQuery(
            driver_path=current_app.config.get('CHROMEDRIVER_PATH', '')
        )
        result = query.query_single(mobile, password)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/api/query/hswh/keyword', methods=['POST'])
def api_hswh_keyword():
    """按编号查询"""
    data = request.json
    if not data:
        return jsonify({'code': 400, 'success': False, 'error': '请提供查询数据'}), 400

    keyword = data.get('keyword', '').strip()
    if not keyword:
        return jsonify({'code': 400, 'success': False, 'error': '请输入编号'}), 400

    try:
        from tools.query_tools.hswh_score import HswhScoreQuery
        from flask import current_app
        query = HswhScoreQuery(
            driver_path=current_app.config.get('CHROMEDRIVER_PATH', '')
        )
        result = query.query_by_keyword(keyword)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/api/query/hswh/batch', methods=['POST'])
def api_hswh_batch():
    """批量查询"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'success': False, 'error': '请上传 Excel 文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'success': False, 'error': '未选择文件'}), 400

    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({'code': 400, 'success': False, 'error': '请上传 Excel 文件'}), 400

    try:
        from tools.query_tools.hswh_score import HswhScoreQuery
        from flask import current_app
        import tempfile

        # Save uploaded file
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        # Read accounts from Excel
        from tools.query_tools.hswh_score import read_batch_accounts
        accounts = read_batch_accounts(tmp_path)

        # Clean up temp file
        os.unlink(tmp_path)

        # Query
        query = HswhScoreQuery(
            driver_path=current_app.config.get('CHROMEDRIVER_PATH', '')
        )
        result = query.query_batch(accounts)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@main_bp.route('/api/query/hswh/template', methods=['GET'])
def api_hswh_template():
    """下载批量查询模板"""
    from flask import send_file
    from tools.query_tools.hswh_score import write_template_xlsx
    import tempfile

    tmp_path = tempfile.mktemp(suffix='.xlsx')
    write_template_xlsx(tmp_path)
    return send_file(tmp_path, as_attachment=True, download_name='华数华大成绩查询模板.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
