from .base import SeleniumBase
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tools.registry import register_tool
import time


@register_tool('selenium', 'Selenium 自动化', 'screenshot', '网页截图', '自动截取网页截图，支持全页面和指定区域', icon='camera')
class ScreenshotTool(SeleniumBase):
    """网页截图工具"""

    def capture(self, url, output_path, width=1920, height=1080, full_page=True):
        """截取网页截图

        Args:
            url: 目标网页 URL
            output_path: 截图保存路径
            width: 浏览器宽度
            height: 浏览器高度
            full_page: 是否截取整个页面
        """
        driver = self.get_driver(width, height)
        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, 'body'))
            )
            time.sleep(1)  # 等待动态内容加载

            if full_page:
                # 获取页面总高度
                total_height = driver.execute_script(
                    'return Math.max(document.body.scrollHeight, '
                    'document.documentElement.scrollHeight)'
                )
                driver.set_window_size(width, total_height)
                time.sleep(0.5)

            driver.save_screenshot(output_path)

            return {
                'success': True,
                'path': output_path,
                'size': {'width': width, 'height': total_height if full_page else height}
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            driver.quit()

    def capture_element(self, url, selector, output_path):
        """截取特定元素"""
        driver = self.get_driver()
        try:
            driver.get(url)
            element = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            time.sleep(0.5)
            element.screenshot(output_path)
            return {'success': True, 'path': output_path}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            driver.quit()
