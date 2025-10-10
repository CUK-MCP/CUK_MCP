# classes/GoogleCalendarAPIClient_class.py (개선판)

from __future__ import annotations
import os
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GoogleCalendarAPIClient:
    SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

    def __init__(self, calendar_id: str = "primary"):
        self.calendar_id = calendar_id
        self.creds = self._authenticate()
        self.service = build("calendar", "v3", credentials=self.creds)

    # ---- auth ----
    def _authenticate(self) -> Credentials:
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", self.SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # credentials.json 또는 client_secret.json 모두 지원
                cred_file = "credentials.json"
                if not os.path.exists(cred_file):
                    cred_file = "client_secret.json"
                flow = InstalledAppFlow.from_client_secrets_file(cred_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        return creds

    # ---- public API ----
    def sync_events(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        events: {"date": "YYYY-MM-DD" or "YYYY-MM-DD ~ YYYY-MM-DD", "title": "..."} 리스트
        """
        created, skipped = 0, 0
        for e in events:
            try:
                start_date, end_date = self._parse_date_field(e["date"])
                summary = e["title"].strip()

                # 중복 여부(같은 요약+같은 start.date 존재하는지) 확인
                if self._exists(summary, start_date):
                    skipped += 1
                    continue

                body = {
                    "summary": summary,
                    "start": {"date": start_date},
                    "end": {"date": end_date},  # 종일 이벤트 end는 다음날(exclusive)
                }
                self.service.events().insert(calendarId=self.calendar_id, body=body).execute()
                created += 1
            except Exception:
                # 개별 실패는 스킵하고 다음으로(원하면 로깅 추가)
                skipped += 1
        return {"created": created, "skipped": skipped}

    # ---- helpers ----
    def _parse_date_field(self, date_field: str) -> Tuple[str, str]:
        """
        - "YYYY-MM-DD"
        - "YYYY-MM-DD ~ YYYY-MM-DD"
        - 과거 호환: "YYYY.MM.DD"
        반환은 (start_date, end_date_exclusive)
        """
        s = date_field.strip()
        # 범위
        if "~" in s:
            start_raw, end_raw = [x.strip() for x in s.split("~", 1)]
            start = self._parse_any_date(start_raw)
            end_inclusive = self._parse_any_date(end_raw)
            end_exclusive = (datetime.fromisoformat(end_inclusive) + timedelta(days=1)).date().isoformat()
            return start, end_exclusive
        # 단일
        single = self._parse_any_date(s)
        end_exclusive = (datetime.fromisoformat(single) + timedelta(days=1)).date().isoformat()
        return single, end_exclusive

    def _parse_any_date(self, s: str) -> str:
        s = s.strip()
        # ISO "YYYY-MM-DD"
        try:
            return datetime.fromisoformat(s).date().isoformat()
        except ValueError:
            pass
        # legacy "YYYY.MM.DD"
        try:
            return datetime.strptime(s, "%Y.%m.%d").date().isoformat()
        except ValueError:
            raise ValueError(f"지원되지 않는 날짜 형식: {s}")

    def _exists(self, summary: str, start_date: str) -> bool:
        """
        같은 요약(summary)이고 같은 start.date를 가진 종일 이벤트가 이미 있는지 조회.
        """
        try:
            # timeMin/Max는 dateTime이 필요해서 날짜에 00:00/23:59를 붙여 조회
            time_min = f"{start_date}T00:00:00Z"
            time_max = f"{start_date}T23:59:59Z"
            resp = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                q=summary,
                singleEvents=True,
                maxResults=10,
            ).execute()
            items = resp.get("items", [])
            for it in items:
                # 종일 이벤트는 start.date 형태
                st = (it.get("start") or {}).get("date")
                sm = it.get("summary")
                if st == start_date and sm == summary:
                    return True
            return False
        except HttpError:
            # 조회 실패시 중복 판단을 포기하고 생성하도록 false 반환
            return False
