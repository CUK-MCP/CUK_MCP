# app/tools/web_tool.py

from __future__ import annotations
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from classes.UniversityNoticeCrawler_class import UniversityNoticeCrawler
from classes.file_class import MultiBaseFileManager  # 로컬 파일 저장 시 필요
from data.department_data import DEPARTMENT_URL_MAP
global_department = ""
def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="web-get-university-notices",
        description="""
        우리 대학교 공지사항 웹사이트에서 최신 공지사항 목록을 가져옵니다.
        '일반', '학사', '장학', '취창업' 중 특정 카테고리를 지정할 수 있습니다.
        page는 공지사항의 몇번째 페이지를 부를 지 지정합니다.
        """
    )
    async def web_get_university_notices(
            ctx: Context,
            category: Optional[str] = None,
            start_page: int = 1,
            end_page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Args:
            category: '일반', '학사', '장학', '취창업' 중 하나. None이면 전체 목록.
            start_page: 몇번째 페이지부터 정보를 불러 올지 지정.
            end_page: 몇번째 페이지까지 정보를 불러 올지 지정.(지정하지 않는다면 디폴트)
        Returns:
            각 공지사항의 제목, URL, 날짜를 담은 딕셔너리 리스트.
        """
        crawler = UniversityNoticeCrawler(base_url="https://www.catholic.ac.kr/ko/campuslife/notice.do")

        try:
            links = crawler.get_document_links(category,start_page,end_page)
            return links
        except Exception as e:
            return [{"error": f"공지사항을 가져오는 데 실패했습니다: {e}"}]

    @mcp.tool(name="web-get-university-notices_detail",
              description="원하는 페이지에 상세 정보를 가져옵니다.(현재 프로토타입입니다) 텍스트가 많이 없을 수 있습니다")
    async def web_get_university_notices_detail(link: str) -> Dict[str, Any]:
        """
        :param link: 원하는 페이지의 href를 입력
        :return: {"content" : "공지사항의 세부사항"}
        """
        crawler = UniversityNoticeCrawler(base_url="https://www.catholic.ac.kr/ko/campuslife/notice.do")

        try:
            return crawler.get_notice_detail(link)
        except Exception as e:
            return {"error": f"공지사항을 가져오는데 실패했습니다: {e}"}

    @mcp.tool(name="get-department-name",
              description="""
              사용자가 입력한 학과명이 틀리거나 모호 할 경우 리스트를 꺼내 확인할 수 있습니다.
              """)
    def get_department_name():
        return DEPARTMENT_URL_MAP

    @mcp.tool(
        name="web-get-department-notices",
        description="""
            특정 학과 공지사항 리스트를 가져옵니다.
            """
    )
    async def web_get_department_notices(
            department: str,
            start_page: int = 1,
            end_page: int = 1
    ) -> list[Dict[str, Any]]:
        """

        :param department: 학과 문자열
        :param start_page: 시작페이지
        :param end_page: 끝 페이지
        :return: 공지사항 리스트
        """
        department_url_slug = DEPARTMENT_URL_MAP.get(department)
        global_department = department
        if not department_url_slug:
            return [{"error": f"'{department}'에 해당하는 학과를 찾을 수 없습니다."}]
        url = f"https://{department_url_slug}.catholic.ac.kr/{department_url_slug}/community/notice.do"
        # DepartmentNoticeCrawler 인스턴스를 생성할 때 학과 슬러그를 전달합니다.
        crawler = UniversityNoticeCrawler(url)
        try:
            return crawler.get_document_links(start_page = start_page,end_page= end_page)
        except Exception as e:
            return [{"error": f"공지사항을 가져오는데 실패했습니다: {e}"}]
    @mcp.tool(name="web-get-department-notices-detail",
              description="""
              학과 공지사항의 상세정보를 가져옵니다
              """)
    async def web_get_department_notices_detail(
            link: str,
            department: str = global_department
    ) -> Dict[str, Any]:
        """

        :param link: 원하는 페이지의 href를 입력
        :param department: 공지사항을 불러왔을때 입력했을경우 입력 할 필요 없음
        :return: {"content" : "공지사항의 세부사항"}
        """
        department_url_slug = DEPARTMENT_URL_MAP.get(department)
        url = f"https://{department_url_slug}.catholic.ac.kr/{department_url_slug}/community/notice.do"
        if not department_url_slug:
            return {"error": f"'{department}'에 해당하는 학과를 찾을 수 없습니다."}

        # DepartmentNoticeCrawler 인스턴스를 생성할 때 학과 슬러그를 전달합니다.
        crawler = UniversityNoticeCrawler(url)

        try:
            return crawler.get_notice_detail(link)
        except Exception as e:
            return {"error": f"공지사항을 가져오는 데 실패했습니다: {e}"}
