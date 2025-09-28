import datetime
from typing import List, Dict, Any, Optional
from classes.BaseWebCrawler import BaseWebCrawler

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

        links = []
        page_offset = 0
        one_month_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).date()
        stop_crawling = False

        while not stop_crawling:
            final_url = f"{url}&articleLimit=10&article.offset={page_offset}"
            tree = self._fetch_html(final_url)

            if not tree:
                break

            rows = tree.xpath('//div[@class="bn-list-common01 list_type_basic"]/table/tbody/tr')
            if not rows:
                break

            for row in rows:
                date_tag = row.xpath('./td[4]/text()')
                date_str = date_tag[0].strip() if date_tag else None

                if not date_str:
                    continue

                try:
                    notice_date = datetime.datetime.strptime(date_str, '%Y.%m.%d').date()
                    if notice_date < one_month_ago:
                        stop_crawling = True
                        break
                except ValueError:
                    print(f"날짜 형식 오류: {date_str}. 크롤링을 계속합니다.")
                    continue

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

            if stop_crawling:
                break

            page_offset += 10

        return links