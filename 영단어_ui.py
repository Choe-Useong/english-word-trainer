import importlib
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd
import tkinter as tk
from tkinter import messagebox, ttk

core = importlib.import_module("영단어")

WORD_CANDIDATES = ["영어", "단어", "Word", "단어(영어)", "단어(ENG)"]
MEANING_CANDIDATES = ["뜻", "의미", "뜻풀이", "뜻(한국어)", "뜻(의미)", "Meaning"]
STATE_COLUMNS = {"Tries", "Fails", "LastStep", "InitLevel", "Day", "챕터"}

INIT_LEVEL_LABELS = {
    1: "매우 익숙",
    2: "익숙",
    3: "애매함",
    4: "잘 모름",
}


def detect_column(df: pd.DataFrame, candidates: List[str], exclude: set[str]) -> str:
    for name in candidates:
        if name in df.columns:
            return name
    for col in df.columns:
        if col not in exclude:
            return col
    return df.columns[0]


class StudySession:
    def __init__(self, df: pd.DataFrame, filter_mode: str, chapter_spec: str, count_spec: str) -> None:
        self.filter_mode = filter_mode if filter_mode in {"chapter", "count"} else core.FILTER_MODE
        self.chapter_spec = (chapter_spec or str(core.CHAPTER_SPEC)).strip()
        self.count_spec = (count_spec or str(core.COUNT_SPEC)).strip()

        self.df = core.ensure_state_cols(df.copy())

        self.word_col = detect_column(self.df, WORD_CANDIDATES, STATE_COLUMNS)
        meaning_exclude = STATE_COLUMNS | {self.word_col}
        self.meaning_col = detect_column(self.df, MEANING_CANDIDATES, meaning_exclude)

        self.sub, self.sel_desc = self._build_subset()
        if self.sub.empty:
            raise ValueError("선택된 범위에 학습할 단어가 없습니다.")

        self.cur_step = int(pd.to_numeric(self.df["Tries"], errors="coerce").fillna(0).sum())
        self.asked = 0
        self.current_idx: Optional[int] = None

    def _build_subset(self) -> Tuple[pd.DataFrame, str]:
        if self.filter_mode == "chapter":
            if "Day" not in self.df.columns:
                raise ValueError("엑셀에 'Day' 컬럼이 없어 챕터 기준을 사용할 수 없습니다.")
            self.df["챕터"] = self.df["Day"].apply(core.to_chapter_num)
            want = core.parse_chapter_spec(self.chapter_spec)
            subset = self.df[self.df["챕터"].isin(want)].copy()
            desc = f"챕터 {self.chapter_spec}"
        elif self.filter_mode == "count":
            positions = core.parse_count_spec(self.count_spec)
            df_reset = self.df.reset_index(drop=True)
            zero_based = [p - 1 for p in sorted(set(positions)) if 1 <= p <= len(df_reset)]
            subset = df_reset.iloc[zero_based].copy()
            desc = f"번호 {self.count_spec}"
        else:
            raise ValueError("FILTER_MODE는 'chapter' 또는 'count'만 지원합니다.")
        return subset, desc

    @staticmethod
    def _is_valid_init_level(value: object) -> bool:
        if value is None or pd.isna(value):
            return False
        try:
            return int(value) in INIT_LEVEL_LABELS
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _safe_int(value: object, default: int = 0) -> int:
        if value is None or pd.isna(value):
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def get_pending_init_card(self) -> Optional[Tuple[int, pd.Series]]:
        for idx, row in self.sub.iterrows():
            if self._safe_int(row["Tries"]) == 0 and not self._is_valid_init_level(row.get("InitLevel")):
                return idx, row
        return None

    def set_init_level(self, idx: int, level: int) -> None:
        self.sub.loc[idx, "InitLevel"] = level
        mask = (
            (self.df[self.word_col] == self.sub.loc[idx, self.word_col])
            & (self.df[self.meaning_col] == self.sub.loc[idx, self.meaning_col])
        )
        self.df.loc[mask, "InitLevel"] = level

    def choose_next_card(self) -> Optional[Tuple[int, pd.Series]]:
        if self.sub.empty:
            return None
        attempts = 0
        while attempts <= len(self.sub):
            scored: List[Tuple[int, float, float, float]] = []
            for idx, row in self.sub.iterrows():
                tries = self._safe_int(row["Tries"])
                fails = self._safe_int(row["Fails"])
                last = self._safe_int(row["LastStep"])
                prior = core.get_prior(row["InitLevel"])
                diff = core.bayes_diff(prior, core.K, fails, tries)
                recn = core.recency_norm(self.cur_step, last)
                risk = diff * recn
                scored.append((idx, risk, diff, recn))

            scored.sort(key=lambda x: (x[1], x[3]), reverse=True)
            pick = next((r for r in scored if r[1] > 0), None)
            if pick is not None:
                idx_top = pick[0]
                self.current_idx = idx_top
                return idx_top, self.sub.loc[idx_top].copy()

            self.cur_step += 1
            attempts += 1

        self.current_idx = None
        return None

    def record_answer(self, idx: int, correct: bool) -> None:
        row = self.sub.loc[idx]
        mask = (
            (self.df[self.word_col] == row[self.word_col])
            & (self.df[self.meaning_col] == row[self.meaning_col])
        )
        self.df.loc[mask, "Tries"] = (
            self.df.loc[mask, "Tries"].fillna(0).astype(int) + 1
        )
        self.sub.loc[idx, "Tries"] = self._safe_int(row["Tries"]) + 1

        if not correct:
            self.df.loc[mask, "Fails"] = (
                self.df.loc[mask, "Fails"].fillna(0).astype(int) + 1
            )
            self.sub.loc[idx, "Fails"] = self._safe_int(row["Fails"]) + 1

        self.df.loc[mask, "LastStep"] = self.cur_step
        self.sub.loc[idx, "LastStep"] = self.cur_step

        self.cur_step += 1
        self.asked += 1
        self.current_idx = None

    def describe_card_stats(self, row: pd.Series) -> Tuple[str, str]:
        tries = self._safe_int(row.get("Tries"))
        fails = self._safe_int(row.get("Fails"))
        if tries > 0:
            correct = max(0, tries - fails)
            rate = f"{correct / tries * 100:.0f}% ({correct}/{tries})"
        else:
            rate = "-"

        last = self._safe_int(row.get("LastStep"))
        if last <= 0:
            last_seen = "처음 진행"
        else:
            delta = max(0, self.cur_step - last)
            if delta == 0:
                last_seen = "방금 전"
            elif delta == 1:
                last_seen = "1문제 전"
            else:
                last_seen = f"{delta}문제 전"
        return rate, last_seen

    def needs_autosave(self) -> bool:
        return bool(core.AUTOSAVE) and self.asked > 0 and self.asked % core.AUTOSAVE == 0

    def save(self) -> None:
        self.df.to_excel(core.FILE_PATH, sheet_name=core.SHEET_NAME, index=False)

    def finalize(self) -> List[str]:
        self.save()
        return self.get_top10_report() if core.SHOW_TOP10 else []

    def get_top10_report(self) -> List[str]:
        sub = self.sub.copy()
        sub["diff_est"] = sub.apply(
            lambda r: core.bayes_diff(
                core.get_prior(r["InitLevel"]),
                core.K,
                self._safe_int(r["Fails"]),
                self._safe_int(r["Tries"], default=0),
            ),
            axis=1,
        )
        rep = sub.sort_values("diff_est", ascending=False)[
            [self.word_col, self.meaning_col, "Tries", "Fails", "diff_est"]
        ].head(10)

        lines: List[str] = []
        for _, r in rep.iterrows():
            fails = self._safe_int(r["Fails"])
            tries = self._safe_int(r["Tries"], default=1)
            lines.append(
                f"{r[self.word_col]}: {fails}/{tries} (diff={r['diff_est']:.2f})"
            )
        return lines


