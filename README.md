# 영단어 학습 도구 (English Word Trainer)

영단어를 반복 학습할 수 있는 간단한 윈도우 프로그램입니다. 엑셀로 관리하던 단어장을 불러와 시도/오답을 기록하며, 난이도에 따라 다시 복습할 단어를 자동으로 골라 줍니다.

## 빠른 시작 (일반 사용자)
1. GitHub 저장소의 **Releases** 탭으로 이동합니다.
2. 최신 릴리스에서 `program.zip`을 내려받아 원하는 폴더에 압축 해제합니다.
3. 압축이 풀린 `program` 폴더 안에 있는 `영단어/` 폴더에 본인 단어장 엑셀을 넣습니다. (예시 엑셀 파일이 기본으로 포함되어 있습니다.)
4. `영단어_ui.exe`를 실행합니다.
5. 프로그램 상단에서 학습 모드(챕터/개수)와 범위를 선택하고 "공부 시작" 버튼을 누르면 바로 학습이 시작됩니다.

### 프로그램 화면에서 할 수 있는 일
- 왼쪽 목록에서 문제를 풀 단어 범위를 지정합니다.
- 오른쪽 영역에 퀴즈가 나오며 정답을 입력하거나 "정답 보기" 버튼으로 확인할 수 있습니다.
- 틀린 단어는 자동으로 기록되어 다음 학습 때 우선순위가 올라갑니다.

### 단어장(엑셀) 교체하기
- 엑셀 파일은 `program/영단어` 폴더 안에 있어야 합니다.
- 기본 파일 이름은 `영단어.xlsx`이며, 첫 열에 영단어, 두 번째 열에 뜻이 들어 있으면 바로 사용할 수 있습니다.
- 이미 실행 중이라면 프로그램을 종료한 뒤 엑셀 파일을 교체하고 다시 실행하세요.

## 엑셀 파일 형식 팁
| 열 이름 예시 | 설명 |
| --- | --- |
| 단어 / Word | 영어 단어 |
| 뜻 / Meaning | 한국어 뜻 |
| Tries / Fails / InitLevel | (선택) 학습 횟수, 오답 수, 초기 난이도 |

열 이름이 달라도 프로그램이 자동으로 유사한 열을 찾아 사용합니다. 추적용 컬럼이 없다면 학습 과정에서 자동으로 추가됩니다.

---

## 개발자용 정보

### 환경 준비
- Python 3.10 이상 (Windows)
- 의존성 설치: `pip install -r requirements.txt`

### 소스 코드로 실행
```bash
python 영단어_ui.py
```
- `영단어.py` 상단의 설정값(`CHAPTER_SPEC`, `FILTER_MODE`, `COUNT_SPEC` 등)으로 기본 학습 범위를 조정할 수 있습니다.

### 실행 파일 빌드
```bash
python build_exe.py
```
- PyInstaller가 `dist/영단어_ui.exe`를 생성하고, 스크립트가 실행 파일과 데이터 폴더를 `program/` 디렉터리로 복사합니다.

### 새 릴리스 배포 절차
1. `python build_exe.py` 실행으로 `program/` 폴더를 최신 상태로 만듭니다.
2. `Compress-Archive -Path program -DestinationPath program.zip -Force`로 압축 파일을 생성합니다.
3. GitHub > **Releases** > **Draft a new release**에서 태그와 변경 사항을 입력하고 `program.zip`을 첨부한 뒤 Publish 합니다.
4. 필요하면 README 또는 사용 가이드를 업데이트하고 `git commit`/`git push`합니다.

### Git 사용 흐름
1. 상태 확인 : `git status`
2. 스테이징 : `git add <파일>` 또는 `git add .`
3. 커밋 : `git commit -m "메시지"`
4. 푸시 : `git push`

원격 저장소: `https://github.com/Choe-Useong/english-word-trainer.git`

---

## 앞으로 추가하면 좋은 것들
- `영단어.py` 핵심 로직에 대한 자동 테스트
- GitHub Actions로 PyInstaller 빌드 & 릴리스 자동화
- 자주 틀리는 단어 요약 리포트, CSV/JSON 내보내기 기능
- 단어장 샘플과 스크린샷을 README에 추가
