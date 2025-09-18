# 영단어 학습 도구 (English Word Trainer)

로컬 엑셀 데이터를 기반으로 영어 단어를 반복 학습할 수 있는 Tkinter 데스크톱 애플리케이션입니다. 학습 기록을 저장하고 난이도를 조절하며, PyInstaller로 Windows 실행 파일(.exe)까지 배포할 수 있습니다.

## 주요 기능
- `영단어/*.xlsx` 엑셀에서 단어 목록 불러오기
- 시도/오답/레벨 등 학습 상태를 누적 추적
- 챕터 또는 단어 수 기준으로 학습 범위 필터링
- PyInstaller 빌드 스크립트 한 번으로 실행 파일 생성

## 코드 구성
- `영단어_ui.py` : Tkinter GUI 진입점
- `영단어.py` : 엑셀 로드, 학습 상태 컬럼 보정, 난이도 계산 로직
- `build_exe.py` : PyInstaller 빌드를 수행하고 산출물을 복사
- `requirements.txt` : 필요한 파이썬 의존성 (현재 `pandas`)

> `program/`, `dist/`, `build/` 등 빌드 산출물은 Git에 포함하지 않습니다. 필요 시 `build_exe.py`로 다시 생성하세요.

## 사전 준비
1. Windows + Python 3.10 이상 설치
2. `pip install -r requirements.txt`
3. 학습용 엑셀 파일을 `영단어` 폴더에 배치 (기본 이름 `영단어/영단어.xlsx`)

## 파이썬으로 실행하기
```bash
python 영단어_ui.py
```
- 실행 후 챕터/개수 필터를 설정하고 학습 세션을 시작합니다.
- 기본 설정은 `영단어.py` 상단의 상수(`CHAPTER_SPEC`, `FILTER_MODE`, `COUNT_SPEC` 등)를 수정해 조정할 수 있습니다.

## 실행 파일 빌드하기
```bash
python build_exe.py
```
- PyInstaller가 `dist/영단어_ui.exe`를 생성합니다.
- 스크립트가 최신 실행 파일과 엑셀 폴더를 `program/` 디렉터리로 복사합니다.
- `program/` 폴더는 재배포용이며 Git에는 커밋하지 않습니다.

## 배포(Release) 절차
1. `build_exe.py` 실행으로 `program/`을 생성합니다.
2. `program` 폴더를 압축해 `program.zip`을 만듭니다. (PowerShell: `Compress-Archive -Path program -DestinationPath program.zip -Force`)
3. GitHub 저장소 > **Releases** > **Draft a new release**로 이동합니다.
4. 태그(예: `v1.0.0`)와 제목, 변경 사항을 작성하고 `program.zip`을 첨부(Assets)한 뒤 Publish 합니다.
5. README에 최신 릴리스 링크를 안내하거나 필요 시 업데이트합니다.

## Git 사용 흐름
1. 상태 확인 : `git status`
2. 스테이징 : `git add <파일>` 또는 `git add .`
3. 커밋 : `git commit -m "메시지"`
4. 푸시 : `git push`

원격 저장소: `https://github.com/Choe-Useong/english-word-trainer.git`

## 향후 개선 아이디어
- `영단어.py` 핵심 로직에 대한 단위 테스트 추가
- GitHub Actions 워크플로를 통해 빌드 & 릴리스 자동화
- 엑셀 포맷(컬럼명, 예시 데이터)을 README에 도표로 정리
- 학습 기록을 CSV/JSON으로 내보내는 기능 추가
