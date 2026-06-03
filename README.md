# StudyForge

중간고사 PDF와 기존 캡처 문제 은행을 자동으로 가져와 카드처럼 복습하는 로컬 학습 프로그램입니다.

## 실행 방법

1. 이 저장소를 내려받거나 압축을 풉니다.
2. 루트 폴더의 `StudyForge 실행.exe`를 더블클릭합니다.
3. 브라우저가 자동으로 열리면 사용하면 됩니다.

`StudyForge 실행.exe`가 보안 정책 때문에 막히는 환경에서는 `StudyForge 실행.cmd`를 더블클릭하면 됩니다. 실행 창을 닫으면 서버도 종료될 수 있습니다.

## 자료 가져오기

자료가 아직 없으면 화면의 `자료 가져오기`에서 아래 기본 경로가 자동으로 들어갑니다.

```text
G:\내 드라이브\여형준님\21 6-1
G:\내 드라이브\여형준님\21 6-1\족보 암기 프로그램\중간고사
```

원본 자료는 읽기만 합니다. 생성된 라이브러리, 복습 기록, 검수 기록은 `프로그램 구성 파일\data` 안에 저장됩니다.

## 폴더 구조

- `StudyForge 실행.exe`: Python 설치 없이 바로 실행하는 Windows 실행 파일
- `StudyForge 실행.cmd`: exe가 막힐 때 쓰는 보조 실행 파일
- `프로그램 구성 파일`: 실제 앱 코드, 빌드 파일, 테스트, 런처, 런타임 데이터
- `README.md`: 사용 안내

루트에는 실행에 필요한 최소 파일만 두었습니다.

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
python scripts\run_cli.py import --source-root "G:\내 드라이브\여형준님\21 6-1" --legacy-root "G:\내 드라이브\여형준님\21 6-1\족보 암기 프로그램\중간고사"
```
