# classes/UniversityNoticeCrawler.py

from lxml import html
import requests
from typing import List, Dict, Any, Optional


class BaseWebCrawler:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def _fetch_html(self, url: str) -> html.HtmlElement:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # 응답 데이터를 바로 UTF-8로 디코딩
            return html.fromstring(response.content.decode('utf-8'))
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"URL 접속 실패: {e}")
        except UnicodeDecodeError as e:
            # UTF-8 디코딩 실패 시 다른 인코딩 시도
            try:
                return html.fromstring(response.content.decode('euc-kr'))
            except Exception:
                raise RuntimeError(f"인코딩 실패: {e}")


class UniversityNoticeCrawler(BaseWebCrawler):

    def get_document_links(self) -> List[Dict[str, str]]:
        """
        우리 학교 공지사항 페이지에서 제목, 하이퍼링크, 날짜를 추출합니다.

        Returns:
            각 공지사항의 제목, URL, 날짜를 담은 딕셔너리 리스트.
        """
        # 기본 URL 사용
        url = self.base_url

        tree = self._fetch_html(url)
        rows = tree.xpath('//*[@id="cms-content"]//table/tbody/tr')

        links = []
        for row in rows:
            date_tag = row.xpath('.//span[@class="b-date"]/text()')
            date_str = date_tag[0].strip() if date_tag else "날짜 없음"

            link_tag = row.xpath('.//a[@class="b-title"]')

            if link_tag:
                title = link_tag[0].text_content().strip()
                href = link_tag[0].get('href')

                if title and href:
                    full_url = "https://www.catholic.ac.kr" + href
                    links.append({
                        "title": title,
                        "url": full_url,
                        "date": date_str
                    })

        return links