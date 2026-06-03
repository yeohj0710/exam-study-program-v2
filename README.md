# 시험 자료 암기 프로그램

PDF와 기존 캡처 문제 은행을 자동으로 가져와 카드처럼 복습하는 로컬 학습 프로그램입니다.

## 바로 실행

1. 저장소를 내려받거나 압축을 풉니다.
2. 루트 폴더의 `시험 자료 암기 프로그램.exe`를 더블클릭합니다.
3. 자동으로 열린 브라우저에서 학습합니다.

보안 정책 때문에 exe가 막히면 `시험 자료 암기 프로그램.cmd`를 더블클릭하세요. 실행 창을 닫으면 프로그램도 같이 종료될 수 있습니다.

자세한 사용법은 루트 폴더의 `사용설명서.html`을 열면 됩니다.

## 자료 가져오기

자료가 아직 없으면 첫 화면에서 PDF 폴더와 기존 캡처 폴더를 확인한 뒤 `자료 가져오기`를 누릅니다.

기본 경로:

```text
G:\내 드라이브\여형준님\21 6-1
G:\내 드라이브\여형준님\21 6-1\족보 암기 프로그램\중간고사
```

원본 자료는 읽기만 합니다. 생성된 라이브러리, 복습 기록, 검수 기록은 `프로그램 구성 파일\data` 안에 저장됩니다.

## 폴더 구조

- `시험 자료 암기 프로그램.exe`: Python 설치 없이 더블클릭으로 실행하는 Windows 실행 파일
- `시험 자료 암기 프로그램.cmd`: exe가 막힐 때 쓰는 보조 실행 파일
- `사용설명서.html`: 비개발자용 사용 설명서
- `프로그램 구성 파일`: 실제 앱 코드, 빌드 파일, 테스트, 런처, 런타임 데이터

## 개발자용

개발 작업을 할 때만 아래 폴더로 들어갑니다.

```powershell
cd "C:\dev\studyforge\프로그램 구성 파일"
python -m pip install -r requirements.txt
npm install
```

개발 서버:

```powershell
npm run dev:api
npm run dev
```

빌드와 검증:

```powershell
python -m pytest
npm run lint
npm run build
python scripts\run_cli.py validate
```

수동 import:

```powershell
python scripts\run_cli.py import --source-root "G:\내 드라이브\여형준님\21 6-1" --legacy-root "G:\내 드라이브\여형준님\21 6-1\족보 암기 프로그램\중간고사" --copy-legacy-assets
```
