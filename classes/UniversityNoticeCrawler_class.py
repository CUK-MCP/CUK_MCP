import datetime
from typing import List, Dict, Any, Optional
from classes.BaseWebCrawler_class import BaseWebCrawler
from lxml import etree
class UniversityNoticeCrawler(BaseWebCrawler):
    """
    우리 학교 공지사항 페이지를 크롤링하는 클래스.
    """
    def get_document_links(self, category: Optional[str] = None, start_page: int = 0, end_page: int = 0) -> List[Dict[str, str]]:
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

        if start_page < 1:
            start_page = 1
        if end_page < start_page:
            end_page = start_page

        # 카테고리가 전달되지 않거나 유효하지 않은 경우, 전체 목록 URL을 구성합니다.
        if category and category in category_map:
            category_id = category_map[category]
            url = f"{self.base_url}?mode=list&srCategoryId={category_id}&srSearchKey=&srSearchVal="

        else:
            # 카테고리가 None이거나 유효하지 않을 때, 전체 공지사항을 가져오기 위한 URL
            url = f"{self.base_url}?mode=list"

        seen: set[tuple[str, str]] = set()
        all_results: List[Dict[str, str]] = []

        for page in range(start_page, end_page + 1):
            page_offset = (page-1)*10
            final_url = f"{url}&articleLimit=10&article.offset={page_offset}"
            tree = self._fetch_html(final_url)
            if not tree:
                return []

            titles = tree.xpath('//a[@class="b-title"]//text()')
            days = tree.xpath('//span[@class="b-con b-date"]//text()')
            links = tree.xpath('//a[@class="b-title"]/@href')
            if not titles:
                return []
            titles = [t.strip() for t in titles if t and t.strip()]
            dates = [d.strip() for d in days if d and d.strip()]
            links = [l.strip() for l in links if l and l.strip()]
            for title, date_str,link in zip(titles, dates, links):
                key = (title, date_str)
                if key in seen:
                    continue  # 이미 본 공지라면 스킵
                seen.add(key)
                all_results.append({
                    "title": title,
                    "date": date_str,
                    "link": link
                })
        return all_results

    def get_notice_detail(self,link: str) -> Dict[str,str]:
        url = self.base_url + f"{link}"
        tree = self._fetch_html(url)
        print(self.base_url)
        contents = tree.xpath('//div[@class="b-con-box"]//text()')
        contents = " ".join([c.strip() for c in contents if c and c.strip()])

        return {"contents": contents}