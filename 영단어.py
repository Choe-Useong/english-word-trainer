import pandas as pd
import re
from pathlib import Path
import sys

# ===== 설정 =====

def resolve_excel_path() -> Path:
    if getattr(sys, 'frozen', False):
        candidates = [
            Path(getattr(sys, '_MEIPASS')),      # 임시 추출 위치
            Path(sys.executable).resolve().parent,  # exe가 놓인 실제 폴더
        ]
    else:
        script_dir = Path(__file__).resolve().parent
        candidates = [script_dir]

    for base in candidates:
        data_dir = base / '단어장'
        if data_dir.is_dir():
            excel_files = sorted(data_dir.glob('*.xlsx'))
            if excel_files:
                return excel_files[0]
        fallback = base / '단어장.xlsx'
        if fallback.is_file():
            return fallback

    raise FileNotFoundError(
        "단어장(.xlsx) 파일을 찾을 수 없습니다. 단어장 폴더 또는 엑셀 파일을 exe와 같은 위치에 두세요."
    )

FILE_PATH    = resolve_excel_path()
SHEET_NAME   = "Sheet1"
CHAPTER_SPEC = "1-7"             # 예시: "1-7", "1,7,12"
FILTER_MODE  = "count"        # chapter | count
COUNT_SPEC   = "1-10"          # FILTER_MODE=count일 때 1-based 범위 예: "100" or "1-100" or "1,5,10-20"
PRIOR_MAP    = {
    1: 0.0,
    2: 0.3,
    3: 0.6,
    4: 0.9,
}
K            = 3                 # prior 신뢰도(베이지안 기반)
AUTOSAVE     = 10                # n문제마다 자동 저장
SHOW_TOP10   = False             # 세션 종료 시 상위 10개 출력 여부

# ===== 유틸 =====
def to_chapter_num(x):
    """Day가 'day12' 같은 문자열이어도 숫자만 뽑아서 챕터 번호로."""
    if pd.isna(x): return None
    s = str(x)
    m = re.findall(r"\d+", s)
    return int(m[0]) if m else None

def parse_chapter_spec(spec: str):
    """'1-7'/'1~7' 범위, '1,7,12' 개별 선택 모두 지원."""
    s = spec.strip().replace(" ", "")
    if "-" in s or "~" in s:
        a, b = re.split(r"[-~]", s)
        a, b = int(a), int(b)
        if a > b: a, b = b, a
        return set(range(a, b+1))
    return set(int(x) for x in s.split(",") if x)


def parse_count_spec(spec: str):
    """1-based 위치 기준 범위 지정. 예) "100", "1-100", "1,5,10-20" 지원."""
    s = spec.strip().replace(" ", "")
    if not s:
        return []
    parts = s.split(",")
    idxs = set()
    for part in parts:
        if "-" in part or "~" in part:
            a, b = re.split(r"[-~]", part)
            a, b = int(a), int(b)
            if a > b: a, b = b, a
            idxs.update(range(a, b+1))
        else:
            idxs.add(int(part))
    return sorted(idxs)

def ensure_state_cols(df):
    for col in ["Tries", "Fails", "LastStep", "InitLevel"]:
        if col not in df.columns:
            if col == "InitLevel":
                df[col] = pd.NA
            else:
                df[col] = 0
    return df

def get_prior(init_level):
    try:
        return PRIOR_MAP[int(init_level)]
    except:
        return 0.5  # 안전 기본값

def bayes_diff(prior: float, k: int, fails: int, tries: int) -> float:
    # diff = (prior*k + fails) / (k + tries)
    denom = k + tries
    return (prior * k + fails) / (denom if denom > 0 else 1)

def recency_norm(cur_step: int, last_step: int) -> float:
    # rec_norm = (현재 step - 마지막 본 step) / 현재 step  (0~1)
    if cur_step <= 0:
        return 1.0  # 시작 직후엔 다 '오래됨' 취급해서 첫 라운드 가속
    rec = max(0, cur_step - last_step)
    return min(rec / cur_step, 1.0)

