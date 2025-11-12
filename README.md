# 🧠 Model Context Server (MCP 기반 교내 통합 관리 서버)

## 📘 Overview
**모델 컨텍스트 프로토콜(Model Context Protocol, MCP)**을 기반으로 설계된 **교내 통합 관리 서버**입니다.  
이 시스템은 학사 일정 조회, 시간표 검색, 시스템 파일 관리 등 교내 데이터를 효율적으로 관리할 수 있도록 **API 형태**로 제공합니다.  
또한 모듈 간 연동 구조를 통해 확장성과 유지보수성을 확보했습니다.

---

## ⚙️ Tech Stack
- **Backend Framework:** FastMCP (Python 3.11)
- **Language:** Python
- **Data Crawling:** BeautifulSoup4, Requests
- **Architecture:** Modular Service Layer + API Router 구조
- **Protocol:** Model Context Protocol (MCP) 기반 통신 구조

---

## 🧩 Features
| 기능 | 설명 |
|------|------|
| 📅 **학사 일정 조회 API** | 크롤링 모듈을 통해 교내 공지/학사일정을 자동 수집 및 제공 |
| 🕒 **시간표 검색 API** | 데이터베이스에 저장된 시간표 데이터를 FastAPI로 조회 가능 |
| 📁 **파일 관리 시스템** | 로컬 시스템 파일 접근 및 관리 기능을 모듈화하여 제공 |
| 🔗 **MCP 기반 연동** | MCP 규격을 따라 외부 에이전트/클라이언트와 확장 연동 가능 |

---

