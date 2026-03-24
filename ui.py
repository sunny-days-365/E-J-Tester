"""
EJTester - 英語・日本語単語テスト (GUI版)
tkinter を使用（Python標準ライブラリ）
"""

import csv
import random
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass, field

# 間違えログ（mistake_log.py が同フォルダにある場合のみ使用）
try:
    import importlib.util as _ilu
    _ml_spec = _ilu.spec_from_file_location(
        "mistake_log",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "mistake_log.py"))
    _ml = _ilu.module_from_spec(_ml_spec)
    _ml_spec.loader.exec_module(_ml)
except Exception:
    _ml = None


# ──────────────────────────────────────────────
# データモデル
# ──────────────────────────────────────────────
@dataclass
class Word:
    number: int
    kanji: str
    romaji: str
    kana: str
    word_type: str
    meaning: str

    def display_japanese(self) -> str:
        if self.kana and self.kana != self.kanji:
            return f"{self.kanji}（{self.kana}）"
        return self.kanji

    def primary_meaning(self) -> str:
        return self.meaning.split(";")[0].strip()


@dataclass
class QuizResult:
    total: int = 0
    correct: int = 0
    wrong_words: list = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.correct / self.total * 100 if self.total else 0.0


# ──────────────────────────────────────────────
# CSV 読み込み
# ──────────────────────────────────────────────
def load_vocabulary(filepath: str) -> list[Word]:
    words: list[Word] = []
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            words.append(Word(
                number=int(row["#"]),
                kanji=row["ごい"].strip(),
                romaji=row["ローマ字"].strip(),
                kana=row["かな"].strip(),
                word_type=row["Type"].strip(),
                meaning=row["Meaning"].strip(),
            ))
    return words


# ──────────────────────────────────────────────
# カラー・フォント定数
# ──────────────────────────────────────────────
BG         = "#1e1e2e"
BG2        = "#2a2a3e"
BG3        = "#313145"
ACCENT     = "#7c6af7"
ACCENT2    = "#a78bfa"
GREEN      = "#4ade80"
RED        = "#f87171"
YELLOW     = "#fbbf24"
TEXT       = "#e2e8f0"
TEXT_DIM   = "#94a3b8"
BORDER     = "#3f3f5a"

FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_HEAD   = ("Segoe UI", 14, "bold")
FONT_BODY   = ("Segoe UI", 12)
FONT_BODY_B = ("Segoe UI", 12, "bold")
FONT_SMALL  = ("Segoe UI", 10)
FONT_KANJI  = ("Meiryo UI", 28, "bold")
FONT_KANA   = ("Meiryo UI", 14)


# ──────────────────────────────────────────────
# メインアプリケーション
# ──────────────────────────────────────────────
class EJTesterApp(tk.Tk):
    def __init__(self, words: list[Word]):
        super().__init__()
        self.words = words
        self.title("EJTester — 英語・日本語 単語テスト")
        self.geometry("860x640")
        self.minsize(720, 540)
        self.configure(bg=BG)
        self.resizable(True, True)

        # アイコン（エラーは無視）
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

        self._frame: tk.Frame | None = None
        self.show_menu()

    # ── フレーム切り替え ──────────────────────
    def switch_frame(self, frame_class, **kwargs):
        if self._frame:
            self._frame.destroy()
        self._frame = frame_class(self, **kwargs)
        self._frame.pack(fill="both", expand=True)

    def show_menu(self):
        self.switch_frame(MenuFrame)

    def show_word_list(self):
        self.switch_frame(WordListFrame, words=self.words)

    def show_flashcards(self):
        self.switch_frame(FlashCardFrame, words=self.words)

    def show_settings(self):
        self.switch_frame(SettingsFrame, words=self.words)

    def show_weak_settings(self):
        self.switch_frame(WeakWordSettingsFrame, words=self.words)

    def start_quiz(self, quiz_words: list[Word], mode: str, all_words: list[Word]):
        # 直前のテスト設定を記憶しておく（再テスト用）
        self._last_mode      = mode
        self._last_all_words = all_words
        self.switch_frame(ListQuizFrame,
                          quiz_words=quiz_words,
                          mode=mode,
                          all_words=all_words)

    def retry_wrong(self, wrong_words: list[Word]):
        """間違えた単語だけを、前回と同じモードで再テストする"""
        mode      = getattr(self, "_last_mode",      "1")
        all_words = getattr(self, "_last_all_words", wrong_words)
        quiz_words = list(wrong_words)
        random.shuffle(quiz_words)
        self.start_quiz(quiz_words, mode, all_words)

    def show_result(self, result: QuizResult):
        self.switch_frame(ResultFrame, result=result)


# ──────────────────────────────────────────────
# ユーティリティ ウィジェット
# ──────────────────────────────────────────────
def styled_button(parent, text, command, color=ACCENT, width=18, font=FONT_BODY_B):
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg=TEXT, activebackground=ACCENT2, activeforeground=TEXT,
        font=font, relief="flat", cursor="hand2",
        padx=16, pady=10, width=width, bd=0,
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=ACCENT2))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def section_label(parent, text, font=FONT_HEAD, fg=TEXT):
    return tk.Label(parent, text=text, bg=BG, fg=fg, font=font)


# ──────────────────────────────────────────────
# メニュー画面
# ──────────────────────────────────────────────
class MenuFrame(tk.Frame):
    def __init__(self, master: EJTesterApp):
        super().__init__(master, bg=BG)
        self.master: EJTesterApp

        # ヘッダー
        header = tk.Frame(self, bg=BG2, pady=28)
        header.pack(fill="x")
        tk.Label(header, text="🗾  EJTester", font=FONT_TITLE,
                 bg=BG2, fg=ACCENT2).pack()
        tk.Label(header, text="英語・日本語 単語テスト", font=FONT_BODY,
                 bg=BG2, fg=TEXT_DIM).pack(pady=(4, 0))

        # 単語数バッジ
        badge_frame = tk.Frame(self, bg=BG3, pady=12)
        badge_frame.pack(fill="x", padx=60, pady=(20, 0))
        tk.Label(badge_frame, text=f"📚  登録単語数:  {len(master.words)} 語",
                 font=FONT_BODY_B, bg=BG3, fg=YELLOW).pack()

        # ボタン
        btn_frame = tk.Frame(self, bg=BG, pady=30)
        btn_frame.pack()

        buttons = [
            ("▶  テストを開始する",       master.show_settings,        ACCENT),
            ("🔥  苦手単語テスト",         master.show_weak_settings,   "#7a2a2a"),
            ("🃏  フラッシュカード",       master.show_flashcards,      "#2d6a4f"),
            ("📖  単語一覧を見る",         master.show_word_list,       BG3),
            ("✖  終了",                   master.quit,                 "#4a4a6a"),
        ]
        for label, cmd, color in buttons:
            styled_button(btn_frame, label, cmd, color=color, width=24).pack(pady=8)

        # フッター
        tk.Label(self, text="vocabulary.csv を編集して単語を追加できます",
                 font=FONT_SMALL, bg=BG, fg=TEXT_DIM).pack(side="bottom", pady=10)