# ===== 메인 =====
def main():
    df = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME)
    df = ensure_state_cols(df)

    # 선택 범위 필터 (챕터 또는 단어수)
    sel_desc = ""
    if FILTER_MODE == "chapter":
        df["챕터"] = df["Day"].apply(to_chapter_num)
        want = parse_chapter_spec(CHAPTER_SPEC)
        sub = df[df["챕터"].isin(want)].copy()
        sel_desc = f"챕터 {CHAPTER_SPEC}"
    elif FILTER_MODE == "count":
        positions = parse_count_spec(COUNT_SPEC)
        df_reset = df.reset_index(drop=True)
        zero_based = [p-1 for p in sorted(set(positions)) if 1 <= p <= len(df_reset)]
        sub = df_reset.iloc[zero_based].copy()
        sel_desc = f"단어순서 {COUNT_SPEC}"
    else:
        print("FILTER_MODE는 'chapter' 또는 'count'만 지원합니다.")
        return
    if sub.empty:
        print("선택한 범위에 단어가 없습니다.")
        return
    cur_step = int(df["Tries"].sum())
    asked = 0
    print(f"학습 시작: {sel_desc}, 단어 {len(sub)}개, 현재 step={cur_step}")

    while True:
        # --- 지연 초기화: 처음 만나는 카드면 난이도부터 받기 ---
        for idx, row in sub.iterrows():
            if int(row["Tries"]) == 0 and pd.isna(row["InitLevel"]):
                print(f"\n[새 카드 난이도 체크] {row['단어']} / 뜻: {row['뜻']}")
                while True:
                    s = input("난이도(1=매우 쉬움, 2=쉬움, 3=어려움, 4=전혀 모름) > ").strip()
                    if s in {"1","2","3","4"}:
                        sub.loc[idx, "InitLevel"] = int(s)
                        # 원본 df에도 반영(단어/뜻 매칭으로 동기화)
                        mask = (df["단어"] == row["단어"]) & (df["뜻"] == row["뜻"])
                        df.loc[mask, "InitLevel"] = int(s)
                        break
                    else:
                        print("1~4 중에 골라.")

        # --- risk 계산(정렬용) ---
        rows = []
        for idx, row in sub.iterrows():
            tries = int(row["Tries"])
            fails = int(row["Fails"])
            last  = int(row["LastStep"])
            prior = get_prior(row["InitLevel"])
            diff  = bayes_diff(prior, K, fails, tries)
            recn  = recency_norm(cur_step, last)
            # prior=0(매우 쉬움)이라도 오래되면 ε*recn으로 살짝은 나오게
            risk  = diff * recn
            rows.append((idx, risk, diff, recn))

        # risk 내림차순, 동률이면 recency 큰 순
        rows.sort(key=lambda x: (x[1], x[3]), reverse=True)

        # risk>0인 첫 카드 선택 (이론상 항상 존재, 방금 본 카드만 잔뜩이면 다음 루프로)
        pick = next((r for r in rows if r[1] > 0), None)
        if pick is None:
            # 거의 안 생기지만, 모두 방금 본 카드면 한 턴 쉬고 진행
            cur_step += 1
            continue

        idx_top, r_top, d_top, rn_top = pick
        row = sub.loc[idx_top]

        # --- 문제 출제 ---
        print("\n" + "-"*60)
        print(f"[Q] {row['단어']}")
        input("뜻 떠올렸으면 엔터 > ")
        print(f"[A] {row['뜻']}")

        # --- 자기신고 ---
        ans = input("맞았나? y/n  (q=종료) > ").strip().lower()
        if ans == "q":
            break

        # --- 업데이트 (원본 df와 sub 모두) ---
        mask = (df["단어"] == row["단어"]) & (df["뜻"] == row["뜻"])
        df.loc[mask, "Tries"]     = df.loc[mask, "Tries"].astype(int) + 1
        sub.loc[idx_top, "Tries"] = int(sub.loc[idx_top, "Tries"]) + 1
        if ans == "n":
            df.loc[mask, "Fails"]     = df.loc[mask, "Fails"].astype(int) + 1
            sub.loc[idx_top, "Fails"] = int(sub.loc[idx_top, "Fails"]) + 1
        df.loc[mask, "LastStep"]     = cur_step
        sub.loc[idx_top, "LastStep"] = cur_step

        cur_step += 1
        asked += 1

        # --- 자동 저장 ---
        if asked % AUTOSAVE == 0:
            df.to_excel(FILE_PATH, sheet_name=SHEET_NAME, index=False)
            print(f"[자동 저장] {asked}문제 진행, step={cur_step}")

    # --- 최종 저장 & 요약 ---
    df.to_excel(FILE_PATH, sheet_name=SHEET_NAME, index=False)
    print("\n세션 종료. 저장 완료.")

    if SHOW_TOP10:
        # 오답률 상위 10 (베이지안 추정치 기준)
        sub["diff_est"] = sub.apply(
            lambda r: bayes_diff(get_prior(r["InitLevel"]), K, int(r["Fails"]), int(r["Tries"])),
            axis=1
        )
        rep = sub.sort_values("diff_est", ascending=False)[["단어","뜻","Tries","Fails","diff_est"]].head(10)
        if not rep.empty:
            print("\n[오답률 상위 10]")
            for _, r in rep.iterrows():
                print(f"- {r['단어']}: {int(r['Fails'])}/{int(r['Tries'])} (diff≈{r['diff_est']:.2f})")

if __name__ == "__main__":
    main()