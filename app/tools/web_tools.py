from __future__ import annotations
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from classes.UniversityNoticeCrawler_class import UniversityNoticeCrawler
from classes.DepartmentNoticeCrawler_class import DepartmentNoticeCrawler
from classes.department_data import DEPARTMENT_URL_MAP
from classes.file_class import MultiBaseFileManager  # 로컬 파일 저장 시 필요


def register(mcp: FastMCP) -> None:
    # 기존 학교 공지사항 도구
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
        # ... (기존 코드와 동일)
        crawler = UniversityNoticeCrawler(base_url="https://www.catholic.ac.kr/ko/campuslife/notice.do")
        try:
            links = crawler.get_document_links(category, start_page, end_page)
            return links
        except Exception as e:
            return [{"error": f"공지사항을 가져오는 데 실패했습니다: {e}"}]

    # 기존 학교 공지사항 상세정보 도구
    @mcp.tool(name="web-get-university-notices_detail",
              description="원하는 페이지에 상세 정보를 가져옵니다.(현재 프로토타입입니다) 텍스트가 많이 없을 수 있습니다")
    async def web_get_university_notices_detail(link: str) -> Dict[str, Any]:
        # ... (기존 코드와 동일)
        crawler = UniversityNoticeCrawler(base_url="https://www.catholic.ac.kr/ko/campuslife/notice.do")
        try:
            return crawler.get_notice_detail(link)
        except Exception as e:
            return {"error": f"공지사항을 가져오는 데 실패했습니다: {e}"}

    # ★ 새로 추가할 학과 공지사항 도구
    @mcp.tool(
        name="web-get-department-notices_detail",
        description="""
        특정 학과 공지사항의 상세 내용을 가져옵니다.
        """
    )
    async def web_get_department_notices_detail(
            link: str,
            department: str
    ) -> Dict[str, Any]:
        department_url_slug = DEPARTMENT_URL_MAP.get(department)

        if not department_url_slug:
            return {"error": f"'{department}'에 해당하는 학과를 찾을 수 없습니다."}

        # DepartmentNoticeCrawler 인스턴스를 생성할 때 학과 슬러그를 전달합니다.
        crawler = DepartmentNoticeCrawler(department_url_slug)

        try:
            return crawler.get_notice_detail(link)
        except Exception as e:
            return {"error": f"공지사항을 가져오는 데 실패했습니다: {e}"}