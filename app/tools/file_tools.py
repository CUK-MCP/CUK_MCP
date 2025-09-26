
from __future__ import annotations

import fnmatch
from typing import Any, Dict, List, Optional, Tuple
from app.context import AppCtx
from classes.file_class import MultiBaseFileManager  # <-- user's path
from mcp.server.fastmcp import FastMCP, Context
# ---------- helpers ----------

from pathlib import Path

def _coerce_paths(values):
    out = []
    for v in (values or []):
        out.append(v if isinstance(v, Path) else Path(str(v)))
    return [p.resolve() for p in out]

def _get_app_ctx(ctx: Context) -> AppCtx:
    lc = getattr(ctx.request_context, "lifespan_context", None)
    # 우리가 lifespan에서 yield {"app": app} 형태로 보냈다고 가정
    if isinstance(lc, dict) and isinstance(lc.get("app"), AppCtx):
        return lc["app"]
    # 혹시 그냥 AppCtx를 바로 yield했다면 이것도 허용
    if isinstance(lc, AppCtx):
        return lc
    # 디버그 로그

    raise RuntimeError("lifespan_context에 AppCtx가 없습니다. lifespan yield를 확인하세요.")

def _get_manager(ctx: Context) -> MultiBaseFileManager:
    app = _get_app_ctx(ctx)
    if getattr(app, "file_manager", None) is None:
        bases = [p if isinstance(p, Path) else Path(str(p)) for p in (app.allowed_paths or [])]
        bases = [p.resolve() for p in bases]
        app.file_manager = MultiBaseFileManager(bases)
    return app.file_manager

def _split_rel(rel_path: str) -> Tuple[str, str, str]:
    """Return (dir, stem, ext) for a relative path string."""
    p = Path(rel_path)
    return (str(p.parent).replace("\\\\", "/"), p.stem, p.suffix.lower())

def _fuzzy_pick_file(
    fm: MultiBaseFileManager,
    base_index: int,
    rel_dir: str,
    fuzzy_name: str,
    glob: Optional[str] = None,
    cutoff: float = 0.6,
    topk: int = 5,
) -> Dict[str, Any]:
    """
    List files under rel_dir, optionally filter by glob (e.g., '*.pptx'),
    then fuzzy-match by name (stem). Return best and candidates.
    """
    items = fm.listdir(base_index=base_index, rel=Path(rel_dir or "."), files_only=True, max_items=1000)
    if glob:
        items = [it for it in items if fnmatch.fnmatch(it["name"], glob)]
    from difflib import SequenceMatcher
    q = (fuzzy_name or "").strip().lower()
    scored: List[Dict[str, Any]] = []
    for it in items:
        stem = Path(it["name"]).stem.lower()
        s = SequenceMatcher(None, q, stem).ratio() if q else 0.0
        if stem == q:
            s += 0.30
        elif stem.startswith(q):
            s += 0.15
        elif q and q in stem:
            s += 0.10
        it2 = dict(it)
        it2["score"] = round(min(1.0, s), 3)
        scored.append(it2)
    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:topk]
    if not top:
        return {"found": False, "candidates": []}
    if top[0]["score"] >= 0.75 and (len(top) == 1 or top[0]["score"] - top[1]["score"] >= 0.1):
        return {"found": True, "best": top[0], "candidates": top}
    return {"found": "ambiguous", "candidates": top}

# ---------- registration ----------

