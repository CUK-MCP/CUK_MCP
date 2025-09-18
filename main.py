# server.py
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from mcp.server.fastmcp import FastMCP

@dataclass
class AppCtx:
    # 공용 의존성 (DB, 설정 등)
    db_dsn: str = "sqlite://:memory:"

@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[AppCtx]:
    # 서버 시작 시 초기화
    ctx = AppCtx()
    try:
        yield ctx
    finally:
        # 서버 종료 시 정리
        pass

def create_server() -> FastMCP:
    mcp = FastMCP("MyMCPServer", lifespan=lifespan)

    # 기능(모듈)별 등록
    from app.tools import math_tools

    math_tools.register(mcp)
    return mcp

# mcp CLI가 찾을 전역 객체
mcp = create_server()

if __name__ == "__main__":
    # 직접 실행도 가능(기본 stdio). 필요 시 transport 지정 가능.
    mcp.run()
