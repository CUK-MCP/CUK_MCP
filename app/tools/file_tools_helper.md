# README — MCP 파일 툴 & 파일 매니저 (업데이트)

## 서버에 등록되는 MCP 툴

### file-listdir
- 지정한 경로 하위의 **파일/폴더 목록**을 반환
- glob 패턴(`*.pptx` 등) 필터링 가능
- 옵션
  - `dirs_only=true` → 폴더만
  - `files_only=true` → 파일만
  - 둘 다 false(기본) → 파일/폴더 모두

---

### file-list-candidates
- 폴더 내 파일 수가 threshold 이하(기본 100)면 전체 반환
- 초과하면 퍼지 매칭 Top-K만 반환
- 폴더가 클 때, 파일명이 애매할 때 사용

---

### file-read-text
- PDF, PPTX, DOCX, TXT, MD 텍스트 추출
- 슬라이딩 청크 분할 및 캐시 지원
- 경로가 틀리면 퍼지 복구 시도
- 주요 옵션: `do_chunk`, `chunk_size`, `overlap`, `auto_fuzzy`

---

### file-make-dirs
- 여러 개의 폴더를 한 번에 생성
- `parent_rel` 아래에 `names[]` 각각 생성
- 하위 경로 포함 가능

---

### file-move-files
- 하나 이상의 파일을 다른 폴더로 이동(잘라넣기)
- 내부적으로 클래스 `move_many` 사용 → 덮어쓰기, 고유이름 자동부여, 검증 정책 일관 적용
- 파라미터
  - `items`: 단일 dict 또는 배열
    - 필수: `src_base_index|base_index`, `src_rel|src_rel_path|rel_path` 또는 `src_dir|dir + src_name|name`
    - 선택: `new_name`
  - `dst_base_index`: 생략 가능 (첫 항목 src_base_index 사용)
  - `dst_folder_rel`: 기본 `"."`
  - `overwrite`, `create_dst`, `dry_run`, `on_error("continue"|"stop")`
- 단일/배치 모두 지원
- 레거시 키(`base_index`, `rel_path`)도 자동 정규화

---

## 내부 파일 매니저

### MultiBaseFileManager
- 여러 허용 루트(샌드박스) 기반의 안전 경로 처리
- 디렉터리 나열, 퍼지 탐색, 문서 추출(청크/캐시) 제공
- MCP 툴들이 모두 이 클래스를 통해 파일 접근/이동/생성 수행

---

## 추천 사용 흐름
1. 폴더 상태 파악 → file-listdir (dirs_only로 폴더만 볼 수도 있음)  
2. 파일이 많음 → file-list-candidates로 후보 추출  
3. 이동/정리 → file-make-dirs 후 file-move-files  
4. 읽기/요약 → file-read-text (퍼지 복구 자동)

---

## 지원 포맷(텍스트 추출)
- PDF, PPTX, DOCX, TXT, MD

---

## 한 줄 요약
- 탐색: file-listdir / file-list-candidates  
- 정리: file-make-dirs / file-move-files  
- 읽기: file-read-text  
- 안전·퍼지·청크·캐시: MultiBaseFileManager가 책임짐
