"""
EJTester — 統合アプリ
テスト（ui.py）と 単語帳エディタ（word_editor.py）を
1つのウィンドウに統合して起動する。
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox

# ── パス設定 ──────────────────────────────────────────────
_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(_DIR, "vocabulary.csv")

# ── 各モジュールをフレーム化して取り込む ──────────────────
# ui.py / word_editor.py は __main__ ブロックを持つため
# importlib 経由で読み込み、Tk ルートを作らずに使う

import importlib.util as _ilu

def _import(name: str, path: str):
    spec = _ilu.spec_from_file_location(name, path)
    mod  = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_ui  = _import("ui",          os.path.join(_DIR, "ui.py"))
_we  = _import("word_editor", os.path.join(_DIR, "word_editor.py"))

# ── 共通テーマ定数（ui.py から流用） ─────────────────────
BG      = _ui.BG
BG2     = _ui.BG2
BG3     = _ui.BG3
ACCENT  = _ui.ACCENT
ACCENT2 = _ui.ACCENT2
TEXT    = _ui.TEXT
TEXT_DIM= _ui.TEXT_DIM
YELLOW  = _ui.YELLOW

FONT_TITLE = _ui.FONT_TITLE
FONT_HEAD  = _ui.FONT_HEAD
FONT_BODY  = _ui.FONT_BODY
FONT_SMALL = _ui.FONT_SMALL


# ══════════════════════════════════════════════════════════
# テスト側を Frame として埋め込む薄いラッパー
# ══════════════════════════════════════════════════════════
class TesterPane(tk.Frame):
    """
    EJTesterApp(tk.Tk) の UI を tk.Frame の中に収める。
    このクラス自身が EJTesterApp と同じインターフェースを実装する。
    各 Frame の master として直接 self を渡す。
    """
    def __init__(self, master: tk.Widget, words: list):
        super().__init__(master, bg=BG)
        self.words  = words
        self._frame: tk.Frame | None = None
        self._last_mode: str = "1"
        self._last_all_words: list = words
        self.show_menu()

    # ── フレーム切り替え ──
    def switch_frame(self, frame_class, **kwargs):
        if self._frame:
            self._frame.destroy()
        self._frame = frame_class(self, **kwargs)
        self._frame.pack(fill="both", expand=True)

    def show_menu(self):
        self.switch_frame(_ui.MenuFrame)

    def show_word_list(self):
        self.switch_frame(_ui.WordListFrame, words=self.words)

    def show_flashcards(self):
        self.switch_frame(_ui.FlashCardFrame, words=self.words)

    def show_settings(self):
        self.switch_frame(_ui.SettingsFrame, words=self.words)

    def show_weak_settings(self):
        self.switch_frame(_ui.WeakWordSettingsFrame, words=self.words)

    def start_quiz(self, quiz_words, mode, all_words):
        self._last_mode      = mode
        self._last_all_words = all_words
        self.switch_frame(_ui.ListQuizFrame,
                          quiz_words=quiz_words,
                          mode=mode,
                          all_words=all_words)

    def retry_wrong(self, wrong_words):
        import random
        quiz_words = list(wrong_words)
        random.shuffle(quiz_words)
        self.start_quiz(quiz_words, self._last_mode, self._last_all_words)

    def show_result(self, result):
        self.switch_frame(_ui.ResultFrame, result=result)

    def reload_words(self, words: list):
        """単語帳エディタが保存したとき、単語リストを更新する"""
        self.words = words
        self._last_all_words = words
        self.show_menu()

    def quit(self):
        self.winfo_toplevel().quit()

    # FlashCardFrame が bind/unbind を呼ぶのでトップレベルに委譲
    def bind(self, seq=None, func=None, add=None):
        if seq and seq.startswith("<"):
            return self.winfo_toplevel().bind(seq, func, add)
        return super().bind(seq, func, add)

    def unbind(self, seq, funcid=None):
        try:
            return self.winfo_toplevel().unbind(seq, funcid)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════
# 単語帳エディタ側を Frame として埋め込む薄いラッパー
# ══════════════════════════════════════════════════════════
class EditorPane(tk.Frame):
    """
    WordEditorApp（元は tk.Tk）の UI を tk.Frame の中に収める。
    on_save_callback: 単語が保存されたときに TesterPane に通知する関数
    """
    def __init__(self, master: tk.Widget, on_save_callback):
        super().__init__(master, bg=_we.BG)
        self._on_save_callback = on_save_callback
        self._build()

    def _build(self):
        # WordEditorApp のコンテンツを self に直接構築する
        # WordEditorApp(tk.Tk) をそのまま使えないので、
        # 同クラスのメソッド群を self にバインドして再現する。

        # ── 必要な属性を初期化（WordEditorApp.__init__ 相当） ──
        self.rows: list[dict] = _we.load_csv()
        self.forms: list      = []

        # lbl_count（ヘッダー内）は後で _build_ui() 内で作られる
        self._build_editor_ui()

    def _build_editor_ui(self):
        """WordEditorApp._build_ui() 相当をこの Frame 内に構築"""

        # ── ヘッダー ──
        header = tk.Frame(self, bg=_we.BG2, padx=20, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="📝  単語帳エディタ",
                 font=_we.FONT_TITLE, bg=_we.BG2, fg=_we.ACCENT2).pack(side="left")
        self.lbl_count = tk.Label(
            header, text="", font=_we.FONT_SMALL, bg=_we.BG2, fg=_we.TEXT_DIM)
        self.lbl_count.pack(side="left", padx=20)
        self._refresh_count()

        # ── タブスタイル ──
        nb_style = ttk.Style()
        nb_style.configure("EditorNB.TNotebook", background=_we.BG, borderwidth=0)
        nb_style.configure("EditorNB.TNotebook.Tab",
                           background=_we.BG3, foreground=_we.TEXT,
                           padding=[12, 6], font=_we.FONT_BODY)
        nb_style.map("EditorNB.TNotebook.Tab",
                     background=[("selected", _we.ACCENT)],
                     foreground=[("selected", _we.TEXT)])

        self.notebook = ttk.Notebook(self, style="EditorNB.TNotebook")
        self.notebook.pack(fill="both", expand=True)

        # タブ1: 新規追加
        self.tab_add = tk.Frame(self.notebook, bg=_we.BG)
        self.notebook.add(self.tab_add, text="  ➕  新規追加  ")

        # タブ2: 一括入力
        self.tab_bulk = tk.Frame(self.notebook, bg=_we.BG)
        self.notebook.add(self.tab_bulk, text="  📄  一括入力  ")

        # タブ3: 一覧・編集
        self.tab_list = tk.Frame(self.notebook, bg=_we.BG)
        self.notebook.add(self.tab_list, text="  📋  一覧・編集  ")

        # WordEditorApp のメソッドをこの EditorPane にバインドして呼ぶ
        _we.WordEditorApp._build_tab_add(self)
        _we.WordEditorApp._build_tab_bulk(self)
        _we.WordEditorApp._build_tab_list(self)

        self._add_form()

    # ── WordEditorApp のメソッドを委譲（必要なものだけ定義） ──
    # Python の unbound method として呼べるよう self を渡す形式を使う

    def _add_form(self, data=None):
        _we.WordEditorApp._add_form(self, data)

    def _renumber_forms(self):
        _we.WordEditorApp._renumber_forms(self)

    def _clear_empty(self):
        _we.WordEditorApp._clear_empty(self)

    def _save_new(self):
        _we.WordEditorApp._save_new(self)
        self._notify_saved()

    def _bulk_convert(self):
        _we.WordEditorApp._bulk_convert(self)

    def _bulk_clear_tags(self):
        _we.WordEditorApp._bulk_clear_tags(self)

    def _bulk_parse(self):
        return _we.WordEditorApp._bulk_parse(self)

    def _bulk_preview(self):
        _we.WordEditorApp._bulk_preview(self)

    def _bulk_save(self):
        _we.WordEditorApp._bulk_save(self)
        self._notify_saved()

    def _refresh_list(self):
        _we.WordEditorApp._refresh_list(self)

    def _refresh_count(self):
        _we.WordEditorApp._refresh_count(self)

    def _edit_selected(self):
        _we.WordEditorApp._edit_selected(self)

    def _on_edit_save(self, original_num, new_data):
        _we.WordEditorApp._on_edit_save(self, original_num, new_data)
        self._notify_saved()

    def _delete_selected(self):
        _we.WordEditorApp._delete_selected(self)
        self._notify_saved()

    def _renumber_all(self):
        _we.WordEditorApp._renumber_all(self)
        self._notify_saved()

    def _sort_col(self, col):
        _we.WordEditorApp._sort_col(self, col)

    def _notify_saved(self):
        """保存が完了したらテスト側に通知する"""
        self._on_save_callback(self.rows)

    # ── EditDialog が master として参照するため winfo 系を委譲 ──
    def winfo_x(self):      return super().winfo_x()
    def winfo_y(self):      return super().winfo_y()
    def winfo_width(self):  return super().winfo_width()
    def winfo_height(self): return super().winfo_height()


# ══════════════════════════════════════════════════════════
# 統合メインウィンドウ
# ══════════════════════════════════════════════════════════
class EJTesterMain(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EJTester — 単語テスト ＆ 単語帳エディタ")
        self.geometry("1100x760")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.resizable(True, True)
        # 起動時に全画面（最大化）表示
        self.after(0, lambda: self.state("zoomed"))

        # vocabulary.csv を確認
        if not os.path.exists(CSV_PATH):
            messagebox.showerror(
                "エラー", f"vocabulary.csv が見つかりません:\n{CSV_PATH}")
            sys.exit(1)

        self._words = _ui.load_vocabulary(CSV_PATH)
        self._build_ui()

    def _build_ui(self):
        # ── トップバー ──
        topbar = tk.Frame(self, bg=BG2, padx=20, pady=10)
        topbar.pack(fill="x")
        tk.Label(topbar, text="🗾  EJTester",
                 font=FONT_TITLE, bg=BG2, fg=ACCENT2).pack(side="left")
        self.lbl_word_count = tk.Label(
            topbar, text=self._count_text(),
            font=FONT_SMALL, bg=BG2, fg=TEXT_DIM)
        self.lbl_word_count.pack(side="left", padx=20)

        # ── メインタブ ──
        tab_style = ttk.Style()
        tab_style.theme_use("clam")   # clam テーマが foreground の上書きを確実に適用する
        tab_style.configure("Main.TNotebook",
                            background=BG, borderwidth=0, tabmargins=0)
        tab_style.configure("Main.TNotebook.Tab",
                            background=BG3, foreground=TEXT,
                            lightcolor=BG3, bordercolor=BG,
                            padding=[18, 9], font=FONT_HEAD)
        tab_style.map("Main.TNotebook.Tab",
                      background=[("selected", ACCENT),   ("!selected", BG3)],
                      foreground=[("selected", "#ffffff"), ("!selected", TEXT)],
                      lightcolor=[("selected", ACCENT)],
                      bordercolor=[("selected", ACCENT)])

        self.nb = ttk.Notebook(self, style="Main.TNotebook")
        self.nb.pack(fill="both", expand=True)

        # ─ タブ1: テスト ─
        self.tester_pane = TesterPane(self.nb, self._words)
        self.nb.add(self.tester_pane, text="  🗾  単語テスト  ")

        # ─ タブ2: 単語帳エディタ ─
        self.editor_pane = EditorPane(self.nb, self._on_words_saved)
        self.nb.add(self.editor_pane, text="  📝  単語帳エディタ  ")

    def _count_text(self) -> str:
        return f"登録単語数: {len(self._words)} 語"

    def _on_words_saved(self, new_rows: list[dict]):
        """単語帳エディタで保存が発生したときに呼ばれる"""
        # CSV から改めて Word オブジェクトとして読み直す
        try:
            self._words = _ui.load_vocabulary(CSV_PATH)
        except Exception:
            return
        self.lbl_word_count.config(text=self._count_text())
        # テスト側の単語リストも更新
        self.tester_pane.reload_words(self._words)


# ══════════════════════════════════════════════════════════
# エントリポイント
# ══════════════════════════════════════════════════════════
def main():
    app = EJTesterMain()
    app.mainloop()


if __name__ == "__main__":
    main()
