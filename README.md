# English Word Trainer

Tkinter-based desktop app for practicing English vocabulary with Korean prompts. The UI loads word lists from Excel, tracks study progress, and supports packaging into a standalone Windows executable.

## Features
- Load vocabulary rows from Excel (`영단어/*.xlsx`)
- Track quiz progress (tries, fails, levels, session metadata)
- Interactive Tkinter study session with chapter or count filtering
- PyInstaller build script for producing distributable executables

## Project Structure
- `영단어_ui.py` - Tkinter GUI entry point that orchestrates study sessions
- `영단어.py` - Core logic for locating Excel files, managing state columns, and scoring words
- `build_exe.py` - PyInstaller helper that builds and copies release artifacts
- `release/` - Generated release-ready zip/exe bundles (ignored by Git)
- `dist/`, `build/`, `__pycache__/` - Intermediate build and cache folders (ignored by Git)

## Prerequisites
- Windows with Python 3.10 or newer
- Excel vocabulary file placed in the `영단어` directory (default expects `영단어/영단어.xlsx`)
- Install dependencies: `pip install -r requirements.txt`

## Running the App
```bash
python 영단어_ui.py
```

### Configuration
Adjust the values in `영단어.py` to fine-tune study behavior:
- `CHAPTER_SPEC`, `FILTER_MODE`, `COUNT_SPEC` - select study range
- `PRIOR_MAP` - adjust weighting for word difficulty levels
- `MIN_FAILS_FOR_STEP_UP`, `MAX_FAIL_GAP` - control level progression thresholds

## Building the Executable
```bash
python build_exe.py
```
The script runs PyInstaller, then copies the output into `release/` with a timestamped folder. Distribute the executable together with the Excel data (`영단어` directory or the same folder as the EXE) so the app can find the word list.

## Working with Git
1. Stage changes: `git add .`
2. Commit: `git commit -m "Describe change"`
3. Push: `git push`

Remote repository: `https://github.com/Choe-Useong/english-word-trainer.git`.

## Next Ideas
- Add automated tests around the data loading and scoring logic in `영단어.py`
- Publish the `release/` output as GitHub Releases for easier downloads
- Add a GitHub Actions workflow that runs the build script on push
