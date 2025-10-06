
from __future__ import annotations
"""
SeleniumFlowRunner: 로그인/클릭 네비게이션 중심의 비동기 시나리오 실행기
- 로그인 → 다중 클릭/입력 → 파일 다운로드 트리거까지 "행동 시퀀스"를 선언적으로 기술
- 즉시 반환(job_id) + 상태 폴링(get_status)
- 실패 내성(retry), 명시적 대기(wait), 어설션(expect) 지원

의존성
- selenium>=4.24
- (옵션) webdriver-manager>=4.0

보안
- 자격증명은 코드에 하드코딩하지 말고: 환경변수/시크릿 볼트/MCP secure param 사용 권장
"""
"""
SeleniumFlowRunner: 로그인/클릭 네비게이션 중심의 비동기 시나리오 실행기
- 로그인 → 다중 클릭/입력 → 파일 다운로드 트리거까지 "행동 시퀀스"를 선언적으로 기술
- 즉시 반환(job_id) + 상태 폴링(get_status)
- 실패 내성(retry), 명시적 대기(wait), 어설션(expect) 지원

의존성
- selenium>=4.24
- (옵션) webdriver-manager>=4.0

보안
- 자격증명은 코드에 하드코딩하지 말고: 환경변수/시크릿 볼트/MCP secure param 사용 권장
"""
import os
import time
import uuid
import hashlib
import threading
import concurrent.futures as cf
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

# from webdriver_manager.chrome import ChromeDriverManager


# ----------------- 모델 -----------------
class JobState:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class Act(str, Enum):
    GOTO = "goto"            # url로 이동
    CLICK = "click"          # 셀렉터 클릭
    TYPE = "type"            # 셀렉터 입력
    WAIT_VISIBLE = "wait_visible"  # 요소가 보일 때까지 대기
    WAIT_CLICKABLE = "wait_clickable"# 요소가 클릭 가능해질 때까지 대기
    WAIT_URL_CONTAINS = "wait_url_contains"
    WAIT_INVISIBLE = "wait_invisible"
    SLEEP = "sleep"          # 고정 시간 대기(불가피할 때만)
    EXEC_JS = "exec_js"      # JS 실행
    EXPECT_TEXT = "expect_text"      # 요소 텍스트 포함 어설션
    SCREENSHOT = "screenshot"        # 스크린샷 저장
    # 필요 시 확장: SELECT, HOVER, SCROLL, UPLOAD 등


@dataclass
class Step:
    act: Act
    value: Optional[str] = None           # url, 텍스트, js 코드, url substring 등
    selector: Optional[str] = None        # CSS 선택자
    wait_sec: int = 20                    # 개별 스텝 대기시간
    retry: int = 0                        # 스텝 재시도 횟수
    optional: bool = False                # 선택 스텝이면 실패 시 건너뜀



@dataclass
class DownloadResult:
    file_path: Optional[Path] = None
    file_size: Optional[int] = None
    sha256: Optional[str] = None


@dataclass
class FlowJob:
    job_id: str
    out_dir: Path
    created_at: float = field(default_factory=time.time)
    state: str = JobState.PENDING
    message: str = ""
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    steps: List[Step] = field(default_factory=list)
    result: Optional[DownloadResult] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "message": self.message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "out_dir": str(self.out_dir),
            "result": None if not self.result else {
                "file_path": str(self.result.file_path) if self.result.file_path else None,
                "file_size": self.result.file_size,
                "sha256": self.result.sha256,
            },
        }