# ──────────────────────────────────────────────
# テスト設定画面
# ──────────────────────────────────────────────
class SettingsFrame(tk.Frame):
    def __init__(self, master: EJTesterApp, words: list[Word]):
        super().__init__(master, bg=BG)
        self.master: EJTesterApp
        self.all_words = words

        # ── タイトル ──
        tk.Label(self, text="テスト設定", font=FONT_TITLE,
                 bg=BG, fg=ACCENT2, pady=20).pack()

        inner = tk.Frame(self, bg=BG2, padx=40, pady=30)
        inner.pack(padx=60, fill="x")

        # ── 出題モード ──
        section_label(inner, "出題モード").grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.mode_var = tk.StringVar(value="1")
        modes = [
            ("1", "日本語 → 英語（4択）"),
            ("2", "日本語 → 英語（記述）"),
            ("3", "英語 → 日本語（記述）"),
            ("4", "ローマ字 → 日本語（4択）"),
            ("5", "ランダム（全モード混合）"),
        ]
        mode_frame = tk.Frame(inner, bg=BG2)
        mode_frame.grid(row=1, column=0, sticky="w", pady=(0, 20))
        for val, label in modes:
            tk.Radiobutton(
                mode_frame, text=label, variable=self.mode_var, value=val,
                bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2,
                activeforeground=ACCENT2, font=FONT_BODY, indicatoron=True,
            ).pack(anchor="w", pady=2)

        # ── 番号範囲 ──
        section_label(inner, "番号範囲").grid(row=2, column=0, sticky="w", pady=(0, 6))
        # 単語番号の最小・最大を自動取得
        all_nums = sorted(w.number for w in words)
        num_min, num_max = all_nums[0], all_nums[-1]
        # 100 単位でチェックボックスを生成
        import math
        chunk = 100
        chunks = []
        lo = num_min
        while lo <= num_max:
            hi = min(lo + chunk - 1, num_max)
            chunks.append((lo, hi))
            lo += chunk

        self.range_chunk_vars: dict[tuple, tk.BooleanVar] = {}
        range_chunk_frame = tk.Frame(inner, bg=BG2)
        range_chunk_frame.grid(row=3, column=0, sticky="w", pady=(0, 6))
        for lo, hi in chunks:
            cnt = sum(1 for w in words if lo <= w.number <= hi)
            var = tk.BooleanVar(value=True)
            self.range_chunk_vars[(lo, hi)] = var
            tk.Checkbutton(
                range_chunk_frame,
                text=f"  {lo} 〜 {hi}  （{cnt} 語）",
                variable=var,
                bg=BG2, fg=TEXT, selectcolor=BG3,
                activebackground=BG2, activeforeground=ACCENT2,
                font=FONT_BODY,
            ).pack(anchor="w", pady=2)

        # ── 出題範囲 ──
        section_label(inner, "出題範囲").grid(row=4, column=0, sticky="w", pady=(0, 6))
        self.range_var = tk.StringVar(value="all")
        ranges = [
            ("all",    f"すべての単語（選択した番号範囲内）"),
            ("random", "ランダムに選ぶ"),
            ("type",   "品詞で絞り込む"),
        ]
        range_frame = tk.Frame(inner, bg=BG2)
        range_frame.grid(row=5, column=0, sticky="w", pady=(0, 20))
        for val, label in ranges:
            tk.Radiobutton(
                range_frame, text=label, variable=self.range_var, value=val,
                bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2,
                activeforeground=ACCENT2, font=FONT_BODY,
                command=self._on_range_change,
            ).pack(anchor="w", pady=2)

        # ランダム問題数
        self.count_frame = tk.Frame(inner, bg=BG2)
        self.count_frame.grid(row=6, column=0, sticky="w", pady=(0, 10))
        tk.Label(self.count_frame, text="問題数:", font=FONT_BODY,
                 bg=BG2, fg=TEXT).pack(side="left")
        self.count_var = tk.IntVar(value=min(20, len(words)))
        self.count_spin = tk.Spinbox(
            self.count_frame, from_=1, to=len(words),
            textvariable=self.count_var, width=6,
            font=FONT_BODY, bg=BG3, fg=TEXT, buttonbackground=BG3,
            relief="flat", bd=4,
        )
        self.count_spin.pack(side="left", padx=8)
        tk.Label(self.count_frame, text=f"語 (最大 {len(words)} 語)",
                 font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left")
        self.count_frame.grid_remove()

        # 品詞フィルタ
        self.type_frame = tk.Frame(inner, bg=BG2)
        self.type_frame.grid(row=7, column=0, sticky="w", pady=(0, 10))
        self.type_vars: dict[str, tk.BooleanVar] = {}
        types = sorted(set(w.word_type for w in words))
        cols = 2
        for idx, t in enumerate(types):
            var = tk.BooleanVar(value=True)
            self.type_vars[t] = var
            count = sum(1 for w in words if w.word_type == t)
            cb = tk.Checkbutton(
                self.type_frame, text=f"{t}  ({count}語)",
                variable=var, bg=BG2, fg=TEXT,
                selectcolor=BG3, activebackground=BG2,
                activeforeground=ACCENT2, font=FONT_SMALL,
            )
            cb.grid(row=idx // cols, column=idx % cols, sticky="w", padx=(0, 20), pady=2)
        self.type_frame.grid_remove()

        # ── ボタン ──
        btn_row = tk.Frame(self, bg=BG, pady=20)
        btn_row.pack()
        styled_button(btn_row, "▶  テスト開始", self._start, ACCENT).pack(side="left", padx=10)
        styled_button(btn_row, "← 戻る", master.show_menu, BG3, width=10).pack(side="left", padx=10)

    def _on_range_change(self):
        val = self.range_var.get()
        self.count_frame.grid_remove()
        self.type_frame.grid_remove()
        if val == "random":
            self.count_frame.grid()
        elif val == "type":
            self.type_frame.grid()

    def _start(self):
        mode = self.mode_var.get()
        r = self.range_var.get()

        # ── 番号範囲でまず絞り込む ──
        selected_chunks = [
            (lo, hi) for (lo, hi), v in self.range_chunk_vars.items() if v.get()
        ]
        if not selected_chunks:
            messagebox.showwarning("警告", "少なくとも1つの番号範囲を選んでください。")
            return
        base_words = [
            w for w in self.all_words
            if any(lo <= w.number <= hi for lo, hi in selected_chunks)
        ]
        if not base_words:
            messagebox.showwarning("警告", "選択した番号範囲に単語がありません。")
            return

        if r == "all":
            quiz_words = list(base_words)
            random.shuffle(quiz_words)
        elif r == "random":
            n = self.count_var.get()
            quiz_words = random.sample(base_words, min(n, len(base_words)))
        else:  # type
            selected_types = [t for t, v in self.type_vars.items() if v.get()]
            if not selected_types:
                messagebox.showwarning("警告", "少なくとも1つの品詞を選んでください。")
                return
            filtered = [w for w in base_words if w.word_type in selected_types]
            if not filtered:
                messagebox.showwarning("警告", "選択した条件に一致する単語がありません。")
                return
            quiz_words = list(filtered)
            random.shuffle(quiz_words)

        self.master.start_quiz(quiz_words, mode, self.all_words)


# ──────────────────────────────────────────────
# 苦手単語テスト設定画面
# ──────────────────────────────────────────────
WEAK_RED = "#c0392b"   # 苦手テスト固有のアクセント色

class WeakWordSettingsFrame(tk.Frame):
    """間違え回数の多い単語を優先して出題する設定画面。"""

    def __init__(self, master: EJTesterApp, words: list[Word]):
        super().__init__(master, bg=BG)
        self.master: EJTesterApp
        self.all_words = words

        # ── 間違えログを読み込む ──
        self._log: dict[str, int] = _ml.load_log() if _ml else {}

        # 間違え回数付きの単語リスト（回数 > 0 のみ）
        self._weak: list[tuple[int, Word]] = sorted(
            [(self._log.get(str(w.number), 0), w)
             for w in words if self._log.get(str(w.number), 0) > 0],
            key=lambda x: -x[0]
        )

        # ── タイトル ──
        header = tk.Frame(self, bg=BG2, padx=20, pady=16)
        header.pack(fill="x")
        tk.Label(header, text="🔥  苦手単語テスト",
                 font=FONT_TITLE, bg=BG2, fg="#f87171").pack(side="left")

        # ── メインコンテンツ（左：設定 / 右：苦手単語プレビュー） ──
        content = tk.Frame(self, bg=BG)
        content.pack(fill="both", expand=True, padx=20, pady=10)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        # ── 左：設定パネル ──
        left = tk.Frame(content, bg=BG2, padx=24, pady=20)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        if not self._weak:
            tk.Label(left, text="まだ間違えた単語の\n記録がありません。",
                     font=FONT_BODY, bg=BG2, fg=TEXT_DIM,
                     justify="center").pack(pady=30)
            tk.Label(left, text="通常のテストで間違えると\nここに蓄積されます。",
                     font=FONT_SMALL, bg=BG2, fg=TEXT_DIM,
                     justify="center").pack()
            styled_button(left, "← 戻る", master.show_menu, BG3, width=14).pack(pady=20)
            # 右パネルは空
            tk.Frame(content, bg=BG).grid(row=0, column=1, sticky="nsew")
            return

        # ── 出題モード ──
        section_label(left, "出題モード", fg=TEXT).pack(anchor="w", pady=(0, 6))
        self.mode_var = tk.StringVar(value="1")
        modes = [
            ("1", "日本語 → 英語（4択）"),
            ("2", "日本語 → 英語（記述）"),
            ("3", "英語 → 日本語（記述）"),
            ("4", "ローマ字 → 日本語（4択）"),
            ("5", "ランダム（全モード混合）"),
        ]
        for val, label in modes:
            tk.Radiobutton(
                left, text=label, variable=self.mode_var, value=val,
                bg=BG2, fg=TEXT, selectcolor=BG3, activebackground=BG2,
                activeforeground=ACCENT2, font=FONT_BODY,
            ).pack(anchor="w", pady=2)

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=12)

        # ── 出題数・しきい値 ──
        section_label(left, "出題設定", fg=TEXT).pack(anchor="w", pady=(0, 8))

        count_row = tk.Frame(left, bg=BG2)
        count_row.pack(anchor="w", pady=4)
        tk.Label(count_row, text="出題数:", font=FONT_BODY, bg=BG2, fg=TEXT).pack(side="left")
        self.count_var = tk.IntVar(value=min(20, len(self._weak)))
        tk.Spinbox(
            count_row, from_=1, to=len(self._weak),
            textvariable=self.count_var, width=5,
            font=FONT_BODY, bg=BG3, fg=TEXT, buttonbackground=BG3,
            relief="flat", bd=4,
        ).pack(side="left", padx=8)
        tk.Label(count_row, text=f"語 (最大 {len(self._weak)} 語)",
                 font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left")

        min_row = tk.Frame(left, bg=BG2)
        min_row.pack(anchor="w", pady=4)
        tk.Label(min_row, text="最小間違え回数:", font=FONT_BODY, bg=BG2, fg=TEXT).pack(side="left")
        max_mistakes = self._weak[0][0] if self._weak else 1
        self.min_wrong_var = tk.IntVar(value=1)
        tk.Spinbox(
            min_row, from_=1, to=max(max_mistakes, 1),
            textvariable=self.min_wrong_var, width=4,
            font=FONT_BODY, bg=BG3, fg=TEXT, buttonbackground=BG3,
            relief="flat", bd=4,
            command=self._refresh_preview,
        ).pack(side="left", padx=8)
        tk.Label(min_row, text="回以上",
                 font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(side="left")

        tk.Frame(left, bg=BORDER, height=1).pack(fill="x", pady=12)

        # ── リセットボタン ──
        tk.Button(left, text="🗑  間違えログをリセット",
                  command=self._reset_log,
                  bg="#4a1a1a", fg=TEXT, font=FONT_SMALL,
                  relief="flat", cursor="hand2", padx=10, pady=6).pack(anchor="w", pady=(0, 10))

        # ── アクションボタン ──
        btn_row = tk.Frame(left, bg=BG2)
        btn_row.pack(anchor="w", pady=(4, 0))
        styled_button(btn_row, "🔥  テスト開始", self._start,
                      WEAK_RED, width=14).pack(side="left", padx=(0, 8))
        styled_button(btn_row, "← 戻る", master.show_menu,
                      BG3, width=8).pack(side="left")

        # ── 右：苦手単語プレビュー ──
        right = tk.Frame(content, bg=BG2, padx=16, pady=16)
        right.grid(row=0, column=1, sticky="nsew")

        tk.Label(right, text="📊  間違え回数ランキング",
                 font=FONT_HEAD, bg=BG2, fg=ACCENT2).pack(anchor="w", pady=(0, 8))

        list_frame = tk.Frame(right, bg=BG2)
        list_frame.pack(fill="both", expand=True)

        vsb = tk.Scrollbar(list_frame)
        vsb.pack(side="right", fill="y")

        cols = ("No.", "日本語", "ローマ字", "意味", "間違え回数")
        self.preview_tree = ttk.Treeview(
            list_frame, columns=cols, show="headings",
            yscrollcommand=vsb.set, height=16)
        vsb.config(command=self.preview_tree.yview)

        s = ttk.Style()
        s.configure("Weak.Treeview",
                    background=BG2, foreground=TEXT,
                    fieldbackground=BG2, rowheight=26, font=FONT_SMALL)
        s.configure("Weak.Treeview.Heading",
                    background=BG3, foreground=ACCENT2, font=FONT_SMALL)
        s.map("Weak.Treeview", background=[("selected", BG3)])
        self.preview_tree.config(style="Weak.Treeview")

        col_widths = {"No.": 40, "日本語": 130, "ローマ字": 110,
                      "意味": 250, "間違え回数": 80}
        for col in cols:
            self.preview_tree.heading(col, text=col)
            self.preview_tree.column(col, width=col_widths[col], anchor="w")
        self.preview_tree.pack(side="left", fill="both", expand=True)

        # タグ：回数に応じた色
        self.preview_tree.tag_configure("high",   foreground=RED)
        self.preview_tree.tag_configure("medium", foreground=YELLOW)
        self.preview_tree.tag_configure("low",    foreground=TEXT)

        self._refresh_preview()

    def _refresh_preview(self):
        """しきい値に応じてプレビューリストを更新する"""
        if not hasattr(self, "preview_tree"):
            return
        self.preview_tree.delete(*self.preview_tree.get_children())
        try:
            min_w = self.min_wrong_var.get()
        except Exception:
            min_w = 1
        filtered = [(cnt, w) for cnt, w in self._weak if cnt >= min_w]
        for cnt, w in filtered:
            if cnt >= 5:
                tag = "high"
            elif cnt >= 3:
                tag = "medium"
            else:
                tag = "low"
            self.preview_tree.insert("", "end",
                values=(w.number, w.display_japanese(), w.romaji, w.meaning, f"❌ {cnt}回"),
                tags=(tag,))
        # 出題数の最大値を更新
        if hasattr(self, "count_var"):
            n = max(1, len(filtered))
            self.count_var.set(min(self.count_var.get(), n))

    def _reset_log(self):
        if not messagebox.askyesno("確認",
                "間違えログを全てリセットしますか？\nこの操作は元に戻せません。"):
            return
        if _ml:
            _ml.reset_log()
        self._log = {}
        self._weak = []
        messagebox.showinfo("完了", "間違えログをリセットしました。")
        self.master.show_menu()

    def _start(self):
        try:
            min_w = self.min_wrong_var.get()
            n     = self.count_var.get()
        except Exception:
            return
        filtered = [(cnt, w) for cnt, w in self._weak if cnt >= min_w]
        if not filtered:
            messagebox.showwarning("警告",
                "条件に一致する苦手単語がありません。\nしきい値を下げてみてください。")
            return
        # 間違え回数の多い順に並べ、上位 n 件を出題
        quiz_words = [w for _, w in filtered[:n]]
        random.shuffle(quiz_words)
        mode = self.mode_var.get()
        self.master.start_quiz(quiz_words, mode, self.all_words)


# ──────────────────────────────────────────────
# クイズ画面
# ──────────────────────────────────────────────
class QuizFrame(tk.Frame):
    def __init__(self, master: EJTesterApp,
                 quiz_words: list[Word], mode: str, all_words: list[Word]):
        super().__init__(master, bg=BG)
        self.master: EJTesterApp
        self.quiz_words = quiz_words
        self.mode = mode
        self.all_words = all_words
        self.result = QuizResult()
        self.index = 0
        self.answered = False
        self.choice_btns: list[tk.Button] = []

        self._build_ui()
        self._load_question()

    # ── UI 構築 ──
    def _build_ui(self):
        total = len(self.quiz_words)

        # ── トップバー ──
        top = tk.Frame(self, bg=BG2, padx=20, pady=12)
        top.pack(fill="x")

        left_top = tk.Frame(top, bg=BG2)
        left_top.pack(side="left")
        self.lbl_progress = tk.Label(left_top, text="", font=FONT_BODY_B, bg=BG2, fg=TEXT)
        self.lbl_progress.pack(anchor="w")

        self.lbl_score = tk.Label(left_top, text="", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM)
        self.lbl_score.pack(anchor="w")

        # プログレスバー
        bar_frame = tk.Frame(top, bg=BG2)
        bar_frame.pack(side="right", fill="x", expand=True, padx=(20, 0))
        self.progress_var = tk.DoubleVar(value=0)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Accent.Horizontal.TProgressbar",
                        troughcolor=BG3, background=ACCENT, thickness=10)
        self.progressbar = ttk.Progressbar(
            bar_frame, variable=self.progress_var,
            maximum=total, style="Accent.Horizontal.TProgressbar", length=300)
        self.progressbar.pack(side="right", pady=8)

        # ── 問題エリア ──
        q_frame = tk.Frame(self, bg=BG3, padx=30, pady=24)
        q_frame.pack(fill="x", padx=30, pady=(20, 10))

        self.lbl_mode_hint = tk.Label(q_frame, text="", font=FONT_SMALL,
                                      bg=BG3, fg=TEXT_DIM)
        self.lbl_mode_hint.pack(anchor="w")

        self.lbl_question = tk.Label(q_frame, text="", font=FONT_KANJI,
                                     bg=BG3, fg=TEXT, wraplength=700, justify="center")
        self.lbl_question.pack(pady=(8, 4))

        self.lbl_sub = tk.Label(q_frame, text="", font=FONT_KANA,
                                bg=BG3, fg=TEXT_DIM)
        self.lbl_sub.pack()

        self.lbl_hint = tk.Label(q_frame, text="", font=FONT_SMALL,
                                 bg=BG3, fg=TEXT_DIM)
        self.lbl_hint.pack(pady=(4, 0))

        # ── 回答エリア ──
        self.answer_frame = tk.Frame(self, bg=BG, padx=30, pady=10)
        self.answer_frame.pack(fill="x")

        # 記述入力
        self.entry_frame = tk.Frame(self.answer_frame, bg=BG)
        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(
            self.entry_frame, textvariable=self.entry_var,
            font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=8, width=40,
        )
        self.entry.pack(side="left", ipady=6)
        self.btn_submit = styled_button(
            self.entry_frame, "回答する", self._submit_text, ACCENT, width=10)
        self.btn_submit.pack(side="left", padx=10)
        self.entry.bind("<Return>", lambda e: self._submit_text())

        # 4択ボタン
        self.choice_frame = tk.Frame(self.answer_frame, bg=BG)
        for _ in range(4):
            btn = tk.Button(
                self.choice_frame, text="", font=FONT_BODY,
                bg=BG3, fg=TEXT, activebackground=BG2, activeforeground=TEXT,
                relief="flat", cursor="hand2", wraplength=360, justify="left",
                padx=16, pady=12, bd=0,
            )
            btn.pack(fill="x", pady=5)
            self.choice_btns.append(btn)

        # ── フィードバック ──
        self.lbl_feedback = tk.Label(self, text="", font=FONT_BODY_B,
                                     bg=BG, fg=GREEN, pady=4)
        self.lbl_feedback.pack()

        self.lbl_answer_reveal = tk.Label(self, text="", font=FONT_BODY,
                                          bg=BG, fg=TEXT_DIM, wraplength=700)
        self.lbl_answer_reveal.pack()

        # ── 次へボタン ──
        self.btn_next = styled_button(self, "次の問題 →", self._next_question, ACCENT, width=16)
        self.btn_next.pack(pady=12)
        self.btn_next.pack_forget()

    # ── 問題読み込み ──
    def _load_question(self):
        self.answered = False
        self.lbl_feedback.config(text="")
        self.lbl_answer_reveal.config(text="")
        self.btn_next.pack_forget()
        self.entry_frame.pack_forget()
        self.choice_frame.pack_forget()

        total = len(self.quiz_words)
        i = self.index
        q = self.quiz_words[i]

        # プログレス更新
        self.progress_var.set(i)
        self.lbl_progress.config(text=f"問題  {i + 1} / {total}")
        self.lbl_score.config(
            text=f"✅ 正解 {self.result.correct}   ❌ 不正解 {self.result.correct + (i - self.result.correct)- (i - self.result.correct)}")
        self.lbl_score.config(
            text=f"✅ 正解 {self.result.correct}  ❌ 不正解 {i - self.result.correct}")

        # モード決定
        mode = self.mode if self.mode != "5" else random.choice(["1", "2", "3", "4"])
        self._current_mode = mode
        self._current_word = q

        mode_hints = {
            "1": "日本語 → 英語（4択）",
            "2": "日本語 → 英語（記述）",
            "3": "英語 → 日本語（記述）",
            "4": "ローマ字 → 日本語（4択）",
        }
        self.lbl_mode_hint.config(text=f"モード: {mode_hints[mode]}  ｜  品詞: {q.word_type}")

        if mode == "1":
            # 日本語 → 英語 4択
            self.lbl_question.config(text=q.display_japanese(), font=FONT_KANJI)
            self.lbl_sub.config(text=f"（{q.romaji}）")
            self.lbl_hint.config(text="")
            self._show_choices_meaning(q)

        elif mode == "2":
            # 日本語 → 英語 記述
            self.lbl_question.config(text=q.display_japanese(), font=FONT_KANJI)
            self.lbl_sub.config(text=f"（{q.romaji}）")
            self.lbl_hint.config(text="英語で意味を入力してください")
            self._show_entry()

        elif mode == "3":
            # 英語 → 日本語 記述
            self.lbl_question.config(text=q.meaning, font=FONT_BODY_B)
            self.lbl_sub.config(text="")
            self.lbl_hint.config(text="日本語（漢字・ひらがな・カタカナ・ローマ字）を入力してください")
            self._show_entry()

        elif mode == "4":
            # ローマ字 → 日本語 4択
            self.lbl_question.config(text=q.romaji, font=FONT_KANJI)
            self.lbl_sub.config(text=f"意味: {q.primary_meaning()}")
            self.lbl_hint.config(text="")
            self._show_choices_japanese(q)

    def _show_entry(self):
        self.entry_var.set("")
        self.entry_frame.pack(pady=10)
        self.entry.focus_set()

    def _show_choices_meaning(self, q: Word):
        others = [w for w in self.all_words if w.number != q.number]
        distractors = random.sample(others, min(3, len(others)))
        choices = [q.meaning] + [d.meaning for d in distractors]
        random.shuffle(choices)
        self._choices = choices
        self.choice_frame.pack(fill="x", pady=10)
        for i, (btn, text) in enumerate(zip(self.choice_btns, choices)):
            btn.config(
                text=f"  {i+1}.  {text}", bg=BG3, fg=TEXT,
                command=lambda c=text: self._submit_choice_meaning(c),
                state="normal",
            )
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=BG2) if b["state"] == "normal" else None)
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BG3) if b["state"] != "disabled" and b["bg"] not in (GREEN, RED) else None)

    def _show_choices_japanese(self, q: Word):
        others = [w for w in self.all_words if w.number != q.number]
        distractors = random.sample(others, min(3, len(others)))
        choices = [q.display_japanese()] + [d.display_japanese() for d in distractors]
        random.shuffle(choices)
        self._choices_jp = choices
        self.choice_frame.pack(fill="x", pady=10)
        for i, (btn, text) in enumerate(zip(self.choice_btns, choices)):
            btn.config(
                text=f"  {i+1}.  {text}", bg=BG3, fg=TEXT,
                command=lambda c=text: self._submit_choice_jp(c),
                state="normal",
            )
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=BG2) if b["state"] == "normal" else None)
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=BG3) if b["state"] != "disabled" and b["bg"] not in (GREEN, RED) else None)

    # ── 回答処理 ──
    def _submit_text(self):
        if self.answered:
            return
        q = self._current_word
        answer = self.entry_var.get().strip()
        if not answer:
            return
        self.answered = True
        self.entry.config(state="disabled")
        self.btn_submit.config(state="disabled")

        if self._current_mode == "2":
            meanings = [m.strip().lower() for m in q.meaning.replace(";", ",").split(",")]
            ok = any(answer.lower() == m for m in meanings) or answer.lower() in q.meaning.lower()
            correct_text = q.meaning
        else:  # mode 3
            correct_answers = [a for a in [q.kanji, q.kana, q.romaji] if a]
            ok = answer in correct_answers
            correct_text = f"{q.display_japanese()}（{q.romaji}）"

        self._show_feedback(ok, correct_text)

    def _submit_choice_meaning(self, selected: str):
        if self.answered:
            return
        self.answered = True
        q = self._current_word
        ok = selected == q.meaning
        for btn in self.choice_btns:
            btn.config(state="disabled")
            if btn["text"].endswith(q.meaning) or q.meaning in btn["text"]:
                btn.config(bg=GREEN, fg=BG)
            elif btn["text"].endswith(selected) or selected in btn["text"]:
                if not ok:
                    btn.config(bg=RED, fg=TEXT)
        self._show_feedback(ok, q.meaning, highlight_done=True)

    def _submit_choice_jp(self, selected: str):
        if self.answered:
            return
        self.answered = True
        q = self._current_word
        correct = q.display_japanese()
        ok = selected == correct
        for btn in self.choice_btns:
            btn.config(state="disabled")
            if correct in btn["text"]:
                btn.config(bg=GREEN, fg=BG)
            elif selected in btn["text"] and not ok:
                btn.config(bg=RED, fg=TEXT)
        self._show_feedback(ok, correct, highlight_done=True)

    def _show_feedback(self, ok: bool, correct_text: str, highlight_done: bool = False):
        q = self._current_word
        if ok:
            self.result.correct += 1
            self.lbl_feedback.config(text="✅  正解！", fg=GREEN)
            self.lbl_answer_reveal.config(
                text=f"{q.display_japanese()}（{q.romaji}） → {q.meaning}", fg=TEXT_DIM)
        else:
            self.result.wrong_words.append(q)
            self.lbl_feedback.config(text="❌  不正解", fg=RED)
            self.lbl_answer_reveal.config(
                text=f"正解は:  {correct_text}", fg=YELLOW)
        self.result.total += 1
        self.btn_next.pack(pady=12)
        # ラスト問題なら「結果を見る」に変更
        if self.index >= len(self.quiz_words) - 1:
            self.btn_next.config(text="結果を見る 📊", command=self._finish)

    # ── 次の問題 ──
    def _next_question(self):
        self.index += 1
        if self.index >= len(self.quiz_words):
            self._finish()
        else:
            self._load_question()

    def _finish(self):
        self.progress_var.set(len(self.quiz_words))
        self.master.show_result(self.result)


