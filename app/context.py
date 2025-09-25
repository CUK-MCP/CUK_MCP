# app/context.py
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from classes.file_class import MultiBaseFileManager  # 동일 폴더가 아니니 상대가 아닌 절대경로 임포트

@dataclass
class AppCtx:
    allowed_paths: List[Path] = field(default_factory=list)
    file_manager: Optional[MultiBaseFileManager] = None
