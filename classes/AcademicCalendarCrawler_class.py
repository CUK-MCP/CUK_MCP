# classes/AcademicCalendarCrawler_class.py
from __future__ import annotations
import re
from typing import List, Dict, Tuple
from classes.BaseWebCrawler_class import BaseWebCrawler


class AcademicCalendarCrawler(BaseWebCrawler):
    """
    가톨릭대학교 학사일정 페이지에서 연도별 학사 일정을 크롤링하는 클래스
    """

    def __init__(self, base_url: str):
        super().__init__(base_url)

    def get_academic_events(self) -> List[Dict[str, str]]:
        """
        학사일정 페이지를 크롤링하여 (날짜, 내용) 형태로 반환
        """
        url = f"{self.base_url}calendar2024_list.do?mode=list&selectedYear=2025"
        root = self._fetch_html(url)
        if root is None:
            return [{"error": "HTML을 불러오지 못했습니다."}]

        # 모든 월 단위 일정 div 탐색
        month_boxes = root.xpath('//div[contains(@class, "b-cal-list-box")]/div')
        if not month_boxes:
            return [{"error": "학사일정 블록을 찾을 수 없습니다."}]

        events = []
        current_year = 2025  # 기본 시작연도

        for box in month_boxes:
            # 월/연도 정보 추출
            title = box.xpath('./p/text()')
            if not title:
                continue

            month_text = "".join(title).strip()
            year_match = re.search(r'(\d{4})년', month_text)
            month_match = re.search(r'(\d{1,2})월', month_text)

            if year_match:
                current_year = int(year_match.group(1))
            if not month_match:
                continue

            month = int(month_match.group(1))

            # 일별 일정들 파싱
            day_divs = box.xpath('./div/div')
            for div in day_divs:
                day_text = " ".join(div.xpath('./p//text()')).strip()
                event_list = div.xpath('.//ul/li')

                if not day_text or not event_list:
                    continue

                # 날짜 파싱 (예: "4(화) ~ 10(월)" or "2(금)")
                dates = re.findall(r'(\d{1,2})', day_text)
                start_date = end_date = None

                if len(dates) == 1:
                    start_date = f"{current_year}-{month:02d}-{int(dates[0]):02d}"
                elif len(dates) >= 2:
                    start_date = f"{current_year}-{month:02d}-{int(dates[0]):02d}"
                    end_date = f"{current_year}-{month:02d}-{int(dates[-1]):02d}"

                # 일정 내용 추출
                for li in event_list:
                    title_text = " ".join(li.xpath('.//text()')).strip()
                    if not title_text:
                        continue

                    # 불필요한 개행, 공백 제거
                    title_text = re.sub(r'\s+', ' ', title_text)

                    if start_date and end_date:
                        events.append({
                            "date": f"{start_date} ~ {end_date}",
                            "title": title_text
                        })
                    elif start_date:
                        events.append({
                            "date": start_date,
                            "title": title_text
                        })

        return events
