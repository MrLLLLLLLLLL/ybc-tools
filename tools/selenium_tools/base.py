from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class SeleniumBase:
    """Selenium 工具基类"""

    def __init__(self, headless=True):
        self.headless = headless

    def _build_options(self, width=1920, height=1080):
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--window-size={width},{height}')
        return options

    def get_driver(self, width=1920, height=1080):
        options = self._build_options(width, height)
        return webdriver.Chrome(options=options)
