import unittest
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_homepage(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'tool-card', resp.data)
        self.assertIn(b'YBC', resp.data)

    def test_api_tools(self):
        resp = self.client.get('/api/tools')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data['code'], 200)
        self.assertIn('dev_tools', data['data'])

    def test_json_format_valid(self):
        resp = self.client.post('/api/devtools/json-format',
            json={'json_string': '{"a":1,"b":2}', 'indent': 2})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['data']['valid'])
        self.assertIn('\n', data['data']['formatted'])

    def test_json_format_invalid(self):
        resp = self.client.post('/api/devtools/json-format',
            json={'json_string': 'not json', 'indent': 2})
        self.assertEqual(resp.status_code, 400)
        data = json.loads(resp.data)
        self.assertFalse(data['data']['valid'])

    def test_json_format_sort_keys(self):
        resp = self.client.post('/api/devtools/json-format',
            json={'json_string': '{"z":1,"a":2}', 'indent': 2, 'sort_keys': True})
        data = json.loads(resp.data)
        formatted = data['data']['formatted']
        self.assertTrue(formatted.index('"a"') < formatted.index('"z"'))

    def test_tool_page_json_formatter(self):
        resp = self.client.get('/tool/json_formatter')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'JSON', resp.data)

    def test_tool_page_file_converter(self):
        resp = self.client.get('/tool/file_converter')
        self.assertEqual(resp.status_code, 200)

    def test_tool_page_404(self):
        resp = self.client.get('/tool/nonexistent')
        self.assertEqual(resp.status_code, 404)

    def test_file_convert_no_file(self):
        resp = self.client.post('/api/file/convert')
        self.assertEqual(resp.status_code, 400)

    def test_screenshot_no_url(self):
        resp = self.client.post('/api/selenium/screenshot',
            json={})
        self.assertEqual(resp.status_code, 400)


class TestJsonConversion(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_json_to_csv(self):
        import tempfile
        import io

        # Create a JSON file
        json_data = json.dumps([{'name': 'Alice', 'age': '30'}, {'name': 'Bob', 'age': '25'}])
        data = {
            'file': (io.BytesIO(json_data.encode()), 'test.json'),
            'format': 'csv'
        }
        resp = self.client.post('/api/file/convert',
            data=data, content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'name', resp.data)
        self.assertIn(b'Alice', resp.data)

    def test_csv_to_json(self):
        import io

        csv_data = 'name,age\nAlice,30\nBob,25\n'
        data = {
            'file': (io.BytesIO(csv_data.encode()), 'test.csv'),
            'format': 'json'
        }
        resp = self.client.post('/api/file/convert',
            data=data, content_type='multipart/form-data')
        self.assertEqual(resp.status_code, 200)
        result = json.loads(resp.data)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'Alice')


if __name__ == '__main__':
    unittest.main()