def register(mcp: FastMCP, enable_legacy: bool = False) -> None:
    """
    파일 관련 MCP 툴들을 등록합니다.
    포함: file-read-text (자동 퍼지 폴백), file-find-folder, file-listdir, file-find-file
    (툴 이름은 ^[a-zA-Z0-9_-]{1,64}$ 규칙을 만족해야 하므로 '.'(dot) 금지)
    """

    @mcp.tool(
        name="file-listdir",
        description="특정 베이스/상대 경로 하위의 파일/폴더 목록을 반환합니다. glob로 필터링할 수 있습니다(예: '*.pptx')."
    )
    async def file_listdir(
            ctx: Context,
            base_index: int = 0,
            rel_path: Optional[str] = None,
            files_only: bool = False,
            max_items: int = 500,
            glob: Optional[str] = None,
    ) -> Dict[str, Any]:
        fm = _get_manager(ctx)
        try:
            items = fm.listdir(base_index=base_index, rel=Path(rel_path or "."), files_only=files_only,
                               max_items=max_items)
            if glob:
                items = [it for it in items if fnmatch.fnmatch(it["name"], glob)]
            base = str(fm.allowed[base_index])
            directory = str((fm.allowed[base_index] / (rel_path or ".")).resolve())
            return {"items": items, "base": base, "directory": directory}
        except FileNotFoundError as e:
            return {"error": f"경로를 찾을 수 없습니다: {e}"}
        except PermissionError as e:
            return {"error": f"권한 오류: {e}"}
        except Exception as e:
            return {"error": f"목록 실패: {e}"}

    @mcp.tool(
        name="file-list-candidates",
        description=(
            "지정 폴더의 파일 후보를 반환합니다. "
            "폴더 내 파일 수가 threshold(기본 100) 초과면 fuzzy Top-K만, "
            "그 이하면 전체 목록을 반환합니다. LLM이 최종 선택하세요."
        )
    )
    async def file_list_candidates(
        ctx: Context,
        base_index: int,
        rel_dir: str = "",
        query_name: str = "",          # 사용자가 말한 대략적 파일명(없어도 됨)
        glob: Optional[str] = None,    # 예: '*.pptx'
        threshold: int = 100,          # 100개 기준 분기
        fuzzy_topk: int = 20           # 퍼지일 때 후보 상한
    ) -> Dict[str, Any]:
        fm = _get_manager(ctx)

        # 1) 폴더 나열
        items = fm.listdir(
            base_index=base_index,
            rel=Path(rel_dir or "."),
            files_only=True,
            max_items=10_000  # 내부 상한(안전빵) — 실제 반환은 분기 아래에서 조절
        )

        # 2) 확장자/패턴 필터
        if glob:
            items = [it for it in items if fnmatch.fnmatch(it["name"], glob)]

        total = len(items)

        # 3) 분기
        if total <= threshold:
            # 전체 파일을 그대로 전달 (LLM이 선택)
            slim = [
                {
                    "name": it["name"],
                    "rel": it.get("rel", it["name"]),
                    "ext": Path(it["name"]).suffix.lower(),
                    "mtime": it.get("mtime"),
                    "size": it.get("size"),
                }
                for it in items
            ]
            return {
                "strategy": "all",
                "total": total,
                "items": slim,
                "base_index": base_index,
                "rel_dir": rel_dir,
                "note": (
                    f"파일이 {total}개로 threshold({threshold}) 이하입니다. "
                    "LLM은 items에서 가장 적절한 파일 1개를 골라, "
                    "그 파일명을 rel_path로 하여 file-read-text를 호출하세요."
                )
            }

        # total > threshold → 퍼지 후보만 반환
        fuzzy = _fuzzy_pick_file(
            fm=fm,
            base_index=base_index,
            rel_dir=rel_dir,
            fuzzy_name=query_name or "",
            glob=glob,
            cutoff=0.0,          # 컷오프 낮게(후보는 topk로 자름)
            topk=fuzzy_topk
        )

        cand = [
            {
                "name": c["name"],
                "rel": c.get("rel", c["name"]),
                "score": c.get("score", 0.0),
                "ext": Path(c["name"]).suffix.lower(),
                "mtime": c.get("mtime"),
                "size": c.get("size"),
            }
            for c in fuzzy.get("candidates", [])
        ]

        return {
            "strategy": "fuzzy",
            "total": total,
            "candidates": cand,
            "base_index": base_index,
            "rel_dir": rel_dir,
            "note": (
                f"파일이 {total}개로 threshold({threshold}) 초과입니다. "
                "LLM은 candidates에서 가장 적절한 파일 1개를 고르세요. "
                "만약 비슷한 파일명이 없다고 판단하면 사용자에게 "
                "‘폴더에 파일이 너무 많고 요청하신 파일명과 비슷한 파일이 없습니다’라고 안내해 주세요."
            )
        }

    @mcp.tool(
        name="file-read-text",
        description="PDF/PPTX/DOCX/TXT/MD 파일에서 텍스트를 추출합니다. (상대경로 또는 절대경로로 지정) 자동 퍼지 폴백을 지원합니다."
    )
    async def file_read_text(
        ctx: Context,
        base_index: int = 0,
        rel_path: Optional[str] = None,
        absolute_path: Optional[str] = None,
        do_chunk: bool = True,
        chunk_size: int = 1200,
        overlap: int = 150,
        auto_fuzzy: bool = True,
        do_text: bool = False
    ) -> Dict[str, Any]:
        fm = _get_manager(ctx)

        def _as_payload(res) -> Dict[str, Any]:
            payload: Dict[str, Any] = {
                "metadata": res.metadata,
                "source": res.metadata.get("source"),
            }
            if do_text:
                payload["text"] = res.text
            if do_chunk:
                payload["chunks"] = res.chunks or []
            return payload

        try:
            if absolute_path:
                res = fm.extract_absolute(Path(absolute_path), do_chunk=do_chunk, chunk_size=chunk_size, overlap=overlap)
                return _as_payload(res)

            if rel_path is None:
                raise ValueError("absolute_path 또는 rel_path 중 하나를 제공해야 합니다.")

            # 1차 시도
            try:
                res = fm.extract_from(base_index, Path(rel_path), do_chunk=do_chunk, chunk_size=chunk_size, overlap=overlap)
                return _as_payload(res)
            except FileNotFoundError as e:
                if not auto_fuzzy:
                    raise

                # 자동 퍼지 복구
                rel_dir, stem, ext = _split_rel(rel_path)
                glob = None
                if ext in {".pptx", ".ppt", ".pdf", ".docx", ".txt", ".md"}:
                    glob = f"*{ext}"

                fuzzy = _fuzzy_pick_file(fm, base_index, rel_dir, stem, glob=glob, cutoff=0.6, topk=5)
                if fuzzy.get("found") is True and "best" in fuzzy:
                    best = fuzzy["best"]
                    fixed_rel = str(Path(rel_dir) / best["name"]) if rel_dir else best["name"]
                    res2 = fm.extract_from(base_index, Path(fixed_rel), do_chunk=do_chunk, chunk_size=chunk_size, overlap=overlap)
                    res2.metadata["resolved_from"] = rel_path
                    return _as_payload(res2)
                elif fuzzy.get("found") == "ambiguous":
                    return {
                        "error": "ambiguous",
                        "message": "정확한 파일을 찾지 못했습니다. 후보 중에서 선택하세요.",
                        "candidates": fuzzy.get("candidates", []),
                        "base_index": base_index,
                        "rel_dir": rel_dir,
                        "requested": rel_path,
                    }
                else:
                    raise FileNotFoundError(e)

        except FileNotFoundError as e:
            return {"error": f"파일을 찾을 수 없습니다: {e}"}
        except PermissionError as e:
            return {"error": f"권한 오류: {e}"}
        except ValueError as e:
            return {"error": f"요청 오류: {e}"}
        except Exception as e:
            return {"error": f"추출 실패: {e}"}
    if enable_legacy:
        @mcp.tool(
            name="file-find-folder",
            description="여러 베이스 경로에서 폴더명을 퍼지 매칭으로 찾아 Top-K 후보를 반환합니다."
        )
        async def file_find_folder(
            ctx: Context,
            name: str,
            max_depth: int = 2,
            topk: int = 5,
        ) -> Dict[str, Any]:
            fm = _get_manager(ctx)
            try:
                return fm.find_folder(name, max_depth=max_depth, topk=topk)
            except PermissionError as e:
                return {"error": f"권한 오류: {e}"}
            except Exception as e:
                return {"error": f"탐색 실패: {e}"}


        @mcp.tool(
            name="file-find-file",
            description="지정한 폴더(rel_dir) 안에서 fuzzy 이름 매칭으로 파일을 찾아 Top-K를 반환합니다(선택적으로 glob 필터 사용)."
        )
        async def file_find_file(
            ctx: Context,
            base_index: int,
            rel_dir: str,
            fuzzy_name: str,
            glob: Optional[str] = None,
            topk: int = 5,
        ) -> Dict[str, Any]:
            fm = _get_manager(ctx)
            try:
                return _fuzzy_pick_file(fm, base_index, rel_dir, fuzzy_name, glob=glob, cutoff=0.6, topk=topk)
            except FileNotFoundError as e:
                return {"error": f"경로를 찾을 수 없습니다: {e}"}
            except PermissionError as e:
                return {"error": f"권한 오류: {e}"}
            except Exception as e:
                return {"error": f"파일 탐색 실패: {e}"}
