import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'ybc-tools-dev-secret-key')
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
    OUTPUT_FOLDER = os.path.join(DATA_DIR, 'outputs')
    SCREENSHOT_FOLDER = os.path.join(DATA_DIR, 'screenshots')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    ALLOWED_EXTENSIONS = {'json', 'csv', 'xml', 'txt', 'xlsx', 'pdf', 'png', 'jpg', 'zip', 'tar'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
