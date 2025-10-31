from __future__ import annotations
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP, Context
import requests
def register(mcp: FastMCP) -> None:
    @mcp.tool(
        name="backend",
        description="""
            백엔드에 요청을 보냅니다
            """
    )
    async def getreq(
    ) -> list[Dict[str, Any]]:
        BASE_URL = "http://127.0.0.1:8000/timetable/list?department=컴퓨터정보공학부&ctype=제1전공선택"
        # 1️⃣ GET 요청
        response = requests.get(f"{BASE_URL}")
        return response.json()

