## 🔧 환경 설정 및 설치

img2text는 OCR 기능을 위해 Tesseract 엔진을 필요로 합니다. 아래 지침에 따라 Tesseract를 설치하고 환경 변수를 설정해 주세요.

### Tesseract 설치

* **Windows**: [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)에서 최신 버전을 다운로드하여 설치합니다. 설치 과정 중 'Add to PATH' 옵션과 'Korean' 언어 팩을 반드시 선택해 주세요.
* **macOS**: 터미널에서 `brew install tesseract`를 실행합니다.

### pytesseract 경로 설정

Tesseract 설치 후에도 `tesseract is not installed` 오류가 발생하면, `BaseWebCrawler_class.py` 파일의 Tesseract 경로를 직접 지정해 주세요.

```python
import pytesseract
# Tesseract 설치 경로를 수정해 주세요.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'