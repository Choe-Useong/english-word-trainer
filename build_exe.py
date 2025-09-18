
"""Build the 영단어 UI app into a standalone Windows executable.

Usage:
    python build_exe.py

Requirements:
    pip install PyInstaller

The script creates release/영단어_ui.exe and copies 학습용 엑셀 자료를 옮겨
사용자가 별도 설정 없이 실행할 수 있도록 정리합니다.
"""

from __future__ import annotations

import importlib.util
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
APP_SCRIPT = ROOT / "영단어_ui.py"
OUTPUT_DIR = ROOT / "release"
BUILD_DIR = ROOT / "build"
SPEC_FILE = ROOT / "영단어_ui.spec"

EXCEL_FILE_SOURCE = ROOT / "단어장.xlsx"
EXCEL_DIR_SOURCE = ROOT / "단어장"


def ensure_pyinstaller_available() -> None:
    if importlib.util.find_spec("PyInstaller") is None:
        raise SystemExit(
            "PyInstaller가 설치되어 있지 않습니다. 'pip install PyInstaller' 후 다시 실행해 주세요."
        )


def run_pyinstaller() -> None:
    if SPEC_FILE.exists():
        SPEC_FILE.unlink()
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        "영단어_ui",
        "--hidden-import",
        "영단어",
        "--distpath",
        str(OUTPUT_DIR),
        "--workpath",
        str(BUILD_DIR),
        str(APP_SCRIPT),
    ]
    completed = subprocess.run(cmd, cwd=ROOT)
    if completed.returncode != 0:
        raise SystemExit("PyInstaller 실행이 실패했습니다. 콘솔 로그를 확인해 주세요.")


def copy_learning_materials() -> None:
    if EXCEL_DIR_SOURCE.is_dir():
        target_dir = OUTPUT_DIR / EXCEL_DIR_SOURCE.name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(EXCEL_DIR_SOURCE, target_dir)
        print(f"단어장 폴더 복사 완료 → {target_dir}")
        return

    if EXCEL_FILE_SOURCE.is_file():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        target_file = OUTPUT_DIR / EXCEL_FILE_SOURCE.name
        shutil.copy2(EXCEL_FILE_SOURCE, target_file)
        print(f"단어장 엑셀 복사 완료 → {target_file}")
        return

    print("[경고] 복사할 단어장 자료(폴더 또는 엑셀 파일)를 찾지 못했습니다.")


def main() -> None:
    if not APP_SCRIPT.exists():
        raise SystemExit(f"앱 스크립트를 찾을 수 없습니다: {APP_SCRIPT}")
    ensure_pyinstaller_available()
    run_pyinstaller()
    copy_learning_materials()
    print("완료: release/영단어_ui.exe 를 실행해 주세요.")


if __name__ == "__main__":
    main()
