from lxml import html
import requests
from typing import List, Dict, Any
from abc import ABC, abstractmethod
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.detech(), encoding= 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detech(), encoding= 'uft-8')

class BaseWebCrawler(ABC):

    def __init__(self, base_url: str):
        self.base_url = base_url

    def _fetch_html(self, url: str) -> html.HtmlElement:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # 1. requests의 추측 인코딩을 무시하고, lxml에 바이트 데이터 전달
            # lxml이 내부적으로 인코딩을 처리하도록 합니다.
            # .content는 바이트 형태의 원시 데이터입니다.
            tree = html.fromstring(response.content)

            # 2. 만약 lxml이 인코딩을 잘못 감지했다면, UTF-8로 강제 디코딩 후 다시 파싱
            if tree.xpath('//meta[@charset]'):
                charset_tag = tree.xpath('//meta[@charset]')[0]
                encoding = charset_tag.attrib['charset'].lower()
                if encoding != 'utf-8':
                    decoded_content = response.content.decode('utf-8', errors='ignore')
                    return html.fromstring(decoded_content)

            return tree

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"URL 접속 실패: {e}")
        except Exception as e:
            raise RuntimeError(f"HTML 파싱 또는 인코딩 실패: {e}")