# ----------------- 실행기 -----------------
class SeleniumFlowRunner:
    def __init__(
        self,
        download_root: Path | str,
        headless: bool = False,
        max_workers: int = 2,
        page_wait: int = 30,
        download_timeout: int = 600,
        default_wait: int = 20,
    ) -> None:
        self.download_root = Path(download_root)
        self.download_root.mkdir(parents=True, exist_ok=True)
        self.headless = headless
        self.page_wait = page_wait
        self.download_timeout = download_timeout
        self.default_wait = default_wait

        self._executor = cf.ThreadPoolExecutor(max_workers=max_workers)
        self._jobs: Dict[str, FlowJob] = {}
        self._cancel_flags: Dict[str, threading.Event] = {}

    # ---------- Public API ----------
    def start_flow(self, steps: List[Step], out_subdir: Optional[str] = None) -> str:
        job_id = uuid.uuid4().hex
        out_dir = self.download_root / (out_subdir or "") / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        job = FlowJob(job_id=job_id, out_dir=out_dir, steps=steps)
        self._jobs[job_id] = job
        flag = threading.Event()
        self._cancel_flags[job_id] = flag
        self._executor.submit(self._run, job, flag)
        return job_id

    def get_status(self, job_id: str) -> Dict[str, Any]:
        job = self._jobs.get(job_id)
        return job.to_dict() if job else {"error": "job not found", "job_id": job_id}

    def cancel(self, job_id: str) -> Dict[str, Any]:
        flag = self._cancel_flags.get(job_id)
        job = self._jobs.get(job_id)
        if not job:
            return {"error": "job not found", "job_id": job_id}
        if flag:
            flag.set()
            return {"ok": True, "job_id": job_id}
        return {"ok": False, "job_id": job_id, "message": "no cancel flag"}

    def list_jobs(self) -> Dict[str, Any]:
        return {"jobs": [j.to_dict() for j in self._jobs.values()]}

    # ---------- Internals ----------
    def _build_driver(self, dl_dir: Path) -> webdriver.Chrome:
        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")

        prefs = {
            "download.default_directory": str(dl_dir.resolve()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        opts.add_experimental_option("prefs", prefs)
        # driver = webdriver.Chrome(ChromeDriverManager().install(), options=opts)
        driver = webdriver.Chrome(options=opts)
        driver.set_page_load_timeout(self.page_wait)
        driver.set_script_timeout(self.page_wait)
        opts.add_experimental_option("detach", True)
        return driver

    def _run(self, job: FlowJob, cancel: threading.Event) -> None:
        job.state = JobState.RUNNING
        job.started_at = time.time()
        driver = None
        try:
            driver = self._build_driver(job.out_dir)
            for step in job.steps:
                if cancel.is_set():
                    job.state = JobState.CANCELED
                    job.message = "canceled by user"
                    return
                self._exec_step(driver, job, step)

            # (옵션) 다운로드 결과 추출: 가장 최신 파일 1개와 해시 계산
            res = self._detect_latest_file(job.out_dir)
            job.result = res
            job.state = JobState.SUCCESS
            job.message = "ok"
        except Exception as e:
            job.state = JobState.FAILED
            job.message = f"{type(e).__name__}: {e}"
        finally:
            job.finished_at = time.time()
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass

    # 한 스텝 실행
    def _exec_step(self, driver: webdriver.Chrome, job: FlowJob, step: Step) -> None:
        wait = WebDriverWait(driver, step.wait_sec or self.default_wait)

        def _with_retry(fn, retry: int):
            last_err = None
            for _ in range(retry + 1):
                try:
                    return fn()
                except Exception as e:
                    last_err = e
                    time.sleep(0.5)
            raise last_err

        def _wait_invisible():
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, step.selector)))

        def _click():
            el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, step.selector)))
            el.click()

        def _type():
            el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, step.selector)))
            el.clear()
            el.send_keys(step.value or "")

        def _wait_visible():
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, step.selector)))

        def _wait_clickable():
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, step.selector)))

        def _wait_url_contains():
            wait.until(EC.url_contains(step.value or ""))

        def _sleep():
            time.sleep(float(step.value or 1))

        def _exec_js():
            driver.execute_script(step.value or "")

        def _expect_text():
            el = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, step.selector)))
            text = el.text or ""
            kw = step.value or ""
            if kw not in text:
                raise AssertionError(f"expect_text: '{kw}' not in element text")

        def _screenshot():
            p = job.out_dir / f"{int(time.time()*1000)}.png"
            driver.save_screenshot(str(p))

        action_map = {
            Act.GOTO: lambda: driver.get(step.value or ""),
            Act.CLICK: _click,
            Act.TYPE: _type,
            Act.WAIT_VISIBLE: _wait_visible,
            Act.WAIT_CLICKABLE: _wait_clickable,
            Act.WAIT_URL_CONTAINS: _wait_url_contains,
            Act.SLEEP: _sleep,
            Act.EXEC_JS: _exec_js,
            Act.EXPECT_TEXT: _expect_text,
            Act.SCREENSHOT: _screenshot,
            Act.WAIT_INVISIBLE: _wait_invisible,
        }
        fn = action_map.get(step.act)
        if not fn:
            raise ValueError(f"unsupported act: {step.act}")

        try:
            _with_retry(fn, step.retry)
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
            if step.optional:
                # 선택 스텝이면 실패를 무시하고 다음 단계로 진행
                return
            raise

        # 최신 파일 추정(선택)
    def _detect_latest_file(self, folder: Path) -> DownloadResult:
        files = [p for p in folder.glob("**/*") if p.is_file() and not p.name.endswith(".crdownload")]
        if not files:
            return DownloadResult()
        latest = max(files, key=lambda p: p.stat().st_mtime)
        return DownloadResult(
            file_path=latest,
            file_size=latest.stat().st_size,
            sha256=self._sha256(latest),
        )

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

