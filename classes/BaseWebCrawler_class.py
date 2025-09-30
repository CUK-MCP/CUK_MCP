from lxml import html
import requests
import pytesseract
from PIL import Image
import io
import os
from typing import Optional

# Tesseract-OCR 실행 파일의 경로를 직접 지정합니다.
# 이 경로는 사용자의 컴퓨터에 따라 다릅니다.
# 주석처리해도 잘돌아가긴 하더라
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class BaseWebCrawler():
    """
    모든 웹 크롤러의 기반이 되는 추상 클래스.
    URL 접속 및 HTML 파싱과 같은 공통 기능을 제공합니다.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url

    def _fetch_html(self, url: str) -> Optional[html.HtmlElement]:
        """
        주어진 URL에서 HTML을 가져와 lxml 객체로 반환합니다.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return html.fromstring(response.content)
        except requests.exceptions.RequestException as e:
            print(f"URL 접속 실패: {e}")
            return None
        except Exception as e:
            print(f"HTML 파싱 또는 인코딩 실패: {e}")
            return None

    def _get_text_from_image(self, image_url: str) -> str:
        """
        URL에서 이미지를 메모리에 로드하고 Tesseract를 사용해 텍스트를 추출합니다.
        """
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()

            image_stream = io.BytesIO(response.content)
            image = Image.open(image_stream)

            text = pytesseract.image_to_string(image, lang='kor+eng')
            return text

        except Exception as e:
            print(f"이미지에서 텍스트 추출 실패: {e}")
            return ""