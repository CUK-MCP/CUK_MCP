import datetime
from typing import List, Dict, Any, Optional
from classes.BaseWebCrawler_class import BaseWebCrawler
from lxml import etree, html


class DepartmentNoticeCrawler(BaseWebCrawler):
    """
    특정 학과의 공지사항 페이지를 크롤링하는 클래스.
    """

    def __init__(self, department_url_slug: str):
        # 학과명으로 베이스 URL을 동적으로 생성
        base_url = f"https://{department_url_slug}.catholic.ac.kr"
        super().__init__(base_url)
        self.department_url_slug = department_url_slug

    def get_document_links(self) -> List[Dict[str, str]]:
        """
        해당 학과의 공지사항 목록을 추출합니다.
        """
        # 학과 목록 페이지의 전체 URL을 구성
        url = f"{self.base_url}/{self.department_url_slug}/community/notice.do"

        tree = self._fetch_html(url)
        if not tree:
            return []

        all_results: List[Dict[str, str]] = []

        titles = tree.xpath('//a[@class="b-title"]//text()')
        days = tree.xpath('//span[@class="b-con b-date"]//text()')
        links = tree.xpath('//a[@class="b-title"]/@href')

        if not titles:
            return []

        titles = [t.strip() for t in titles if t and t.strip()]
        dates = [d.strip() for d in days if d and d.strip()]
        links = [l.strip() for l in links if l and l.strip()]

        for title, date_str, link in zip(titles, dates, links):
            all_results.append({
                "title": title,
                "date": date_str,
                "link": link
            })
        return all_results

    def get_notice_detail(self, link: str) -> Dict[str, str]:
        """
        학과 공지사항 상세 페이지의 내용을 가져옵니다.
        """
        # `link`는 상대 경로이므로, 전체 경로와 함께 URL을 구성해야 합니다.
        url = f"{self.base_url}/{self.department_url_slug}/community/notice.do" + link

        tree = self._fetch_html(url)
        if not tree:
            return {"error": "페이지를 가져오는 데 실패했습니다."}

        contents = tree.xpath('//div[@class="b-con-box"]//text()')
        contents = " ".join([c.strip() for c in contents if c and c.strip()])

        return {"contents": contents}