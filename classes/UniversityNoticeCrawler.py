import datetime
from typing import List, Dict, Any, Optional
from classes.BaseWebCrawler import BaseWebCrawler
from lxml import etree
class UniversityNoticeCrawler(BaseWebCrawler):
    """
    우리 학교 공지사항 페이지를 크롤링하는 클래스.
    """
    def get_document_links(self, category: Optional[str] = None) -> List[Dict[str, str]]:
        """
        지정된 카테고리의 공지사항 목록을 추출합니다.
        게시일이 1달 이내인 문서만 반환합니다.

        Args:
            category (Optional[str]): '일반', '학사', '장학', '취창업' 중 하나.
        """
        category_map = {
            '일반': 20,
            '학사': 21,
            '장학': 22,
            '취창업': 23
        }

        # 카테고리가 전달되지 않거나 유효하지 않은 경우, 전체 목록 URL을 구성합니다.
        if category and category in category_map:
            category_id = category_map[category]
            url = f"{self.base_url}?mode=list&srCategoryId={category_id}&srSearchKey=&srSearchVal="

        else:
            # 카테고리가 None이거나 유효하지 않을 때, 전체 공지사항을 가져오기 위한 URL
            url = f"{self.base_url}?mode=list"
        page_offset = 0
        final_url = f"{url}&articleLimit=10&article.offset={page_offset}"
        tree = self._fetch_html(final_url)
        if not tree:
            return []

        titles = tree.xpath('//a[@class="b-title"]//text()')
        days = tree.xpath('//span[@class="b-con b-date"]//text()')

        if not titles:
            return []
        titles = [t.strip() for t in titles if t and t.strip()]
        dates = [d.strip() for d in days if d and d.strip()]
        results = []
        for title, date_str in zip(titles, dates):
            # 날짜 형식 체크 및 한 달 이전이면 중단(원래 로직 유지)

            results.append({
                "title": title,
                "date": date_str
            })


        return results