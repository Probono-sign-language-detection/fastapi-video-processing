import base64
import json
import logging
import time
from io import BytesIO
from typing import List
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

class PdfGenerator:
    """
     Simple use case:
        pdf_file = PdfGenerator(['https://google.com']).main()
        with open('new_pdf.pdf', "wb") as outfile:
            outfile.write(pdf_file[0].getbuffer())

    More info:
    # https://chromedevtools.github.io/devtools-protocol/tot/Page#method-printToPDF
    """
    driver = None
    print_options = {
        'landscape': True,
        'displayHeaderFooter': False,
        'printBackground': True,
        'preferCSSPageSize': True,
        'paperWidth': 11.69,  # 세로 길이를 가로로 설정 (가로 방향 출력을 위해)
        'paperHeight': 8.27,  # 가로 길이를 세로로 설정 (가로 방향 출력을 위해)
    }

    def __init__(self, urls: List[str], button_id: str):
        self.urls = urls
        self.button_id = button_id
        self.remote_selenium_grid_url = os.getenv("SELENIUM_GRID_URL")


    def _wait_for_page_to_load(self, timeout=10):
        WebDriverWait(self.driver, timeout).until(
            lambda x: x.execute_script("return document.readyState") == "complete"
        )
        print('_wait_for_page_to_load method 성공')

    def _close_new_tabs(self):
        print('_close_new_tabs method 시작')
        try:
            tabs = self.driver.window_handles
            while len(tabs) != 1:
                self.driver.switch_to.window(tabs[1])
                self.driver.close()
                tabs = self.driver.window_handles
            self.driver.switch_to.window(tabs[0])
            print('_close_new_tabs method 성공')
        except Exception as e:
            pass

    def _handle_js_alert(self, timeout=5):
        print('_handle_js_alert method 시작')
        try:
            alert = WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
            alert.accept()
            print('_handle_js_alert method 성공')
        except Exception as e:
            print('_handle_js_alert method 실패')
            print(e)
            pass

    def _try_remove_cookie_by_js(self):
        print('_try_remove_by_js method 시작')
        try:
            # Optionally set a cookie and localStorage item to prevent popups - verify if needed
            self.driver.execute_script("""
                document.cookie = "cookiePopupShown=true";
                localStorage.setItem('popupShown', 'true');
            """)
            print('_try_remove_by_js method 성공')
        except Exception as e:
            print(e)
            print(f"try_remove_cookie_by_js 실패")
            pass


    def _click_popup_close_button_by_id(self, selector):
        print('_click_popup_close_button method 시작')
        try:
            popup_close_button = self.driver.find_element(By.ID, selector)
            popup_close_button.click()
            print('_click_popup_close_button method 성공')
        except Exception as e:
            print('_click_popup_close_button method 실패')
            print(e)
            pass

    def _click_popup_close_button_by_css_selector(self, selector):
        print('_click_popup_close_button_by_css_selector method')
        try:
            popup_close_button = self.driver.find_element(By.CSS_SELECTOR,selector)
            popup_close_button.click()
            print('_click_popup_close_button_by_css_selector method 성공')
        except Exception as e:
            pass 

    def _wait_and_click_popup_id(self, selector, timeout=10):
        print('_wait_and_click_popup method 시작')
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.ID, selector))
                )
            self.driver.execute_script("arguments[0].click();", element)
            print('_wait_and_click_popup method 성공')
        except Exception as e:
            print('_wait_and_click_popup method 실패')
            print(e)
            pass

    def _get_pdf_from_url(self, url, *args, **kwargs):
        self.driver.get(url)
        # Wait for the page to load
        self._wait_for_page_to_load(timeout=10)

        # Try various methods to close popups/alerts    
        self._close_new_tabs()
        
        self._handle_js_alert(timeout=5)
        self._try_remove_cookie_by_js()

        self._click_popup_close_button_by_id(self.button_id)
        self._click_popup_close_button_by_css_selector(self.button_id)
        self._wait_and_click_popup_id(self.button_id, timeout=10)

        print_options = self.print_options.copy()
        result = self._send_devtools(self.driver, "Page.printToPDF", print_options)
        return base64.b64decode(result['data'])
    

    @staticmethod
    def _send_devtools(driver, cmd, params):
        """
        크롬 개발자 도구를 이용해서 pdf를 생성하는 방법
        Works only with chromedriver.
        Method uses cromedriver's api to pass various commands to it.
        """
        resource = "/session/%s/chromium/send_command_and_get_result" % driver.session_id
        url = driver.command_executor._url + resource
        body = json.dumps({'cmd': cmd, 'params': params})
        response = driver.command_executor._request('POST', url, body)
        return response.get('value')

    def _generate_pdfs(self):
        pdf_files = []

        for url in self.urls:
            result = self._get_pdf_from_url(url)
            file = BytesIO()
            file.write(result)
            pdf_files.append(file)

        return pdf_files

    def main(self) -> List[BytesIO]:
        webdriver_options = ChromeOptions()
        webdriver_options.add_argument('--headless')
        webdriver_options.add_argument('--disable-gpu')
        webdriver_options.add_argument('--disable-extensions')
        webdriver_options.add_argument('window-size=1920x1080')
        webdriver_options.add_argument('disable-infobars')
        webdriver_options.add_argument('--disable-cookies')
        webdriver_options.add_argument('--disable-popup-blocking')
        webdriver_options.add_argument("disable-notifications")
        webdriver_options.add_argument('--disable-popup-blocking')
        webdriver_options.add_argument("--disable-single-click-autofill")

        webdriver_options.add_experimental_option("prefs", {"autofill.profile_enabled": False})
        webdriver_options.add_experimental_option("prefs", {"disable-popup-blocking": True})
        webdriver_options.add_experimental_option("excludeSwitches", ["disable-infobars"])
        webdriver_options.add_experimental_option("useAutomationExtension", False)

        webdriver_options.add_argument(
            f"user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
        )

        # Set desired capabilities using options
        webdriver_options.set_capability('browserName', 'chrome')
        
        try:
            # Initialize the browser - host.docker.internal
            self.driver = driver = webdriver.Remote(
                command_executor=self.remote_selenium_grid_url,
                options=webdriver_options
            )
            result = self._generate_pdfs()
        finally:
            self.driver.close()

        return result