# ----------------- 사용 예시 -----------------
if __name__ == "__main__":
    runner = SeleniumFlowRunner(download_root=Path.cwd() / "flows")

    USER = os.getenv("SITE_USER", "") or "kimho9270"
    PASS = os.getenv("SITE_PASS", "") or "kim66859270@"

    steps = [
        Step(Act.GOTO, value="https://uportal.catholic.ac.kr/sso/jsp/sso/ip/login_form.jsp"),
        Step(Act.WAIT_VISIBLE, selector="#userId"),
        Step(Act.TYPE, selector="#userId", value=USER),
        Step(Act.TYPE, selector="#password", value=PASS),
        Step(Act.CLICK, selector="button.n-form"),
        Step(Act.WAIT_VISIBLE, selector="#devloadingBar", wait_sec=2, optional=True),
        Step(Act.WAIT_INVISIBLE, selector="#devloadingBar", wait_sec=30),
        Step(Act.GOTO, value="https://uportal.catholic.ac.kr/stw/scsr/scoo/scooOpsbOpenSubjectInq.do"),
        Step(Act.WAIT_VISIBLE, selector="#devloadingBar", wait_sec=2, optional=True),
        Step(Act.WAIT_INVISIBLE, selector="#devloadingBar", wait_sec=30),
        Step(Act.WAIT_CLICKABLE, selector='[onclick="$.scooOpsbOpenSubjectInq.excelDownload();"]'),
        Step(Act.CLICK, selector='[onclick="$.scooOpsbOpenSubjectInq.excelDownload();"]'),
        # Step(Act.WAIT_VISIBLE, selector=".n-form.devClose", wait_sec=10),
        # Step(Act.WAIT_CLICKABLE, selector=".n-form.devClose", wait_sec=10),
        # Step(Act.CLICK, selector=".n-form.devClose"),
        # Step(Act.WAIT_VISIBLE, selector=".devMenuA", wait_sec=5),
        # Step(Act.WAIT_CLICKABLE, selector=".devMenuA", wait_sec=5),
        # Step(Act.CLICK, selector=".devMenuA"),
        # Step(Act.WAIT_VISIBLE, selector="#devloadingBar", wait_sec=2, optional=True),
        # Step(Act.WAIT_INVISIBLE, selector="#devloadingBar", wait_sec=30),
        # Step(Act.WAIT_VISIBLE, selector="a.devMenuA:nth-of-type(3)", wait_sec=5),
        # Step(Act.WAIT_CLICKABLE, selector="a.devMenuA:nth-of-type(3)", wait_sec=5),
        # Step(Act.CLICK, selector="a.devMenuA:nth-of-type(3)"),
        # Step(Act.CLICK, selector="a.downloads"),
        # Step(Act.WAIT_CLICKABLE, selector="button#export"),
        # Step(Act.CLICK, selector="button#export"),
        # # 필요 시: Step(Act.SCREENSHOT), Step(Act.EXPECT_TEXT, selector=".toast", value="내보내기 시작")
        # Step(Act.SLEEP, value="2"),  # 불가피한 지연만 짧게
    ]

    jid = runner.start_flow(steps, out_subdir="userA")
    print("job_id:", jid)
    while True:
        s = runner.get_status(jid)
        print(s["state"], s.get("message"))
        if s["state"] in {JobState.SUCCESS, JobState.FAILED, JobState.CANCELED}:
            print(s)
            break
        time.sleep(1)
