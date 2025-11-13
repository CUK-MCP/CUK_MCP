from __future__ import annotations
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
from data.ctype_data import CTYPE_DATA
import requests
def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="get_timetable",
        description="""
            원하는 시간표를 가져옵니다.
            """
    )
    async def get_timetable(department: str, ctype: str) -> list[Dict[str, Any]]:
        """

        :param department: 학과명
        :param ctype: 이수구분
        :return: 수업 리스트
        """
        BASE_URL = f"http://127.0.0.1:8000/timetable/list?department={department}&ctype={ctype}"
        # 1️⃣ GET 요청
        response = requests.get(f"{BASE_URL}")
        return response.json()
    @mcp.tool(
        name="get_ctype",
        description = """
        이수구분을 검색합니다.
        """
    )
    def get_ctype() -> list:
        return CTYPE_DATA