class ConfigFrame(ttk.Frame):
    def __init__(self, parent: tk.Tk, df: pd.DataFrame, on_start, on_cancel: Optional[Callable[[], None]] = None) -> None:
        super().__init__(parent, padding=20)
        self.parent = parent
        self.df = df
        self.on_start = on_start
        self.on_cancel = on_cancel

        default_mode = core.FILTER_MODE if core.FILTER_MODE in {"chapter", "count"} else "count"
        self.mode_var = tk.StringVar(value=default_mode)
        self.chapter_var = tk.StringVar(value=str(core.CHAPTER_SPEC))
        self.count_var = tk.StringVar(value=str(core.COUNT_SPEC))

        self._chapter_choices = self._collect_chapter_choices()
        self._build_widgets()
        self._update_mode()
        self.parent.protocol("WM_DELETE_WINDOW", self._cancel)

    def _collect_chapter_choices(self) -> List[str]:
        if "Day" not in self.df.columns:
            return []
        try:
            series = self.df["Day"].apply(core.to_chapter_num)
        except Exception:
            return []
        valid = sorted({int(v) for v in series.dropna().tolist()})
        return [str(v) for v in valid]

    def _build_widgets(self) -> None:
        title = ttk.Label(self, text="학습 범위를 선택한 뒤 시작을 눌러 주세요.", font=("Segoe UI", 11, "bold"))
        title.pack(anchor="w")

        mode_frame = ttk.LabelFrame(self, text="범위 방식")
        mode_frame.pack(fill="x", pady=(12, 0))

        ttk.Radiobutton(
            mode_frame,
            text="챕터(Day) 기준",
            value="chapter",
            variable=self.mode_var,
            command=self._update_mode,
        ).pack(anchor="w")
        ttk.Radiobutton(
            mode_frame,
            text="번호 범위 기준",
            value="count",
            variable=self.mode_var,
            command=self._update_mode,
        ).pack(anchor="w")

        self.chapter_frame = ttk.LabelFrame(self, text="챕터 / Day")
        self.chapter_frame.pack(fill="x", pady=(12, 0))

        ttk.Label(self.chapter_frame, text="입력 예: 1-3 또는 1,5").pack(anchor="w")
        self.chapter_entry = ttk.Entry(self.chapter_frame, textvariable=self.chapter_var)
        self.chapter_entry.pack(fill="x", pady=(2, 4))

        if self._chapter_choices:
            ttk.Label(self.chapter_frame, text="Day 목록에서 선택").pack(anchor="w")
            self.chapter_combo = ttk.Combobox(
                self.chapter_frame,
                values=self._chapter_choices,
                state="readonly",
            )
            self.chapter_combo.pack(fill="x", pady=(2, 0))
            self.chapter_combo.bind("<<ComboboxSelected>>", self._on_combo_selected)
        else:
            self.chapter_combo = None
            ttk.Label(
                self.chapter_frame,
                text="Day 열이 없거나 숫자를 찾을 수 없습니다.",
                foreground="#888",
            ).pack(anchor="w", pady=(2, 0))

        self.count_frame = ttk.LabelFrame(self, text="번호 범위")
        self.count_frame.pack(fill="x", pady=(12, 0))

        ttk.Label(self.count_frame, text="입력 예: 1-10 또는 3,5,8").pack(anchor="w")
        self.count_entry = ttk.Entry(self.count_frame, textvariable=self.count_var)
        self.count_entry.pack(fill="x", pady=(2, 4))

        ttk.Label(
            self,
            text="쉼표와 범위를 섞어서 입력할 수 있습니다.",
            foreground="#555",
        ).pack(anchor="w", pady=(8, 0))

        button_row = ttk.Frame(self)
        button_row.pack(fill="x", pady=(18, 0))

        close_btn = ttk.Button(button_row, text="닫기", command=self._cancel)
        close_btn.pack(side="right")
        self.start_button = ttk.Button(button_row, text="시작", command=self._start)
        self.start_button.pack(side="right", padx=(0, 8))
        self.start_button.focus_set()

        self.parent.bind("<Return>", lambda _: self._start())
        self.parent.bind("<Escape>", lambda _: self._cancel())

    def _update_mode(self) -> None:
        mode = self.mode_var.get()
        chapter_state = "normal" if mode == "chapter" else "disabled"
        count_state = "disabled" if mode == "chapter" else "normal"
        self.chapter_entry.configure(state=chapter_state)
        if getattr(self, "chapter_combo", None) is not None:
            combo_state = "readonly" if mode == "chapter" else "disabled"
            self.chapter_combo.configure(state=combo_state)
        self.count_entry.configure(state=count_state)

    def _on_combo_selected(self, _: tk.Event) -> None:
        if getattr(self, "chapter_combo", None) is None:
            return
        value = self.chapter_combo.get().strip()
        if value:
            self.chapter_var.set(value)

    def _start(self) -> None:
        mode = self.mode_var.get()
        if mode == "chapter":
            spec = self.chapter_var.get().strip()
            if not spec:
                messagebox.showerror("안내", "챕터 범위를 입력하거나 선택해 주세요.", parent=self)
                return
            self.on_start("chapter", spec, "")
            self.parent.destroy()
        else:
            spec = self.count_var.get().strip()
            if not spec:
                messagebox.showerror("안내", "번호 범위를 입력해 주세요.", parent=self)
                return
            self.on_start("count", "", spec)
            self.parent.destroy()

    def _cancel(self) -> None:
        if self.on_cancel is not None:
            self.on_cancel()
        self.parent.destroy()