# ──────────────────────────────────────────────
# リスト式テスト画面（インライン入力・Tab移動対応）
# ──────────────────────────────────────────────
class ListQuizFrame(tk.Frame):
    """全問をスクロール可能なグリッドで表示。
    各行に Entry（記述）または OptionMenu（4択）を直接配置。
    Tab / Shift+Tab で次・前の入力欄へ移動。
    Enter で採点。全問採点後に「結果を見る」が有効化。
    """

    ROW_H   = 36   # 1行の高さ(px)
    PAD_X   = 6
    PAD_Y   = 2

    def __init__(self, master: EJTesterApp,
                 quiz_words: list[Word], mode: str, all_words: list[Word]):
        super().__init__(master, bg=BG)
        self.master: EJTesterApp
        self.quiz_words = quiz_words
        self.mode = mode
        self.all_words = all_words
        self.result = QuizResult()
        self.states: list[str | None] = [None] * len(quiz_words)
        self.modes: list[str] = [
            mode if mode != "5" else random.choice(["1", "2", "3", "4"])
            for _ in quiz_words
        ]

        # 各行のウィジェット参照
        self.entries:      list[tk.Entry | None]       = [None] * len(quiz_words)
        self.entry_vars:   list[tk.StringVar]           = [tk.StringVar() for _ in quiz_words]
        self.result_labels: list[tk.Label | None]       = [None] * len(quiz_words)
        self.row_frames:   list[tk.Frame]               = []

        self._build_ui()

    # ── UI 構築 ──────────────────────────────
    def _build_ui(self):
        total = len(self.quiz_words)

        # ── トップバー ──
        top = tk.Frame(self, bg=BG2, padx=16, pady=10)
        top.pack(fill="x")

        left = tk.Frame(top, bg=BG2)
        left.pack(side="left")
        mode_labels = {
            "1": "日本語 → 英語（4択）",
            "2": "日本語 → 英語（記述）",
            "3": "英語 → 日本語（記述）",
            "4": "ローマ字 → 日本語（4択）",
            "5": "ランダム（全モード混合）",
        }
        tk.Label(left, text=f"📝  {mode_labels.get(self.mode, '')}",
                 font=FONT_HEAD, bg=BG2, fg=ACCENT2).pack(anchor="w")
        tk.Label(left, text="Tab / Shift+Tab で移動　Enter で採点",
                 font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).pack(anchor="w")

        self.lbl_score = tk.Label(
            top, text=f"✅ 0  ❌ 0  ／  残 {total}",
            font=FONT_BODY_B, bg=BG2, fg=TEXT)
        self.lbl_score.pack(side="right", padx=8)

        # プログレスバー
        bar_outer = tk.Frame(self, bg=BG, pady=3)
        bar_outer.pack(fill="x", padx=16)
        self.progress_var = tk.DoubleVar(value=0)
        s = ttk.Style()
        s.configure("LQ.Horizontal.TProgressbar",
                    troughcolor=BG3, background=ACCENT, thickness=7)
        ttk.Progressbar(bar_outer, variable=self.progress_var,
                        maximum=total,
                        style="LQ.Horizontal.TProgressbar").pack(fill="x")

        # ── ヘッダー行 ──
        header = tk.Frame(self, bg=BG3)
        header.pack(fill="x", padx=16, pady=(4, 0))
        self._make_header(header)

        # ── スクロール可能なリスト ──
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=BG)
        self._canvas_win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>",
                        lambda e: self.canvas.configure(
                            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(
                             self._canvas_win, width=e.width))
        # マウスホイールスクロール（フレーム破棄時に解除）
        def _on_mousewheel(e):
            if self.canvas.winfo_exists():
                self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.bind("<Destroy>", lambda e: self.canvas.unbind_all("<MouseWheel>")
                  if e.widget is self else None)

        # 各行を生成
        self._populate_rows()

        # ── 下部ボタン ──
        bottom = tk.Frame(self, bg=BG, pady=8)
        bottom.pack(fill="x", padx=16)
        self.btn_finish = tk.Button(
            bottom,
            text="📊 結果を見る（未回答をスキップ）",
            command=self._finish,
            bg="#4a3a6a", fg=TEXT, font=FONT_BODY,
            relief="flat", cursor="hand2", padx=14, pady=7)
        self.btn_finish.pack(side="right")
        styled_button(bottom, "← 戻る", self.master.show_menu,
                      BG3, width=10).pack(side="left")

        # 最初の入力欄にフォーカス
        self.after(100, self._focus_first)

    # ── ヘッダー ──────────────────────────────
    def _make_header(self, parent: tk.Frame):
        # モードに関わらず共通ヘッダー
        cols = self._col_defs()
        for col_def in cols:
            tk.Label(parent, text=col_def["head"],
                     font=FONT_SMALL, bg=BG3, fg=ACCENT2,
                     width=col_def["w"], anchor="w",
                     padx=self.PAD_X, pady=4).pack(side="left")

    def _col_defs(self) -> list[dict]:
        """モードに応じた列定義（head=ヘッダ文字列, w=幅文字数）"""
        m = self.mode
        if m in ("1", "2"):
            return [
                {"head": "No.",    "w":  4},
                {"head": "日本語", "w": 14},
                {"head": "ローマ字","w": 12},
                {"head": "品詞",   "w": 14},
                {"head": "回答",   "w": 20},
                {"head": "結果",   "w": 28},
            ]
        elif m == "3":
            return [
                {"head": "No.",       "w":  4},
                {"head": "英語の意味","w": 28},
                {"head": "品詞",      "w": 14},
                {"head": "回答",      "w": 18},
                {"head": "結果",      "w": 24},
            ]
        elif m == "4":
            return [
                {"head": "No.",       "w":  4},
                {"head": "ローマ字",  "w": 12},
                {"head": "英語の意味","w": 22},
                {"head": "品詞",      "w": 12},
                {"head": "回答",      "w": 16},
                {"head": "結果",      "w": 20},
            ]
        else:  # random
            return [
                {"head": "No.",  "w":  4},
                {"head": "問題", "w": 22},
                {"head": "品詞", "w": 12},
                {"head": "モード","w": 12},
                {"head": "回答", "w": 18},
                {"head": "結果", "w": 22},
            ]

    # ── 行生成 ────────────────────────────────
    def _populate_rows(self):
        col_defs = self._col_defs()
        mode_short = {"1": "JP→EN(択)", "2": "JP→EN(記)",
                      "3": "EN→JP(記)", "4": "RM→JP(択)"}

        for idx, (w, m) in enumerate(zip(self.quiz_words, self.modes)):
            bg = BG if idx % 2 == 0 else BG2
            row = tk.Frame(self.inner, bg=bg)
            row.pack(fill="x")
            self.row_frames.append(row)

            # ── 問題セル（モードに応じて内容が変わる）──
            if self.mode in ("1", "2"):
                cells = [str(w.number), w.display_japanese(), w.romaji, w.word_type]
            elif self.mode == "3":
                cells = [str(w.number), w.meaning, w.word_type]
            elif self.mode == "4":
                cells = [str(w.number), w.romaji, w.primary_meaning(), w.word_type]
            else:  # random
                if m in ("1", "2"):   q_text = w.display_japanese()
                elif m == "3":        q_text = w.meaning
                else:                 q_text = w.romaji
                cells = [str(w.number), q_text, w.word_type, mode_short.get(m, m)]

            for i, (cell_text, col_def) in enumerate(zip(cells, col_defs)):
                tk.Label(row, text=cell_text,
                         font=FONT_SMALL, bg=bg, fg=TEXT,
                         width=col_def["w"], anchor="w",
                         padx=self.PAD_X, pady=self.PAD_Y,
                         wraplength=col_def["w"] * 7).pack(side="left")

            ans_col  = col_defs[-2]   # 「回答」列定義
            res_col  = col_defs[-1]   # 「結果」列定義

            # ── 回答ウィジェット ──
            if m in ("1", "4"):
                # 4択 → OptionMenu
                choices = (self._make_meaning_choices(w) if m == "1"
                           else self._make_jp_choices(w))
                var = self.entry_vars[idx]
                var.set("── 選択 ──")
                om = tk.OptionMenu(row, var, *choices)
                om.config(bg=BG3, fg=TEXT, activebackground=BG2,
                          activeforeground=TEXT, font=FONT_SMALL,
                          relief="flat", highlightthickness=0,
                          width=ans_col["w"] - 2, anchor="w")
                om["menu"].config(bg=BG3, fg=TEXT, font=FONT_SMALL)
                om.pack(side="left", padx=(self.PAD_X, 0), pady=self.PAD_Y)
                # Tab/Shift+Tab バインド
                om.bind("<Tab>",       lambda e, i=idx: self._focus_next(i))
                om.bind("<Shift-Tab>", lambda e, i=idx: self._focus_prev(i))
                om.bind("<Return>",    lambda e, i=idx: self._submit(i))
                self.entries[idx] = om   # type: ignore[assignment]
            else:
                # 記述 → Entry
                ent = tk.Entry(row, textvariable=self.entry_vars[idx],
                               font=FONT_SMALL, bg=BG3, fg=TEXT,
                               insertbackground=TEXT, relief="flat",
                               bd=4, width=ans_col["w"])
                ent.pack(side="left", padx=(self.PAD_X, 0),
                         pady=self.PAD_Y, ipady=3)
                ent.bind("<Return>",    lambda e, i=idx: self._submit(i))
                ent.bind("<Tab>",       lambda e, i=idx: (self._submit_if_filled(i),
                                                           self._focus_next(i), "break")[2])
                ent.bind("<Shift-Tab>", lambda e, i=idx: (self._submit_if_filled(i),
                                                           self._focus_prev(i), "break")[2])
                self.entries[idx] = ent

            # ── 結果ラベル（最初は空） ──
            lbl = tk.Label(row, text="", font=FONT_SMALL, bg=bg, fg=TEXT,
                           width=res_col["w"], anchor="w",
                           padx=self.PAD_X, pady=self.PAD_Y,
                           wraplength=res_col["w"] * 7)
            lbl.pack(side="left")
            self.result_labels[idx] = lbl

    # ── フォーカス移動 ────────────────────────
    def _focus_first(self):
        for ent in self.entries:
            if ent:
                ent.focus_set()
                break

    def _focus_next(self, idx: int):
        for i in range(idx + 1, len(self.entries)):
            if self.states[i] is None and self.entries[i]:
                self.entries[i].focus_set()
                self._scroll_to(i)
                return "break"
        return "break"

    def _focus_prev(self, idx: int):
        for i in range(idx - 1, -1, -1):
            if self.states[i] is None and self.entries[i]:
                self.entries[i].focus_set()
                self._scroll_to(i)
                return "break"
        return "break"

    def _scroll_to(self, idx: int):
        """指定行がビューに入るようスクロール"""
        self.inner.update_idletasks()
        row = self.row_frames[idx]
        y0 = row.winfo_y()
        y1 = y0 + row.winfo_height()
        total_h = self.inner.winfo_height()
        if total_h == 0:
            return
        self.canvas.yview_moveto(max(0.0, (y0 - 40) / total_h))

    # ── 4択選択肢生成 ─────────────────────────
    def _make_meaning_choices(self, w: Word) -> list[str]:
        others = [x for x in self.all_words if x.number != w.number]
        distractors = random.sample(others, min(3, len(others)))
        choices = [w.meaning] + [d.meaning for d in distractors]
        random.shuffle(choices)
        return choices

    def _make_jp_choices(self, w: Word) -> list[str]:
        others = [x for x in self.all_words if x.number != w.number]
        distractors = random.sample(others, min(3, len(others)))
        choices = [w.display_japanese()] + [d.display_japanese() for d in distractors]
        random.shuffle(choices)
        return choices

    # ── 採点 ──────────────────────────────────
    def _submit_if_filled(self, idx: int):
        """Tabで移動する前に、入力済みなら採点する"""
        if self.states[idx] is None and self.entry_vars[idx].get().strip():
            self._submit(idx)

    def _submit(self, idx: int):
        if self.states[idx] is not None:
            return
        w  = self.quiz_words[idx]
        m  = self.modes[idx]
        ans = self.entry_vars[idx].get().strip()

        if not ans or ans == "── 選択 ──":
            return

        # 正誤判定
        if m == "1":
            ok = (ans == w.meaning)
            correct_val = w.meaning
        elif m == "2":
            meanings = [x.strip().lower()
                        for x in w.meaning.replace(";", ",").split(",")]
            ok = any(ans.lower() == x for x in meanings) or ans.lower() in w.meaning.lower()
            correct_val = w.meaning
        elif m == "3":
            ok = ans in [a for a in [w.kanji, w.kana, w.romaji] if a]
            correct_val = w.display_japanese()
        else:  # 4
            ok = (ans == w.display_japanese())
            correct_val = w.display_japanese()

        self.states[idx] = "correct" if ok else "wrong"
        if ok:
            self.result.correct += 1
        else:
            self.result.wrong_words.append(w)
        self.result.total += 1

        # 入力欄を無効化・色変え
        ent = self.entries[idx]
        row = self.row_frames[idx]
        row_bg = "#1a3a2a" if ok else "#3a1a1a"
        row.config(bg=row_bg)
        for child in row.winfo_children():
            try:
                child.config(bg=row_bg)
            except tk.TclError:
                pass
        if ent:
            try:
                ent.config(state="disabled",
                           disabledbackground=row_bg,
                           disabledforeground=GREEN if ok else RED)
            except tk.TclError:
                ent.config(state="disabled")

        # 結果ラベル更新
        lbl = self.result_labels[idx]
        if lbl:
            if ok:
                lbl.config(text="✅ 正解", fg=GREEN, bg=row_bg)
            else:
                lbl.config(text=f"❌ {correct_val}", fg=RED, bg=row_bg)

        # スコア・プログレス更新
        answered  = sum(1 for s in self.states if s is not None)
        remaining = len(self.quiz_words) - answered
        self.lbl_score.config(
            text=f"✅ {self.result.correct}  "
                 f"❌ {self.result.total - self.result.correct}  ／  残 {remaining}")
        self.progress_var.set(answered)

        if remaining == 0:
            self.btn_finish.config(text="📊 結果を見る", bg=ACCENT)

        # 次の未回答欄へ自動移動
        self._focus_next(idx)

    # ── 結果へ ────────────────────────────────
    def _finish(self):
        for idx, (s, w) in enumerate(zip(self.states, self.quiz_words)):
            if s is None:
                self.result.total += 1
                self.result.wrong_words.append(w)
                self.states[idx] = "wrong"
                lbl = self.result_labels[idx]
                if lbl:
                    lbl.config(text=f"❌ {w.meaning}", fg=RED)
        # 間違えログを更新
        if _ml is not None:
            wrong_nums   = [w.number for w in self.result.wrong_words]
            correct_nums = [w.number for w in self.quiz_words
                            if w not in self.result.wrong_words]
            _ml.record_results(wrong_nums, correct_nums)
        self.master.show_result(self.result)


