# app/tools/web_tools.py

from __future__ import annotations
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context

# --- Classes ---
from classes.UniversityNoticeCrawler_class import UniversityNoticeCrawler
from classes.AcademicCalendarCrawler_class import AcademicCalendarCrawler
from classes.GoogleCalendarAPIClient_class import GoogleCalendarAPIClient  # ✅ Google Calendar 연동 추가
from data.department_data import DEPARTMENT_URL_MAP


def register(mcp: FastMCP) -> None:
    """
    FastMCP 툴 등록 함수.
    학교 관련 공지사항, 학사일정, 학과공지, 구글캘린더 연동 기능을 모두 포함합니다.
    """

    # -----------------------------
    # 1️⃣ 대학교 공지사항
    # -----------------------------
    @mcp.tool(
        name="web-get-university-notices",
        description="""
        우리 대학교 공지사항 웹사이트에서 최신 공지사항 목록을 가져옵니다.
        '일반', '학사', '장학', '취창업' 중 특정 카테고리를 지정할 수 있습니다.
        """
    )
    async def web_get_university_notices(
        ctx: Context,
        category: Optional[str] = None,
        start_page: int = 1,
        end_page: int = 1
    ) -> List[Dict[str, Any]]:
        crawler = UniversityNoticeCrawler(base_url="https://www.catholic.ac.kr/ko/campuslife/notice.do")
        try:
            links = crawler.get_document_links(category, start_page, end_page)
            return links
        except Exception as e:
            return [{"error": f"공지사항을 가져오는 데 실패했습니다: {e}"}]

    @mcp.tool(
        name="web-get-university-notices-detail",
        description="특정 학교 공지사항의 상세 정보를 가져옵니다. (현재 프로토타입입니다.)"
    )
    async def web_get_university_notices_detail(link: str) -> Dict[str, Any]:
        crawler = UniversityNoticeCrawler(base_url="https://www.catholic.ac.kr/ko/campuslife/notice.do")
        try:
            return crawler.get_notice_detail(link)
        except Exception as e:
            return {"error": f"공지사항 상세정보를 가져오는데 실패했습니다: {e}"}

    # -----------------------------
    # 2️⃣ 학과 공지사항
    # -----------------------------
    @mcp.tool(
        name="get-department-name",
        description="입력한 학과명이 틀리거나 모호할 경우, 가능한 학과 리스트를 반환합니다."
    )
    def get_department_name():
        return DEPARTMENT_URL_MAP

    @mcp.tool(
        name="web-get-department-notices",
        description="특정 학과의 공지사항 리스트를 가져옵니다."
    )
    async def web_get_department_notices(
        department: str,
        start_page: int = 1,
        end_page: int = 1
    ) -> List[Dict[str, Any]]:
        department_url_slug = DEPARTMENT_URL_MAP.get(department)
        if not department_url_slug:
            return [{"error": f"'{department}'에 해당하는 학과를 찾을 수 없습니다."}]

        url = f"https://{department_url_slug}.catholic.ac.kr/{department_url_slug}/community/notice.do"
        crawler = UniversityNoticeCrawler(url)
        try:
            return crawler.get_document_links(start_page=start_page, end_page=end_page)
        except Exception as e:
            return [{"error": f"학과 공지사항을 가져오는데 실패했습니다: {e}"}]

    @mcp.tool(
        name="web-get-department-notices-detail",
        description="특정 학과 공지사항의 상세 정보를 가져옵니다."
    )
    async def web_get_department_notices_detail(
        link: str,
        department: str
    ) -> Dict[str, Any]:
        department_url_slug = DEPARTMENT_URL_MAP.get(department)
        if not department_url_slug:
            return {"error": f"'{department}'에 해당하는 학과를 찾을 수 없습니다."}

        url = f"https://{department_url_slug}.catholic.ac.kr/{department_url_slug}/community/notice.do"
        crawler = UniversityNoticeCrawler(url)
        try:
            return crawler.get_notice_detail(link)
        except Exception as e:
            return {"error": f"공지사항 상세정보를 가져오는데 실패했습니다: {e}"}

    # -----------------------------
    # 3️⃣ 학사일정
    # -----------------------------
    @mcp.tool(
        name="web-get-academic-events",
        description="가톨릭대학교 학사일정 정보를 가져옵니다. (2025~2026학년도)"
    )
    async def web_get_academic_events(ctx: Context) -> List[Dict[str, Any]]:
        calendar_url = "https://www.catholic.ac.kr/ko/support/"
        crawler = AcademicCalendarCrawler(base_url=calendar_url)
        try:
            events = crawler.get_academic_events()
            return events
        except Exception as e:
            return [{"error": f"학사일정을 가져오는 데 실패했습니다: {e}"}]

    # -----------------------------
    # 4️⃣ Google Calendar 연동
    # -----------------------------
    @mcp.tool(
        name="web-sync-google-calendar",
        description="가톨릭대학교 학사일정을 사용자의 Google Calendar에 자동으로 동기화합니다."
    )
    async def web_sync_google_calendar(ctx: Context) -> Dict[str, Any]:
        try:
            # 학사일정 크롤링
            calendar_url = "https://www.catholic.ac.kr/ko/support/"
            crawler = AcademicCalendarCrawler(base_url=calendar_url)
            events = crawler.get_academic_events()

            # Google Calendar에 등록
            client = GoogleCalendarAPIClient()
            result = client.sync_events(events)

            return {
                "status": "success",
                "message": f"총 {result['created']}개 생성, {result['skipped']}개 중복 건너뜀"
            }
        except Exception as e:
            return {"status": "error", "message": f"Google Calendar 동기화 실패: {e}"}
