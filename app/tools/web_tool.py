# app/tools/web_tool.py

from __future__ import annotations
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from classes.UniversityNoticeCrawler import UniversityNoticeCrawler
from classes.file_class import MultiBaseFileManager  # 로컬 파일 저장 시 필요


def register(mcp: FastMCP) -> None:
    """
    웹 크롤링 관련 MCP 툴들을 등록합니다.
    """

    @mcp.tool(
        name="web-get-university-notices",
        description="우리 대학교 공지사항 웹사이트의 최신 공지사항 목록을 가져옵니다."
    )
    async def web_get_university_notices(
            ctx: Context,
    ) -> List[Dict[str, Any]]:
        """
        Returns:
            각 공지사항의 제목, URL, 날짜를 담은 딕셔너리 리스트.
        """
        # category 인자 없이 호출
        crawler = UniversityNoticeCrawler(base_url="https://www.catholic.ac.kr/ko/campuslife/notice.do")

        try:
            links = crawler.get_document_links()
            return links
        except Exception as e:
            return [{"error": f"공지사항을 가져오는 데 실패했습니다: {e}"}]