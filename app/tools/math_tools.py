# app/tools/math_tools.py
from mcp.server.fastmcp import FastMCP

def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def add(a: int, b: int) -> int:
        """두 수를 더한다"""
        return a + b

    @mcp.tool()
    def sub(a: int, b: int) -> int:
        """두 수를 뺀다"""
        print("test")
        return a - b
