from lxml import html
import requests
from abc import ABC
from typing import Optional

class BaseWebCrawler(ABC):
    """
    모든 웹 크롤러의 기반이 되는 추상 클래스.
    URL 접속 및 HTML 파싱과 같은 공통 기능을 제공합니다.
    """
    def __init__(self, base_url: str):
        self.base_url = base_url

    def _fetch_html(self, url: str) -> Optional[html.HtmlElement]:
        """
        주어진 URL에서 HTML을 가져와 lxml 객체로 반환합니다.
        다양한 인코딩을 처리할 수 있도록 견고하게 작성되었습니다.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # lxml이 내부적으로 인코딩을 처리하도록 바이트 데이터를 전달합니다.
            return html.fromstring(response.content)
        except requests.exceptions.RequestException as e:
            print(f"URL 접속 실패: {e}")
            return None
        except Exception as e:
            print(f"HTML 파싱 또는 인코딩 실패: {e}")
            return None