# ──────────────────────────────────────────────
# フラッシュカード画面
# ──────────────────────────────────────────────
class FlashCardFrame(tk.Frame):
    """全単語をランダム順にフラッシュカード形式で表示する。
    カードをクリック（または Space）すると表裏が切り替わる。
    ← / → キー、またはボタンで前後に移動。
    """

    CARD_BG_FRONT = "#2d2d4e"
    CARD_BG_BACK  = "#1e3a2f"

    def __init__(self, master: EJTesterApp, words: list[Word]):
        super().__init__(master, bg=BG)
        self.master: EJTesterApp
        self.words = list(words)
        random.shuffle(self.words)
        self.index = 0
        self.showing_front = True   # True=日本語面, False=英語面

        self._build_ui()
        self._show_card()

    # ── UI 構築 ──────────────────────────────
    def _build_ui(self):
        # トップバー
        top = tk.Frame(self, bg=BG2, padx=20, pady=12)
        top.pack(fill="x")
        tk.Label(top, text="🃏  フラッシュカード", font=FONT_HEAD,
                 bg=BG2, fg=ACCENT2).pack(side="left")

        right_top = tk.Frame(top, bg=BG2)
        right_top.pack(side="right")
        self.lbl_progress = tk.Label(right_top, text="", font=FONT_BODY_B,
                                      bg=BG2, fg=TEXT)
        self.lbl_progress.pack(side="left", padx=(0, 16))

        # シャッフルボタン
        tk.Button(right_top, text="🔀 シャッフル", command=self._shuffle,
                  bg=BG3, fg=TEXT, font=FONT_SMALL, relief="flat",
                  cursor="hand2", padx=10, pady=4).pack(side="left", padx=4)

        # プログレスバー
        bar_outer = tk.Frame(self, bg=BG, pady=6)
        bar_outer.pack(fill="x", padx=30)
        self.progress_var = tk.DoubleVar(value=0)
        style = ttk.Style()
        style.configure("FC.Horizontal.TProgressbar",
                        troughcolor=BG3, background="#2d6a4f", thickness=8)
        ttk.Progressbar(bar_outer, variable=self.progress_var,
                        maximum=len(self.words),
                        style="FC.Horizontal.TProgressbar").pack(fill="x")

        # ── カードエリア ──
        card_outer = tk.Frame(self, bg=BG, pady=10)
        card_outer.pack(fill="both", expand=True, padx=40)

        self.card = tk.Frame(card_outer, bg=self.CARD_BG_FRONT,
                             relief="flat", bd=0, cursor="hand2")
        self.card.pack(fill="both", expand=True)
        self.card.bind("<Button-1>", lambda e: self._flip())

        # カード内コンテンツ（クリック透過のため同じバインド）
        def bind_flip(widget):
            widget.bind("<Button-1>", lambda e: self._flip())

        self.lbl_face_tag = tk.Label(self.card, text="", font=FONT_SMALL,
                                      bg=self.CARD_BG_FRONT, fg=TEXT_DIM)
        self.lbl_face_tag.pack(pady=(18, 0))
        bind_flip(self.lbl_face_tag)

        self.lbl_main = tk.Label(self.card, text="", font=FONT_KANJI,
                                  bg=self.CARD_BG_FRONT, fg=TEXT,
                                  wraplength=700, justify="center")
        self.lbl_main.pack(expand=True)
        bind_flip(self.lbl_main)

        self.lbl_sub = tk.Label(self.card, text="", font=FONT_KANA,
                                 bg=self.CARD_BG_FRONT, fg=TEXT_DIM)
        self.lbl_sub.pack()
        bind_flip(self.lbl_sub)

        self.lbl_type = tk.Label(self.card, text="", font=FONT_SMALL,
                                  bg=self.CARD_BG_FRONT, fg=TEXT_DIM, pady=6)
        self.lbl_type.pack()
        bind_flip(self.lbl_type)

        self.lbl_flip_hint = tk.Label(self.card, text="クリックして裏面を見る",
                                       font=FONT_SMALL, bg=self.CARD_BG_FRONT,
                                       fg=TEXT_DIM, pady=12)
        self.lbl_flip_hint.pack(side="bottom")
        bind_flip(self.lbl_flip_hint)

        # ── ナビゲーションボタン ──
        nav = tk.Frame(self, bg=BG, pady=14)
        nav.pack()

        self.btn_prev = tk.Button(
            nav, text="◀  前へ", command=self._prev,
            bg=BG3, fg=TEXT, font=FONT_BODY, relief="flat",
            cursor="hand2", padx=20, pady=10, width=10)
        self.btn_prev.pack(side="left", padx=10)

        self.btn_next = tk.Button(
            nav, text="次へ  ▶", command=self._next,
            bg=ACCENT, fg=TEXT, font=FONT_BODY_B, relief="flat",
            cursor="hand2", padx=20, pady=10, width=10)
        self.btn_next.pack(side="left", padx=10)

        styled_button(nav, "🏠  メニューへ", self.master.show_menu,
                      BG3, width=12).pack(side="left", padx=10)

        # ── キーバインド ──
        self.master.bind("<Right>",  lambda e: self._next())
        self.master.bind("<Left>",   lambda e: self._prev())
        self.master.bind("<space>",  lambda e: self._flip())
        self.bind("<Destroy>", self._unbind_keys)

    def _unbind_keys(self, event):
        if event.widget is self:
            self.master.unbind("<Right>")
            self.master.unbind("<Left>")
            self.master.unbind("<space>")

    # ── カード表示 ────────────────────────────
    def _show_card(self):
        self.showing_front = True
        w = self.words[self.index]
        self.progress_var.set(self.index + 1)
        self.lbl_progress.config(text=f"{self.index + 1} / {len(self.words)}")

        # 前後ボタンの有効/無効
        self.btn_prev.config(state="normal" if self.index > 0 else "disabled")
        self.btn_next.config(
            text="次へ  ▶" if self.index < len(self.words) - 1 else "最初に戻る  ↩",
            bg=ACCENT if self.index < len(self.words) - 1 else YELLOW,
            fg=BG if self.index == len(self.words) - 1 else TEXT,
        )

        # 表面: 日本語
        bg = self.CARD_BG_FRONT
        self._set_card_bg(bg)
        self.lbl_face_tag.config(text="🇯🇵  日本語", bg=bg, fg=TEXT_DIM)
        self.lbl_main.config(text=w.display_japanese(), font=FONT_KANJI, bg=bg, fg=TEXT)
        self.lbl_sub.config(text=f"（{w.romaji}）", bg=bg, fg=TEXT_DIM)
        self.lbl_type.config(text=w.word_type, bg=bg, fg=TEXT_DIM)
        self.lbl_flip_hint.config(text="クリックして裏面（英語）を見る ▼",
                                   bg=bg, fg=TEXT_DIM)

    def _flip(self):
        w = self.words[self.index]
        if self.showing_front:
            # 裏面: 英語の意味
            bg = self.CARD_BG_BACK
            self._set_card_bg(bg)
            self.lbl_face_tag.config(text="🇺🇸  英語", bg=bg, fg=TEXT_DIM)
            self.lbl_main.config(text=w.meaning, font=FONT_BODY_B, bg=bg, fg=TEXT)
            self.lbl_sub.config(text="", bg=bg)
            self.lbl_type.config(text=w.word_type, bg=bg, fg=TEXT_DIM)
            self.lbl_flip_hint.config(text="クリックして表面（日本語）に戻る ▲",
                                       bg=bg, fg=TEXT_DIM)
            self.showing_front = False
        else:
            self._show_card()

    def _set_card_bg(self, color: str):
        for widget in (self.card, self.lbl_face_tag, self.lbl_main,
                       self.lbl_sub, self.lbl_type, self.lbl_flip_hint):
            widget.config(bg=color)

    def _next(self):
        if self.index < len(self.words) - 1:
            self.index += 1
            self._show_card()
        else:
            # 最後のカード → 最初に戻る
            self.index = 0
            random.shuffle(self.words)
            self._show_card()

    def _prev(self):
        if self.index > 0:
            self.index -= 1
            self._show_card()

    def _shuffle(self):
        random.shuffle(self.words)
        self.index = 0
        self._show_card()


