
from __future__ import annotations

import argparse
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import List
from app.context import AppCtx
# If you have fastmcp installed, you can uncomment imports and server creation.
try:
    from mcp.server.fastmcp import FastMCP
except Exception:  # pragma: no cover
    FastMCP = None  # type: ignore

from classes.file_class import MultiBaseFileManager


def make_lifespan(allowed_paths: List[Path]):
    @asynccontextmanager
    async def lifespan(_server):
        # Normalize & de-duplicate
        norm = []
        seen = set()
        for p in allowed_paths:
            rp = p.resolve()
            sp = str(rp)
            if sp not in seen:
                seen.add(sp)
                norm.append(rp)

        ctx = AppCtx(allowed_paths=norm)
        # Initialize shared file manager
        ctx.file_manager = MultiBaseFileManager(norm)

        try:
            yield ctx
        finally:
            # Place for cleanup (close watchers, caches, etc.)
            pass

    return lifespan

def create_server(allowed_paths: List[Path]):
    if FastMCP is None:
        raise RuntimeError("FastMCP not available. Install `mcp` package to run the server.")
    mcp = FastMCP("MyMCPServer", lifespan=make_lifespan(allowed_paths))

    # Example: register tools here (pseudo)
    # from tools.file_tools import register as register_file_tools
    # register_file_tools(mcp)
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
        print("[Demo] Allowed roots:")
        for i, b in enumerate(ctx_paths):
            print(f"  [{i}] {b}")
        # Try listing first base root
        try:
            items = fm.listdir(base_index=0, rel=Path("."), files_only=False, max_items=20)
            print(f"[Demo] listdir({ctx_paths[0]}) -> {len(items)} items (showing up to 5):")
            for it in items[:5]:
                print(f"   - {it['type']:>3} | {it['relpath']}")
        except Exception as e:
            print(f"[Demo] listdir failed: {e}")
