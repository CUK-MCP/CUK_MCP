import datetime
from typing import List, Dict, Any, Optional
from classes.BaseWebCrawler_class import BaseWebCrawler
from lxml import etree
import requests


class UniversityNoticeCrawler(BaseWebCrawler):
    """
    우리 학교 공지사항 페이지를 크롤링하는 클래스.
    """

    # ... (기존 get_document_links 함수는 그대로 둡니다)

    def get_notice_detail(self, link: str) -> Dict[str, str]:
        url = self.base_url + f"{link}"
        tree = self._fetch_html(url)
        if not tree:
            return {"error": "페이지를 가져오는 데 실패했습니다."}

        # 1. 본문 텍스트 추출
        contents = tree.xpath('//div[@class="b-con-box"]//text()')
        text_content = " ".join([c.strip() for c in contents if c and c.strip()])

        # 2. 본문 내 이미지 URL 찾기
        image_urls = tree.xpath('//div[@class="b-con-box"]//img/@src')

        ocr_text = ""
        # 3. 각 이미지 URL에 대해 OCR 실행
        for img_url in image_urls:
            full_img_url = requests.compat.urljoin(url, img_url)

            extracted_text = self._get_text_from_image(full_img_url)
            if extracted_text:
                ocr_text += f"\n\n[OCR 이미지 텍스트]:\n{extracted_text}"

        # 4. 최종 결과 반환
        return {"contents": text_content + ocr_text}