# ──────────────────────────────────────────────
# 結果画面
# ──────────────────────────────────────────────
class ResultFrame(tk.Frame):
    def __init__(self, master: EJTesterApp, result: QuizResult):
        super().__init__(master, bg=BG)
        self.master: EJTesterApp

        # ── ヘッダー ──
        tk.Label(self, text="テスト結果", font=FONT_TITLE,
                 bg=BG, fg=ACCENT2, pady=20).pack()

        # ── スコアカード ──
        card = tk.Frame(self, bg=BG3, padx=40, pady=24)
        card.pack(padx=60, fill="x")

        acc = result.accuracy
        if acc == 100:
            emoji, msg, color = "🎉", "パーフェクト！素晴らしいです！", GREEN
        elif acc >= 80:
            emoji, msg, color = "👍", "よくできました！", GREEN
        elif acc >= 60:
            emoji, msg, color = "📚", "もう少し練習しましょう！", YELLOW
        else:
            emoji, msg, color = "💪", "もっと頑張りましょう！", RED

        tk.Label(card, text=f"{emoji}  {msg}", font=FONT_HEAD,
                 bg=BG3, fg=color).pack(pady=(0, 16))

        stats = tk.Frame(card, bg=BG3)
        stats.pack()
        for label, value, c in [
            ("問題数",   str(result.total),                      TEXT),
            ("正解",     str(result.correct),                    GREEN),
            ("不正解",   str(result.total - result.correct),     RED),
            ("正解率",   f"{acc:.1f}%",                          color),
        ]:
            col_frame = tk.Frame(stats, bg=BG2, padx=20, pady=14, relief="flat")
            col_frame.pack(side="left", padx=8)
            tk.Label(col_frame, text=value, font=("Segoe UI", 22, "bold"),
                     bg=BG2, fg=c).pack()
            tk.Label(col_frame, text=label, font=FONT_SMALL,
                     bg=BG2, fg=TEXT_DIM).pack()

        # ── 間違えた単語リスト ──
        if result.wrong_words:
            tk.Label(self, text="間違えた単語", font=FONT_HEAD,
                     bg=BG, fg=RED).pack(pady=(16, 4))

            list_outer = tk.Frame(self, bg=BG2)
            list_outer.pack(padx=60, fill="both", expand=True, pady=(0, 10))

            scrollbar = tk.Scrollbar(list_outer)
            scrollbar.pack(side="right", fill="y")

            cols = ("日本語", "ローマ字", "意味")
            tree = ttk.Treeview(list_outer, columns=cols, show="headings",
                                yscrollcommand=scrollbar.set, height=8)
            style = ttk.Style()
            style.configure("Treeview",
                            background=BG2, foreground=TEXT,
                            fieldbackground=BG2, rowheight=28,
                            font=FONT_SMALL)
            style.configure("Treeview.Heading",
                            background=BG3, foreground=ACCENT2,
                            font=FONT_SMALL)
            style.map("Treeview", background=[("selected", BG3)])

            for col in cols:
                tree.heading(col, text=col)
            tree.column("日本語",  width=160, anchor="w")
            tree.column("ローマ字", width=140, anchor="w")
            tree.column("意味",    width=380, anchor="w")

            for w in result.wrong_words:
                tree.insert("", "end",
                            values=(w.display_japanese(), w.romaji, w.meaning))

            tree.pack(side="left", fill="both", expand=True)
            scrollbar.config(command=tree.yview)

        # ── ボタン ──
        btn_row = tk.Frame(self, bg=BG, pady=14)
        btn_row.pack()
        styled_button(btn_row, "▶  もう一度", master.show_settings,
                      ACCENT, width=14).pack(side="left", padx=8)
        if result.wrong_words:
            styled_button(btn_row, "🔁  間違えた単語を再テスト",
                          lambda: master.retry_wrong(result.wrong_words),
                          RED, width=20).pack(side="left", padx=8)
        styled_button(btn_row, "🏠  メニューへ", master.show_menu,
                      BG3, width=14).pack(side="left", padx=8)