class StudyApp(tk.Tk):
    def __init__(self, session: StudySession) -> None:
        super().__init__()
        self.session = session
        self.title("영단어 학습")
        self.geometry("720x520")
        self.minsize(720, 520)
        self.resizable(False, False)

        self._current_card: Optional[Tuple[int, pd.Series]] = None
        self._answer_visible = False
        self._autosave_flag = False

        self._build_widgets()
        self._bind_keys()
        self.protocol("WM_DELETE_WINDOW", self.quit_session)

        self.prepare_next_card()

    def _build_widgets(self) -> None:
        style = ttk.Style(self)
        style.configure('Quiz.TButton', padding=(14, 10))

        top_frame = ttk.Frame(self)
        top_frame.pack(fill='x', pady=(14, 8))

        self.header_var = tk.StringVar(value=f'학습 범위: {self.session.sel_desc}')
        ttk.Label(
            top_frame,
            textvariable=self.header_var,
            font=('Segoe UI', 11, 'bold'),
        ).pack(side='left', padx=(28, 0))

        control_frame = ttk.Frame(top_frame)
        control_frame.pack(side='right', padx=(0, 28))

        self.overall_var = tk.StringVar(value=f"정답률: -\nstep {self.session.cur_step}")

        ttk.Label(control_frame, textvariable=self.overall_var, font=('Segoe UI', 9)).pack(anchor='e')
        ttk.Button(control_frame, text='범위 다시 설정', command=self.open_reconfigure).pack(anchor='e', pady=(6, 0))

        self.status_var = tk.StringVar()

        self.question_var = tk.StringVar(value='문제를 불러오는 중입니다...')
        ttk.Label(
            self,
            textvariable=self.question_var,
            font=('Segoe UI', 22, 'bold'),
            anchor='center',
            justify='center',
            padding=(0, 22),
        ).pack(fill='x', padx=28)

        self.answer_var = tk.StringVar(value='')
        ttk.Label(
            self,
            textvariable=self.answer_var,
            font=('Segoe UI', 11),
            anchor='center',
            padding=(0, 10),
        ).pack(fill='x', padx=28, pady=(0, 18))

        button_frame = ttk.Frame(self)
        button_frame.pack(pady=(0, 18))

        self.show_btn = ttk.Button(button_frame, text='정답 보기', command=self.reveal_answer, style='Quiz.TButton')
        self.show_btn.grid(row=0, column=0, padx=10)

        self.correct_btn = ttk.Button(button_frame, text='맞음 (Y)', command=lambda: self.handle_answer(True), style='Quiz.TButton')
        self.correct_btn.grid(row=0, column=1, padx=10)

        self.incorrect_btn = ttk.Button(button_frame, text='틀림 (N)', command=lambda: self.handle_answer(False), style='Quiz.TButton')
        self.incorrect_btn.grid(row=0, column=2, padx=10)

        bottom_bar = ttk.Frame(self)
        bottom_bar.pack(side='bottom', fill='x', padx=28, pady=(0, 20))

        info_frame = ttk.Frame(bottom_bar)
        info_frame.pack(side='left', anchor='w')

        self.stats_var = tk.StringVar(value='정답률: - | 마지막 학습: -')
        ttk.Label(info_frame, textvariable=self.stats_var, font=('Segoe UI', 9)).pack(anchor='w')
        ttk.Label(info_frame, textvariable=self.status_var, font=('Segoe UI', 9)).pack(anchor='w', pady=(2, 0))

        ttk.Button(bottom_bar, text='종료', command=self.quit_session, style='Quiz.TButton').pack(side='right')

        self._set_answer_buttons(active=False)
    def _bind_keys(self) -> None:
        self.bind("<y>", lambda _: self.handle_answer(True))
        self.bind("<Y>", lambda _: self.handle_answer(True))
        self.bind("<n>", lambda _: self.handle_answer(False))
        self.bind("<N>", lambda _: self.handle_answer(False))
        self.bind("<space>", lambda _: self.reveal_answer())
        self.bind("<Return>", lambda _: self.reveal_answer())
        self.bind("<KP_Enter>", lambda _: self.reveal_answer())

    def _set_answer_buttons(self, *, active: bool) -> None:
        state = tk.NORMAL if active else tk.DISABLED
        self.correct_btn.configure(state=state)
        self.incorrect_btn.configure(state=state)

    def update_overall_summary(self) -> None:
        tries = pd.to_numeric(self.session.sub["Tries"], errors="coerce").fillna(0)
        fails = pd.to_numeric(self.session.sub["Fails"], errors="coerce").fillna(0)
        total_tries = int(tries.sum())
        total_correct = int((tries - fails).clip(lower=0).sum())
        if total_tries > 0:
            rate_text = f"{total_correct / total_tries * 100:.0f}% ({total_correct}/{total_tries})"
        else:
            rate_text = "-"
        self.overall_var.set(f"전체 정답률: {rate_text}\nstep {self.session.cur_step}")

    def prepare_next_card(self) -> None:
        self.header_var.set(f"학습 범위: {self.session.sel_desc}")
        self.update_status(self._autosave_flag)
        self.update_overall_summary()
        self._autosave_flag = False
        self._answer_visible = False
        self.stats_var.set("정답률: - | 마지막 학습: -")
        self._set_answer_buttons(active=False)
        self.show_btn.configure(state=tk.NORMAL)

        pending = self.session.get_pending_init_card()
        if pending:
            idx, row = pending
            self.question_var.set(str(row[self.session.word_col]))
            self.answer_var.set("")
            self.show_btn.configure(state=tk.DISABLED)
            self._prompt_init_level(idx, row)
            return

        pick = self.session.choose_next_card()
        if pick is None:
            self.question_var.set("학습을 마쳤습니다.")
            self.answer_var.set("")
            self.show_btn.configure(state=tk.DISABLED)
            return

        idx, row = pick
        self._current_card = (idx, row)
        self.question_var.set(str(row[self.session.word_col]))
        self.answer_var.set("")
        correct_rate, last_seen = self.session.describe_card_stats(row)
        self.stats_var.set(f"정답률: {correct_rate} | 마지막 학습: {last_seen}")

    def _prompt_init_level(self, idx: int, row: pd.Series) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("초기 난이도 설정")
        dialog.transient(self)
        dialog.grab_set()

        ttk.Label(
            dialog,
            text=f"{row[self.session.word_col]}\n{row[self.session.meaning_col]}",
            anchor="center",
            justify="center",
        ).pack(padx=28, pady=(28, 16))

        choice = tk.StringVar()
        buttons: List[ttk.Radiobutton] = []
        original_level = (
            int(row.get("InitLevel"))
            if self.session._is_valid_init_level(row.get("InitLevel"))
            else None
        )

        for level, label in INIT_LEVEL_LABELS.items():
            btn = ttk.Radiobutton(
                dialog,
                text=f"{level}: {label}",
                value=str(level),
                variable=choice,
            )
            btn.pack(anchor="w", padx=32)
            buttons.append(btn)
            if original_level is not None and original_level == level:
                choice.set(str(level))

        def finalize_with(level: Optional[int]) -> None:
            if level is None:
                dialog.destroy()
                self.after(10, self.prepare_next_card)
                return
            self.session.set_init_level(idx, level)
            dialog.destroy()
            self.after(10, self.prepare_next_card)

        def confirm() -> None:
            value = choice.get()
            if not value:
                messagebox.showinfo("안내", "난이도를 선택해 주세요.", parent=dialog)
                return
            finalize_with(int(value))

        def choose(level: int) -> None:
            choice.set(str(level))
            confirm()

        action_frame = ttk.Frame(dialog)
        action_frame.pack(pady=(18, 24))
        ttk.Button(
            action_frame,
            text="닫기",
            command=lambda: finalize_with(
                int(choice.get()) if choice.get() else original_level
            ),
        ).pack(side="right", padx=6)
        ttk.Button(action_frame, text="저장", command=confirm).pack(side="right", padx=6)

        dialog.bind("<Return>", lambda _: confirm())
        for level in INIT_LEVEL_LABELS:
            dialog.bind(str(level), lambda _e, lv=level: choose(lv))
            dialog.bind(f"<KP_{level}>", lambda _e, lv=level: choose(lv))

        if buttons:
            buttons[0].focus_set()

        dialog.protocol(
            "WM_DELETE_WINDOW",
            lambda: finalize_with(
                int(choice.get()) if choice.get() else original_level
            ),
        )

        dialog.update_idletasks()
        parent_x = self.winfo_rootx()
        parent_y = self.winfo_rooty()
        parent_w = self.winfo_width()
        parent_h = self.winfo_height()
        dlg_w = dialog.winfo_width()
        dlg_h = dialog.winfo_height()
        screen_w = dialog.winfo_screenwidth()

        preferred_x = parent_x + parent_w + 20
        if preferred_x + dlg_w > screen_w:
            preferred_x = max(parent_x + parent_w - dlg_w - 20, parent_x + 20)

        pos_y = parent_y + max((parent_h - dlg_h) // 2, 0)
        dialog.geometry(f"+{int(preferred_x)}+{int(pos_y)}")

    def reveal_answer(self) -> None:
        if not self._current_card or self._answer_visible:
            return
        _, row = self._current_card
        self.question_var.set(str(row[self.session.meaning_col]))
        self.answer_var.set(f"단어: {row[self.session.word_col]}")
        self._answer_visible = True
        self._set_answer_buttons(active=True)
        self.show_btn.configure(state=tk.DISABLED)

    def handle_answer(self, correct: bool) -> None:
        if not self._current_card or not self._answer_visible:
            return
        idx, _ = self._current_card
        try:
            self.session.record_answer(idx, correct)
        except Exception as exc:
            messagebox.showerror("오류", f"결과를 저장하지 못했습니다.\n{exc}")
            return

        autosaved = False
        if self.session.needs_autosave():
            try:
                self.session.save()
                autosaved = True
            except Exception as exc:
                messagebox.showerror("오류", f"자동 저장에 실패했습니다.\n{exc}")

        self._current_card = None
        self._autosave_flag = autosaved
        self.prepare_next_card()

    def update_status(self, autosaved: bool = False) -> None:
        base = f"{self.session.sel_desc} | step {self.session.cur_step} | 진행 {self.session.asked}"
        if autosaved:
            base += " | 자동 저장 완료"
        self.status_var.set(base)

    def open_reconfigure(self) -> None:
        try:
            self.session.save()
        except Exception as exc:
            messagebox.showerror("오류", f"엑셀 저장에 실패했습니다.\n{exc}", parent=self)
            return

        dialog = tk.Toplevel(self)
        dialog.title("학습 범위 다시 설정")
        dialog.geometry("420x380")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        def apply(mode: str, chapter_spec: str, count_spec: str) -> None:
            try:
                new_session = StudySession(self.session.df.copy(), mode, chapter_spec, count_spec)
            except Exception as exc:
                messagebox.showerror("오류", f"세션을 준비하는 중 문제가 발생했습니다.\n{exc}", parent=dialog)
                return
            self.session = new_session
            self._current_card = None
            self._autosave_flag = False
            dialog.destroy()
            self.prepare_next_card()

        ConfigFrame(dialog, self.session.df.copy(), apply, on_cancel=dialog.destroy).pack(fill="both", expand=True)

    def quit_session(self) -> None:
        try:
            report = self.session.finalize()
        except Exception as exc:
            messagebox.showerror("오류", f"마지막 저장에 실패했습니다.\n{exc}")
            report = []
        else:
            if report:
                messagebox.showinfo("정답률 상위 10", "\n".join(report))
        self.destroy()


def main() -> None:
    try:
        df = pd.read_excel(core.FILE_PATH, sheet_name=core.SHEET_NAME)
    except Exception as exc:
        print(f"세션을 준비하는 중 오류가 발생했습니다: {exc}")
        return

    root = tk.Tk()
    root.title("영단어 학습 설정")
    root.geometry("560x440")
    root.minsize(560, 440)
    root.resizable(False, False)

    def start_session(mode: str, chapter_spec: str, count_spec: str) -> None:
        nonlocal root
        try:
            session = StudySession(df, mode, chapter_spec, count_spec)
        except Exception as exc:
            messagebox.showerror("오류", f"세션을 준비하는 중 문제가 발생했습니다.\n{exc}", parent=root)
            return
        root.destroy()
        app = StudyApp(session)
        app.mainloop()

    ConfigFrame(root, df, start_session).pack(fill="both", expand=True)
    root.mainloop()


if __name__ == "__main__":
    main()
