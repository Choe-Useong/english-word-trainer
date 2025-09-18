# 영단어 학습 도구 (English Word Trainer)

엑셀에 정리한 단어장을 기반으로 영어 단어를 반복 학습할 수 있는 Tkinter 데스크톱 애플리케이션입니다. 학습 기록을 누적 관리하며, PyInstaller로 윈도우 실행 파일(.exe)까지 배포할 수 있습니다.

## 주요 기능
- `영단어/*.xlsx` 엑셀 파일에서 단어 목록 로드
- 시도 횟수/오답/레벨/최근 날짜 등 학습 상태 자동 추적
- 챕터 또는 단어 개수 기준으로 학습 범위 필터링
- PyInstaller 스크립트로 손쉽게 실행 파일 생성

## 폴더 구성
- `영단어_ui.py` : Tkinter GUI 진입점
- `영단어.py` : 엑셀 검색, 상태 컬럼 보정, 난이도 계산 로직
- `build_exe.py` : PyInstaller 실행 및 결과 복사
- `requirements.txt` : 필요한 파이썬 패키지 목록 (현재 `pandas`)

> `program/`, `dist/`, `build/` 등 빌드 산출물은 Git에 추적하지 않습니다. 필요 시 `build_exe.py`로 재생성하세요.

## 개발 환경 준비
1. Windows + Python 3.10 이상 설치
2. 의존성 설치: `pip install -r requirements.txt`
3. 학습용 엑셀 파일을 `영단어/` 폴더에 배치 (기본 파일명 `영단어/영단어.xlsx`)

## 소스 코드로 실행하기
```bash
python 영단어_ui.py
```
- 실행 후 챕터/개수 조건을 설정하고 학습 세션을 시작합니다.
- 기본 설정은 `영단어.py` 상단의 상수(`CHAPTER_SPEC`, `FILTER_MODE`, `COUNT_SPEC` 등)를 수정하면 됩니다.

## 일반 사용자용 실행 파일 받기
1. GitHub 저장소의 **Releases** 페이지로 이동합니다.
2. 최신 릴리스에서 `program.zip` 파일을 다운로드합니다.
3. 원하는 위치에 압축을 해제합니다.
4. 압축이 풀린 `program` 폴더 안에서 `영단어/`에 엑셀 파일을 넣거나 교체합니다.
5. `영단어_ui.exe`를 실행합니다. (엑셀과 exe는 항상 동일한 상위 폴더에 있어야 합니다.)

## 유지보수자가 새 버전 배포하기
1. `python build_exe.py` 실행 → `dist/영단어_ui.exe` 생성 및 `program/` 폴더 최신화
2. `Compress-Archive -Path program -DestinationPath program.zip -Force`로 압축 생성 (엑셀 파일이 열려 있지 않은지 확인)
3. GitHub > **Releases** > **Draft a new release**에서 태그/제목/변경 사항 작성 후 `program.zip` 첨부 → Publish
4. 필요한 경우 README 링크나 사용 가이드를 업데이트하고 커밋/푸시합니다.

## Git 사용 흐름
1. 상태 확인 : `git status`
2. 스테이징 : `git add <파일>` 또는 `git add .`
3. 커밋 : `git commit -m "메시지"`
4. 푸시 : `git push`

원격 저장소: `https://github.com/Choe-Useong/english-word-trainer.git`

## 향후 개선 아이디어
- `영단어.py` 핵심 로직에 대한 단위 테스트 추가
- GitHub Actions를 이용한 PyInstaller 자동 빌드 및 Release 업로드 자동화
- 엑셀 포맷(컬럼명, 예시 데이터)을 README에 표로 정리
- 학습 성과를 CSV/JSON으로 내보내는 기능 추가