# ──────────────────────────────────────────────
# 単語一覧画面
# ──────────────────────────────────────────────
class WordListFrame(tk.Frame):
    def __init__(self, master: EJTesterApp, words: list[Word]):
        super().__init__(master, bg=BG)
        self.master: EJTesterApp
        self.all_words = list(words)
        self.current_words = list(words)   # 現在表示中の順序
        self.show_meaning = True           # 意味列の表示フラグ
        # 間違えログを読み込む
        self._log: dict[str, int] = _ml.load_log() if _ml else {}

        # ── トップバー ──
        top = tk.Frame(self, bg=BG2, padx=16, pady=12)
        top.pack(fill="x")

        tk.Label(top, text="📖  単語一覧", font=FONT_HEAD,
                 bg=BG2, fg=ACCENT2).pack(side="left")

        # 右側コントロール群
        ctrl = tk.Frame(top, bg=BG2)
        ctrl.pack(side="right")

        # 検索ボックス
        tk.Label(ctrl, text="🔍", font=FONT_BODY, bg=BG2, fg=TEXT_DIM).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filter())
        tk.Entry(ctrl, textvariable=self.search_var,
                 font=FONT_BODY, bg=BG3, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=6, width=18).pack(side="left", padx=(4, 14), ipady=4)

        # シャッフルボタン
        self.shuffle_btn = tk.Button(
            ctrl, text="🔀 ランダム表示", command=self._shuffle,
            bg="#2d6a4f", fg=TEXT, font=FONT_SMALL, relief="flat",
            cursor="hand2", padx=12, pady=6)
        self.shuffle_btn.pack(side="left", padx=4)

        # 元の順に戻すボタン
        tk.Button(ctrl, text="🔢 番号順に戻す", command=self._reset_order,
                  bg=BG3, fg=TEXT, font=FONT_SMALL, relief="flat",
                  cursor="hand2", padx=12, pady=6).pack(side="left", padx=4)

        # 意味の表示/非表示
        self.meaning_btn = tk.Button(
            ctrl, text="👁 意味を隠す", command=self._toggle_meaning,
            bg="#4a3a6a", fg=TEXT, font=FONT_SMALL, relief="flat",
            cursor="hand2", padx=12, pady=6)
        self.meaning_btn.pack(side="left", padx=(12, 0))

        # ── ステータスバー ──
        self.lbl_status = tk.Label(self, text="", font=FONT_SMALL,
                                    bg=BG3, fg=TEXT_DIM, anchor="w", padx=16, pady=4)
        self.lbl_status.pack(fill="x")

        # ── テーブル ──
        table_frame = tk.Frame(self, bg=BG2)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(6, 0))

        scrollbar = tk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y")

        style = ttk.Style()
        style.configure("Treeview",
                        background=BG2, foreground=TEXT,
                        fieldbackground=BG2, rowheight=30,
                        font=FONT_SMALL)
        style.configure("Treeview.Heading",
                        background=BG3, foreground=ACCENT2,
                        font=FONT_SMALL)
        style.map("Treeview", background=[("selected", BG3)])

        self.cols = ("順", "No.", "日本語", "ローマ字", "品詞", "意味", "間違×")
        self.tree = ttk.Treeview(table_frame, columns=self.cols,
                                  show="headings", yscrollcommand=scrollbar.set)
        widths = {"順": 40, "No.": 45, "日本語": 145, "ローマ字": 115,
                  "品詞": 145, "意味": 280, "間違×": 60}
        for col in self.cols:
            self.tree.heading(col, text=col,
                              command=lambda c=col: self._sort(c))
            self.tree.column(col, width=widths[col], anchor="w", minwidth=30)

        # 間違え回数に応じたタグ色
        self.tree.tag_configure("mis_high",   foreground=RED)
        self.tree.tag_configure("mis_medium", foreground=YELLOW)
        self.tree.tag_configure("mis_low",    foreground=TEXT)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)

        # ── 戻るボタン ──
        styled_button(self, "← メニューへ戻る", master.show_menu, BG3, width=16).pack(pady=10)

        # 初期表示（番号順）
        self._fill(self.current_words)

    # ── テーブル描画 ──────────────────────────
    def _fill(self, words: list[Word]):
        self.tree.delete(*self.tree.get_children())
        for rank, w in enumerate(words, 1):
            meaning_cell = w.meaning if self.show_meaning else "──────"
            cnt = self._log.get(str(w.number), 0)
            mis_cell = f"❌ {cnt}" if cnt > 0 else "—"
            tag = "mis_high" if cnt >= 5 else ("mis_medium" if cnt >= 3 else "mis_low")
            self.tree.insert("", "end",
                             values=(rank, w.number, w.display_japanese(),
                                     w.romaji, w.word_type, meaning_cell, mis_cell),
                             tags=(tag,))
        self.lbl_status.config(
            text=f"  表示中: {len(words)} 語  /  全 {len(self.all_words)} 語"
                 + ("  |  🔀 ランダム順" if self.current_words != self.all_words else "  |  🔢 番号順"))

    # ── シャッフル ────────────────────────────
    def _shuffle(self):
        self.current_words = list(self.all_words)
        random.shuffle(self.current_words)
        self.search_var.set("")
        self._fill(self.current_words)

    def _reset_order(self):
        self.current_words = list(self.all_words)
        self.search_var.set("")
        self._fill(self.current_words)

    # ── 意味の表示/非表示 ─────────────────────
    def _toggle_meaning(self):
        self.show_meaning = not self.show_meaning
        self.meaning_btn.config(
            text="👁 意味を表示" if not self.show_meaning else "👁 意味を隠す",
            bg="#2d4a6a" if not self.show_meaning else "#4a3a6a",
        )
        self._apply_filter()

    # ── 検索フィルタ ──────────────────────────
    def _apply_filter(self):
        q = self.search_var.get().lower()
        if not q:
            self._fill(self.current_words)
            return
        filtered = [w for w in self.current_words if
                    q in w.kanji.lower() or q in w.kana.lower() or
                    q in w.romaji.lower() or q in w.meaning.lower() or
                    q in w.word_type.lower()]
        self._fill(filtered)

    # ── 列ソート ──────────────────────────────
    def _sort(self, col: str):
        data = [(self.tree.set(child, col), child)
                for child in self.tree.get_children("")]
        try:
            data.sort(key=lambda x: int(x[0]))
        except ValueError:
            data.sort(key=lambda x: x[0].lower())
        for i, (_, child) in enumerate(data):
            self.tree.move(child, "", i)


# ──────────────────────────────────────────────
# エントリポイント
# ──────────────────────────────────────────────
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "vocabulary.csv")

    if not os.path.exists(csv_path):
        import tkinter.messagebox as mb
        root = tk.Tk(); root.withdraw()
        mb.showerror("エラー", f"vocabulary.csv が見つかりません:\n{csv_path}")
        sys.exit(1)

    words = load_vocabulary(csv_path)
    app = EJTesterApp(words)
    app.mainloop()


if __name__ == "__main__":
    main()
