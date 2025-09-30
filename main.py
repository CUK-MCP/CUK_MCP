
from __future__ import annotations

import argparse
from contextlib import asynccontextmanager

from pathlib import Path

from app.context import AppCtx
# If you have fastmcp installed, you can uncomment imports and server creation.
try:
    from mcp.server.fastmcp import FastMCP, Context
except Exception:  # pragma: no cover
    FastMCP = None  # type: ignore

from classes.file_class import MultiBaseFileManager
from typing import List, Union


def _coerce_paths(values: List[Union[str, Path]]) -> List[Path]:
    out: List[Path] = []
    seen: set[str] = set()
    for v in values or []:
        p = v if isinstance(v, Path) else Path(str(v))
        rp = p.resolve()
        sp = str(rp)
        if sp not in seen:
            seen.add(sp)
            out.append(rp)
    return out

def make_lifespan(allowed_paths: List[Union[str, Path]]):
    @asynccontextmanager
    async def lifespan(_server: FastMCP):
        # 1) 정규화 + 중복 제거
        norm = _coerce_paths(allowed_paths)


        # 2) AppCtx 준비
        app = AppCtx(allowed_paths=norm)
        app.file_manager = MultiBaseFileManager(norm)

        try:
            # 3) dict로 감싸서 내보냄 → 툴에서 ctx.request_context.lifespan_context['app']로 접근
            yield {"app": app}
        finally:
            # TODO: 필요 시 정리 작업
            pass

    return lifespan

def create_server(allowed_paths: List[Path]):
    if FastMCP is None:
        raise RuntimeError("FastMCP not available. Install `mcp` package to run the server.")
    mcp = FastMCP("MyMCPServer", lifespan=make_lifespan(allowed_paths))

    # Example: register tools here (pseudo)
    # from tools.file_tools import register as register_file_tools
    # register_file_tools(mcp)
    # from app.tools.math_tools import register as register_math
    # register_math(mcp)
    from app.tools.file_tools import register as register_file_tools
    from app.tools.web_tools import register as register_web_tools

    register_web_tools(mcp)
    register_file_tools(mcp)

    return mcp


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", action="append", default=[], help="허용할 베이스 경로. 여러 번 지정 가능")
    args = parser.parse_args()

    allowed = [Path(p) for p in (args.path or [])] or [Path.cwd()]

    # If FastMCP is available, run server, else show a small demo.
    if FastMCP is not None:
        srv = create_server(allowed)
        srv.run()
    else:
        # Demo: initialize context & manager and do a tiny dry-run
        ctx_paths = [p.resolve() for p in allowed]
        fm = MultiBaseFileManager(ctx_paths)


        # Try listing first base root
        try:
            items = fm.listdir(base_index=0, rel=Path("."), files_only=False, max_items=20)


        except Exception as e:
            log.info(f"[Demo] listdir failed: {e}")
