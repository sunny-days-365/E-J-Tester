"""
EJTester - 単語帳エディタ
vocabulary.csv に単語を追加・編集・削除するための専用GUIツール
"""

import csv
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vocabulary.csv")

# ── カラー・フォント（ui.py と共通テーマ）──────────────────
BG      = "#1e1e2e"
BG2     = "#2a2a3e"
BG3     = "#313145"
ACCENT  = "#7c6af7"
ACCENT2 = "#a78bfa"
GREEN   = "#4ade80"
RED     = "#f87171"
YELLOW  = "#fbbf24"
TEXT    = "#e2e8f0"
TEXT_DIM= "#94a3b8"

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_HEAD  = ("Segoe UI", 12, "bold")
FONT_BODY  = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 10)
FONT_MONO  = ("Consolas", 10)

# ── 品詞プリセット ────────────────────────────────────────
WORD_TYPES = [
    "Noun",
    "Verb, Godan verb, Transitive verb",
    "Verb, Godan verb, Intransitive verb",
    "Verb, Ichidan verb, Transitive verb",
    "Verb, Ichidan verb, Intransitive verb",
    "Verb, Suru verb",
    "Noun, Suru verb",
    "い-adjective",
    "Adjective, い-adjective",
    "な-adjective",
    "Adjective, な-adjective",
    "Adverb",
    "Pronoun",
    "Noun, Adverb",
    "Noun, Numeric",
    "Noun, Katakana",
    "Pre-noun adjectival",
    "Noun, Adjective, な-adjective",
    "Noun, Adjective, な-adjective, Adverb",
    "Interjection",
    "Particle",
    "Other",
]


# ── CSV 読み書き ───────────────────────────────────────────
def load_csv() -> list[dict]:
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def save_csv(rows: list[dict]):
    fieldnames = ["#", "ごい", "ローマ字", "かな", "Type", "Meaning"]
    with open(CSV_PATH, encoding="utf-8", newline="") as f:
        # 既存ヘッダーを確認
        first = f.readline()
        if first.strip():
            detected = [h.strip() for h in first.split(",")]
            if detected[0] == "#":
                fieldnames = detected

    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames,
                                quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def next_number(rows: list[dict]) -> int:
    nums = [int(r["#"]) for r in rows if r.get("#", "").isdigit()]
    return max(nums, default=0) + 1


# ══════════════════════════════════════════════════════════
# 単語入力フォーム（1単語分）
# ══════════════════════════════════════════════════════════
class WordForm(tk.Frame):
    """1単語分の入力フォーム。複数並べて使う。"""

    def __init__(self, master, number: int, initial: dict | None = None,
                 on_delete=None):
        super().__init__(master, bg=BG2, bd=1, relief="flat",
                         highlightbackground=BG3, highlightthickness=1)
        self._on_delete = on_delete
        self._build(number, initial or {})

    def _build(self, number: int, data: dict):
        # ── ヘッダー行 ──
        header = tk.Frame(self, bg=BG3)
        header.pack(fill="x")
        self.lbl_num = tk.Label(header, text=f"  #{number}",
                                font=FONT_HEAD, bg=BG3, fg=ACCENT2,
                                width=6, anchor="w")
        self.lbl_num.pack(side="left", padx=(6, 0), pady=4)

        if self._on_delete:
            tk.Button(header, text="✕ 削除",
                      command=self._on_delete,
                      bg="#5a1a1a", fg=RED, font=FONT_SMALL,
                      relief="flat", cursor="hand2",
                      padx=8, pady=2).pack(side="right", padx=6, pady=4)

        # ── フィールドグリッド ──
        body = tk.Frame(self, bg=BG2, padx=10, pady=8)
        body.pack(fill="x")

        labels   = ["日本語（ごい）*", "ローマ字 *", "かな（読み）", "品詞 *", "英語の意味 *"]
        widths   = [18, 18, 18, 38, 42]
        attrs    = ["kanji", "romaji", "kana", "word_type", "meaning"]

        self.vars: dict[str, tk.StringVar] = {a: tk.StringVar() for a in attrs}

        for col, (lbl, w, attr) in enumerate(zip(labels, widths, attrs)):
            tk.Label(body, text=lbl, font=FONT_SMALL, bg=BG2,
                     fg=TEXT_DIM, anchor="w").grid(
                row=0, column=col, sticky="w", padx=(0, 6))

        for col, (w, attr) in enumerate(zip(widths, attrs)):
            val = (data.get("ごい") if attr == "kanji"
                   else data.get("ローマ字") if attr == "romaji"
                   else data.get("かな") if attr == "kana"
                   else data.get("Type") if attr == "word_type"
                   else data.get("Meaning") if attr == "meaning"
                   else "")
            self.vars[attr].set(val or "")

            if attr == "word_type":
                # 品詞はコンボボックス（入力もできる）
                cb = ttk.Combobox(body, textvariable=self.vars[attr],
                                  values=WORD_TYPES, font=FONT_SMALL,
                                  width=w - 2, state="normal")
                cb.grid(row=1, column=col, sticky="w", padx=(0, 6), ipady=3)
            else:
                ent = tk.Entry(body, textvariable=self.vars[attr],
                               font=FONT_SMALL if attr != "meaning" else FONT_MONO,
                               bg=BG3, fg=TEXT, insertbackground=TEXT,
                               relief="flat", bd=4, width=w)
                ent.grid(row=1, column=col, sticky="w", padx=(0, 6), ipady=3)

        # ヒント
        tk.Label(body,
                 text="意味は ; で複数可  例: to run; to dash　／　かなは任意（カタカナ語は空欄でOK）",
                 font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).grid(
            row=2, column=0, columnspan=5, sticky="w", pady=(4, 0))

    def set_number(self, n: int):
        self.lbl_num.config(text=f"  #{n}")

    def get_data(self) -> dict | None:
        """入力を検証して dict を返す。エラーがあれば None。"""
        kanji     = self.vars["kanji"].get().strip()
        romaji    = self.vars["romaji"].get().strip()
        kana      = self.vars["kana"].get().strip()
        word_type = self.vars["word_type"].get().strip()
        meaning   = self.vars["meaning"].get().strip()

        errors = []
        if not kanji:    errors.append("「日本語」が空です")
        if not romaji:   errors.append("「ローマ字」が空です")
        if not word_type:errors.append("「品詞」が空です")
        if not meaning:  errors.append("「英語の意味」が空です")
        if errors:
            messagebox.showerror("入力エラー",
                                 f"#{self.lbl_num.cget('text').strip()}\n" +
                                 "\n".join(f"・{e}" for e in errors))
            return None

        return {
            "ごい":    kanji,
            "ローマ字": romaji,
            "かな":    kana,
            "Type":    word_type,
            "Meaning": meaning,
        }

    def is_empty(self) -> bool:
        return not any(v.get().strip() for v in self.vars.values())


# ══════════════════════════════════════════════════════════
# メインアプリ
# ══════════════════════════════════════════════════════════
class WordEditorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EJTester — 単語帳エディタ")
        self.geometry("1100x720")
        self.minsize(900, 560)
        self.configure(bg=BG)
        self.resizable(True, True)

        self.rows: list[dict] = load_csv()
        self.forms: list[WordForm] = []

        self._build_ui()
        self._add_form()   # 最初の空フォームを表示

    # ── UI 構築 ──────────────────────────────────────────
    def _build_ui(self):
        # ── ヘッダー ──
        header = tk.Frame(self, bg=BG2, padx=20, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="📝  単語帳エディタ",
                 font=FONT_TITLE, bg=BG2, fg=ACCENT2).pack(side="left")
        self.lbl_count = tk.Label(
            header, text="", font=FONT_SMALL, bg=BG2, fg=TEXT_DIM)
        self.lbl_count.pack(side="left", padx=20)
        self._refresh_count()

        # ── タブ ──
        nb = ttk.Style()
        nb.configure("TNotebook", background=BG, borderwidth=0)
        nb.configure("TNotebook.Tab", background=BG3, foreground=TEXT,
                     padding=[12, 6], font=FONT_BODY)
        nb.map("TNotebook.Tab",
               background=[("selected", ACCENT)],
               foreground=[("selected", TEXT)])

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=0, pady=0)

        # ─ タブ1: 新規追加 ─
        self.tab_add = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_add, text="  ➕  新規追加  ")
        self._build_tab_add()

        # ─ タブ2: 一括テキスト入力 ─
        self.tab_bulk = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_bulk, text="  📄  一括入力  ")
        self._build_tab_bulk()

        # ─ タブ3: 一覧・編集 ─
        self.tab_list = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.tab_list, text="  📋  一覧・編集  ")
        self._build_tab_list()

    # ══════════════════════════════════════════════════
    # タブ1: 新規追加
    # ══════════════════════════════════════════════════
    def _build_tab_add(self):
        # ── ツールバー ──
        bar = tk.Frame(self.tab_add, bg=BG3, padx=14, pady=8)
        bar.pack(fill="x")

        tk.Button(bar, text="＋ フォームを追加",
                  command=self._add_form,
                  bg=ACCENT, fg=TEXT, font=FONT_BODY,
                  relief="flat", cursor="hand2",
                  padx=14, pady=6).pack(side="left", padx=(0, 8))

        tk.Button(bar, text="🗑 空フォームをクリア",
                  command=self._clear_empty,
                  bg=BG2, fg=TEXT_DIM, font=FONT_SMALL,
                  relief="flat", cursor="hand2",
                  padx=10, pady=6).pack(side="left", padx=(0, 8))

        tk.Button(bar, text="💾  CSV に保存",
                  command=self._save_new,
                  bg="#2d6a4f", fg=TEXT, font=FONT_HEAD,
                  relief="flat", cursor="hand2",
                  padx=18, pady=6).pack(side="right")

        tk.Label(bar,
                 text="* 必須項目  ／  Tab キーで次フィールドへ移動",
                 font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(side="right", padx=14)

        # ── スクロール領域 ──
        outer = tk.Frame(self.tab_add, bg=BG)
        outer.pack(fill="both", expand=True)

        self.canvas_add = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb = tk.Scrollbar(outer, orient="vertical",
                           command=self.canvas_add.yview)
        self.canvas_add.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas_add.pack(side="left", fill="both", expand=True)

        self.forms_frame = tk.Frame(self.canvas_add, bg=BG)
        self._cwin = self.canvas_add.create_window(
            (0, 0), window=self.forms_frame, anchor="nw")

        self.forms_frame.bind("<Configure>",
                              lambda e: self.canvas_add.configure(
                                  scrollregion=self.canvas_add.bbox("all")))
        self.canvas_add.bind("<Configure>",
                             lambda e: self.canvas_add.itemconfig(
                                 self._cwin, width=e.width))
        self.canvas_add.bind_all(
            "<MouseWheel>",
            lambda e: self.canvas_add.yview_scroll(
                -1 if e.delta > 0 else 1, "units"))

    def _add_form(self, data: dict | None = None):
        next_n = next_number(self.rows) + len(self.forms)
        idx = len(self.forms)

        def do_delete(i=idx):
            f = self.forms[i]
            f.destroy()
            self.forms.pop(i)
            self._renumber_forms()

        f = WordForm(self.forms_frame, next_n, data,
                     on_delete=lambda i=idx: do_delete(i))
        f.pack(fill="x", padx=14, pady=(10, 0))
        self.forms.append(f)
        # スクロールを一番下に
        self.canvas_add.after(
            50, lambda: self.canvas_add.yview_moveto(1.0))

    def _renumber_forms(self):
        base = next_number(self.rows)
        for i, f in enumerate(self.forms):
            f.set_number(base + i)

    def _clear_empty(self):
        to_del = [f for f in self.forms if f.is_empty()]
        for f in to_del:
            self.forms.remove(f)
            f.destroy()
        self._renumber_forms()

    def _save_new(self):
        if not self.forms:
            messagebox.showinfo("情報", "追加するフォームがありません。")
            return

        new_rows = []
        base_n = next_number(self.rows)
        for i, form in enumerate(self.forms):
            if form.is_empty():
                continue
            data = form.get_data()
            if data is None:
                return   # バリデーションエラー → 中断
            data["#"] = str(base_n + len(new_rows))
            new_rows.append(data)

        if not new_rows:
            messagebox.showinfo("情報", "保存できる単語がありません。")
            return

        self.rows.extend(new_rows)
        save_csv(self.rows)

        # フォームをクリア
        for f in self.forms:
            f.destroy()
        self.forms.clear()
        self._add_form()

        self._refresh_count()
        self._refresh_list()
        messagebox.showinfo("保存完了",
                            f"{len(new_rows)} 語を vocabulary.csv に保存しました。\n"
                            f"現在の合計: {len(self.rows)} 語")

    # ══════════════════════════════════════════════════
    # タブ2: 一括テキスト入力
    # ══════════════════════════════════════════════════
    def _build_tab_bulk(self):
        # ── 説明ラベル ──
        desc = tk.Frame(self.tab_bulk, bg=BG3, padx=14, pady=10)
        desc.pack(fill="x")
        tk.Label(desc, text="一括テキスト入力",
                 font=FONT_HEAD, bg=BG3, fg=ACCENT2).pack(side="left")
        tk.Label(desc,
                 text="  テキストを貼り付けて「🔄 フォーマット変換」→「💾 CSV に保存」",
                 font=FONT_SMALL, bg=BG3, fg=TEXT_DIM).pack(side="left")

        # ── フォーマット説明（折りたたみ） ──
        fmt_frame = tk.Frame(self.tab_bulk, bg=BG2, padx=18, pady=8)
        fmt_frame.pack(fill="x")

        # 対応フォーマット A（辞書コピペ形式）
        tk.Label(fmt_frame,
                 text="【フォーマット A】辞書コピペ形式（自動変換対応）",
                 font=FONT_SMALL, bg=BG2, fg=YELLOW).grid(
            row=0, column=0, sticky="w")
        tk.Label(fmt_frame,
                 text="  201　居る　iru　いる　Verb, Ichidan verb\tto be\n"
                      "  ※ 番号・日本語・ローマ字・かな・品詞・意味 を含む複数行ブロック",
                 font=FONT_MONO, bg=BG2, fg=TEXT_DIM).grid(
            row=1, column=0, sticky="w", pady=(0, 6))

        # 対応フォーマット B（CSV 1行形式）
        tk.Label(fmt_frame,
                 text="【フォーマット B】CSV 1行形式（直接入力）",
                 font=FONT_SMALL, bg=BG2, fg=YELLOW).grid(
            row=2, column=0, sticky="w")
        tk.Label(fmt_frame,
                 text="  食べる,taberu,たべる,\"Verb, Ichidan verb\",to eat\n"
                      "  ※ 日本語,ローマ字,かな,品詞,意味　（かな省略可）",
                 font=FONT_MONO, bg=BG2, fg=TEXT_DIM).grid(
            row=3, column=0, sticky="w")

        # ── テキストエリア ──
        text_outer = tk.Frame(self.tab_bulk, bg=BG)
        text_outer.pack(fill="both", expand=True, padx=14, pady=(8, 0))

        vsb = tk.Scrollbar(text_outer, orient="vertical")
        vsb.pack(side="right", fill="y")
        hsb = tk.Scrollbar(text_outer, orient="horizontal")
        hsb.pack(side="bottom", fill="x")

        self.bulk_text = tk.Text(
            text_outer,
            font=FONT_MONO, bg=BG3, fg=TEXT,
            insertbackground=TEXT,
            relief="flat", bd=6,
            wrap="none",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
            undo=True,
        )
        self.bulk_text.pack(side="left", fill="both", expand=True)
        vsb.config(command=self.bulk_text.yview)
        hsb.config(command=self.bulk_text.xview)

        # 行番号ハイライト（入力行に色付け用タグ）
        self.bulk_text.tag_config("error_line", background="#4a1a1a", foreground=RED)
        self.bulk_text.tag_config("ok_line",    background="#1a3a2a", foreground=GREEN)

        # ── ボタンバー ──
        btn_bar = tk.Frame(self.tab_bulk, bg=BG3, padx=14, pady=10)
        btn_bar.pack(fill="x")

        tk.Button(btn_bar, text="🔄  フォーマット変換",
                  command=self._bulk_convert,
                  bg=YELLOW, fg="#1a1a2e", font=FONT_HEAD,
                  relief="flat", cursor="hand2",
                  padx=14, pady=6).pack(side="left", padx=(0, 10))

        tk.Button(btn_bar, text="✅  プレビュー（確認）",
                  command=self._bulk_preview,
                  bg=ACCENT, fg=TEXT, font=FONT_BODY,
                  relief="flat", cursor="hand2",
                  padx=14, pady=6).pack(side="left", padx=(0, 10))

        tk.Button(btn_bar, text="💾  CSV に保存",
                  command=self._bulk_save,
                  bg="#2d6a4f", fg=TEXT, font=FONT_HEAD,
                  relief="flat", cursor="hand2",
                  padx=18, pady=6).pack(side="left", padx=(0, 10))

        tk.Button(btn_bar, text="🗑  クリア",
                  command=lambda: (self.bulk_text.delete("1.0", "end"),
                                   self._bulk_clear_tags()),
                  bg=BG2, fg=TEXT_DIM, font=FONT_SMALL,
                  relief="flat", cursor="hand2",
                  padx=10, pady=6).pack(side="left")

        self.bulk_status = tk.Label(btn_bar, text="",
                                    font=FONT_SMALL, bg=BG3, fg=TEXT_DIM)
        self.bulk_status.pack(side="right", padx=14)

    def _bulk_convert(self):
        """
        辞書コピペ形式（フォーマットA）を CSV 1行形式（フォーマットB）に変換して
        テキストエリアを置き換える。
        既に CSV 形式の行はそのまま保持する。
        """
        import re
        raw = self.bulk_text.get("1.0", "end")
        lines = raw.splitlines()

        # ── ブロック分割 ──────────────────────────────────
        # 各単語ブロックは「数字で始まる行」または「空行」で区切られている
        # 例:
        #   201\t\n居る\niru\nいる\n\nVerb, Ichidan verb\tto be, to have
        #   207\t\nいつ\nitsu\nPronoun\twhen
        #
        # ブロック収集: 番号行を見つけたら新ブロック開始
        blocks: list[list[str]] = []
        current: list[str] = []

        NUM_RE = re.compile(r"^\d+\s*$")   # 番号だけの行（タブ除去後）

        for line in lines:
            stripped = line.strip()
            if NUM_RE.match(stripped):
                if current:
                    blocks.append(current)
                current = [stripped]
            else:
                current.append(stripped)
        if current:
            blocks.append(current)

        csv_lines: list[str] = []
        skipped: list[str] = []

        for block in blocks:
            # 空行を除いたトークン列
            tokens = [t for t in block if t]

            # ── 既に CSV 形式（カンマ区切り1行）の場合はそのまま残す ──
            if len(tokens) == 1 and "," in tokens[0] and not NUM_RE.match(tokens[0]):
                csv_lines.append(tokens[0])
                continue

            # tokens[0] が番号なら除去
            if tokens and NUM_RE.match(tokens[0]):
                tokens = tokens[1:]

            if not tokens:
                continue

            # ── フィールド抽出 ──────────────────────────
            # tokens の構成パターン（かな有り / 無し）：
            #   [日本語, ローマ字, かな, 品詞\t意味]  ← かな有り
            #   [日本語, ローマ字, 品詞\t意味]        ← かな無し（ローマ字で判定）
            # 品詞と意味はタブ区切りで同一トークン内に入ることが多い

            # タブを含むトークンを品詞+意味トークンとして扱う
            def split_type_meaning(tok: str) -> tuple[str, str]:
                if "\t" in tok:
                    parts = tok.split("\t", 1)
                    return parts[0].strip(), parts[1].strip()
                return tok.strip(), ""

            ROMAJI_RE = re.compile(r"^[a-zA-Z\s\-]+$")
            KANA_RE   = re.compile(r"^[\u3040-\u30ff\u30fc]+$")

            kanji = romaji = kana = word_type = meaning = ""

            if len(tokens) == 1:
                # タブ区切りで全部入っている可能性
                parts = tokens[0].split("\t")
                parts = [p.strip() for p in parts if p.strip()]
                if len(parts) >= 4:
                    kanji, romaji, kana = parts[0], parts[1], parts[2]
                    word_type, meaning = split_type_meaning("\t".join(parts[3:]))
                elif len(parts) == 3:
                    kanji, romaji = parts[0], parts[1]
                    word_type, meaning = split_type_meaning(parts[2])
                else:
                    skipped.append(" / ".join(tokens))
                    continue

            elif len(tokens) == 2:
                # [日本語, 品詞\t意味] or [ローマ字, 品詞\t意味]
                if ROMAJI_RE.match(tokens[0]):
                    romaji = tokens[0]
                    word_type, meaning = split_type_meaning(tokens[1])
                else:
                    kanji = tokens[0]
                    word_type, meaning = split_type_meaning(tokens[1])

            elif len(tokens) == 3:
                # [日本語, ローマ字, 品詞\t意味]
                kanji, romaji = tokens[0], tokens[1]
                word_type, meaning = split_type_meaning(tokens[2])

            elif len(tokens) >= 4:
                kanji, romaji = tokens[0], tokens[1]
                # tokens[2] がかなかどうか確認
                if KANA_RE.match(tokens[2]):
                    kana = tokens[2]
                    word_type, meaning = split_type_meaning("\t".join(tokens[3:]))
                else:
                    word_type, meaning = split_type_meaning("\t".join(tokens[2:]))

            # 意味が空の場合：品詞トークンの後ろにタブなしで続いていることも
            # → 品詞プリセットと照合して残りを意味とする
            if word_type and not meaning:
                # 品詞プリセットに前方一致するか試みる
                for preset in sorted(WORD_TYPES, key=len, reverse=True):
                    if word_type.lower().startswith(preset.lower()):
                        meaning = word_type[len(preset):].strip(" ,;-\t")
                        word_type = preset
                        break

            if not kanji or not romaji or not word_type or not meaning:
                skipped.append(" | ".join(tokens))
                continue

            # ── CSV 1行に変換 ──────────────────────────
            def csv_field(s: str) -> str:
                s = s.strip()
                if "," in s or '"' in s:
                    s = s.replace('"', '""')
                    return f'"{s}"'
                return s

            row = ",".join([
                csv_field(kanji),
                csv_field(romaji),
                csv_field(kana),
                csv_field(word_type),
                csv_field(meaning),
            ])
            csv_lines.append(row)

        # ── テキストエリアを置き換え ──
        result = "\n".join(csv_lines)
        self.bulk_text.delete("1.0", "end")
        self.bulk_text.insert("1.0", result)
        self._bulk_clear_tags()

        msg = f"✅ {len(csv_lines)} 語に変換しました。"
        if skipped:
            msg += f"\n⚠️ 変換できなかったブロック: {len(skipped)} 件\n"
            msg += "\n".join(f"  • {s}" for s in skipped[:10])
            if len(skipped) > 10:
                msg += f"\n  …他 {len(skipped) - 10} 件"
        messagebox.showinfo("変換完了", msg)
        self.bulk_status.config(text=f"変換済: {len(csv_lines)} 語")

    def _bulk_clear_tags(self):
        self.bulk_text.tag_remove("error_line", "1.0", "end")
        self.bulk_text.tag_remove("ok_line",    "1.0", "end")

    def _bulk_parse(self) -> tuple[list[dict], list[tuple[int, str]]]:
        """テキストを解析して (ok_rows, errors) を返す。errors = [(行番号, メッセージ)]"""
        import io
        raw = self.bulk_text.get("1.0", "end")
        ok_rows: list[dict] = []
        errors: list[tuple[int, str]] = []

        for lineno, line in enumerate(raw.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue  # 空行・コメント行はスキップ

            # CSV パーサで1行分を解析（カンマを含む品詞を "" で囲むことに対応）
            try:
                parsed = next(csv.reader(io.StringIO(stripped)))
            except Exception:
                errors.append((lineno, "解析エラー"))
                continue

            if len(parsed) < 4:
                errors.append((lineno, f"フィールドが足りません（{len(parsed)} 個）: {stripped}"))
                continue

            # フィールド割り当て（かな は省略可）
            if len(parsed) == 4:
                kanji, romaji, word_type, meaning = (f.strip() for f in parsed)
                kana = ""
            else:
                kanji, romaji, kana, word_type, meaning = (
                    f.strip() for f in parsed[:5])

            field_errors = []
            if not kanji:     field_errors.append("日本語が空")
            if not romaji:    field_errors.append("ローマ字が空")
            if not word_type: field_errors.append("品詞が空")
            if not meaning:   field_errors.append("意味が空")
            if field_errors:
                errors.append((lineno, "  /  ".join(field_errors)))
                continue

            ok_rows.append({
                "ごい":    kanji,
                "ローマ字": romaji,
                "かな":    kana,
                "Type":    word_type,
                "Meaning": meaning,
            })

        return ok_rows, errors

    def _bulk_preview(self):
        self._bulk_clear_tags()
        import io
        raw = self.bulk_text.get("1.0", "end")
        ok_rows, errors = self._bulk_parse()

        # エラー行・OK行に色付け
        error_linenos = {ln for ln, _ in errors}
        ok_count = 0
        for lineno, line in enumerate(raw.splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            tag = "error_line" if lineno in error_linenos else "ok_line"
            if tag == "ok_line":
                ok_count += 1
            self.bulk_text.tag_add(tag, f"{lineno}.0", f"{lineno}.end")

        if errors:
            msg = "\n".join(f"  行 {ln}: {msg}" for ln, msg in errors[:20])
            if len(errors) > 20:
                msg += f"\n  …他 {len(errors) - 20} 件"
            messagebox.showwarning(
                "プレビュー結果",
                f"✅ 正常: {ok_count} 語　❌ エラー: {len(errors)} 行\n\n"
                f"エラー行（赤）を修正してから保存してください:\n{msg}")
        else:
            messagebox.showinfo(
                "プレビュー結果",
                f"✅ すべての行が正常です。{ok_count} 語を追加できます。\n\n"
                f"「💾 CSV に保存」で保存してください。")
        self.bulk_status.config(
            text=f"✅ {ok_count} 語  ❌ {len(errors)} 行エラー")

    def _bulk_save(self):
        ok_rows, errors = self._bulk_parse()
        if not ok_rows:
            messagebox.showwarning("警告", "追加できる単語がありません。\n"
                                   "まず「✅ プレビュー」で内容を確認してください。")
            return

        msg = f"{len(ok_rows)} 語を vocabulary.csv に追加します。"
        if errors:
            msg += f"\n（{len(errors)} 行はエラーのためスキップされます）"
        if not messagebox.askyesno("確認", msg):
            return

        base_n = next_number(self.rows)
        for i, row in enumerate(ok_rows):
            row["#"] = str(base_n + i)

        self.rows.extend(ok_rows)
        save_csv(self.rows)

        self.bulk_text.delete("1.0", "end")
        self._bulk_clear_tags()
        self._refresh_count()
        self._refresh_list()
        self.bulk_status.config(text="")
        messagebox.showinfo("保存完了",
                            f"{len(ok_rows)} 語を保存しました。\n"
                            f"現在の合計: {len(self.rows)} 語")

    # ══════════════════════════════════════════════════
    # タブ3: 一覧・編集
    # ══════════════════════════════════════════════════
    def _build_tab_list(self):
        # ── ツールバー ──
        bar = tk.Frame(self.tab_list, bg=BG3, padx=14, pady=8)
        bar.pack(fill="x")

        # 検索
        tk.Label(bar, text="🔍", font=FONT_BODY, bg=BG3, fg=TEXT_DIM
                 ).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh_list())
        tk.Entry(bar, textvariable=self.search_var,
                 font=FONT_BODY, bg=BG2, fg=TEXT, insertbackground=TEXT,
                 relief="flat", bd=4, width=22
                 ).pack(side="left", padx=(4, 16), ipady=4)

        tk.Button(bar, text="✏️  選択行を編集",
                  command=self._edit_selected,
                  bg=ACCENT, fg=TEXT, font=FONT_BODY,
                  relief="flat", cursor="hand2",
                  padx=12, pady=6).pack(side="left", padx=(0, 8))

        tk.Button(bar, text="🗑  選択行を削除",
                  command=self._delete_selected,
                  bg="#5a1a1a", fg=RED, font=FONT_BODY,
                  relief="flat", cursor="hand2",
                  padx=12, pady=6).pack(side="left", padx=(0, 8))

        tk.Button(bar, text="🔢 番号を整理",
                  command=self._renumber_all,
                  bg=BG2, fg=TEXT_DIM, font=FONT_SMALL,
                  relief="flat", cursor="hand2",
                  padx=10, pady=6).pack(side="left", padx=(0, 8))

        # ── テーブル ──
        tbl_frame = tk.Frame(self.tab_list, bg=BG2)
        tbl_frame.pack(fill="both", expand=True, padx=14, pady=(6, 14))

        vsb = tk.Scrollbar(tbl_frame, orient="vertical")
        hsb = tk.Scrollbar(tbl_frame, orient="horizontal")
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        s = ttk.Style()
        s.configure("Editor.Treeview",
                    background=BG2, foreground=TEXT,
                    fieldbackground=BG2, rowheight=26,
                    font=FONT_SMALL)
        s.configure("Editor.Treeview.Heading",
                    background=BG3, foreground=ACCENT2, font=FONT_SMALL)
        s.map("Editor.Treeview",
              background=[("selected", "#3a3a6a")])

        cols = ("#", "ごい", "ローマ字", "かな", "Type", "Meaning")
        self.tree = ttk.Treeview(tbl_frame, columns=cols, show="headings",
                                 yscrollcommand=vsb.set,
                                 xscrollcommand=hsb.set,
                                 style="Editor.Treeview",
                                 selectmode="extended")
        col_widths = {"#": 48, "ごい": 130, "ローマ字": 110,
                      "かな": 110, "Type": 240, "Meaning": 400}
        for c in cols:
            self.tree.heading(c, text=c,
                              command=lambda col=c: self._sort_col(col))
            self.tree.column(c, width=col_widths[c], anchor="w", minwidth=40)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

        self._refresh_list()

    def _refresh_list(self):
        q = self.search_var.get().lower() if hasattr(self, "search_var") else ""
        self.tree.delete(*self.tree.get_children())
        for row in self.rows:
            if q and not any(q in str(v).lower() for v in row.values()):
                continue
            self.tree.insert("", "end", iid=row["#"],
                             values=(row.get("#"), row.get("ごい"),
                                     row.get("ローマ字"), row.get("かな"),
                                     row.get("Type"), row.get("Meaning")))

    def _refresh_count(self):
        if hasattr(self, "lbl_count"):
            self.lbl_count.config(
                text=f"登録単語数: {len(self.rows)} 語  ／  "
                     f"次の番号: #{next_number(self.rows)}")

    def _edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("情報", "編集する行を選択してください。")
            return
        if len(sel) > 1:
            messagebox.showinfo("情報", "編集は1行ずつ行ってください。")
            return
        iid = sel[0]
        row = next((r for r in self.rows if r["#"] == iid), None)
        if not row:
            return

        EditDialog(self, row, self._on_edit_save)

    def _on_edit_save(self, original_num: str, new_data: dict):
        for i, r in enumerate(self.rows):
            if r["#"] == original_num:
                self.rows[i] = new_data
                break
        save_csv(self.rows)
        self._refresh_list()
        self._refresh_count()

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("情報", "削除する行を選択してください。")
            return
        if not messagebox.askyesno("確認",
                                   f"{len(sel)} 語を削除しますか？\nこの操作は元に戻せません。"):
            return
        self.rows = [r for r in self.rows if r["#"] not in sel]
        save_csv(self.rows)
        self._refresh_list()
        self._refresh_count()

    def _renumber_all(self):
        if not messagebox.askyesno("確認",
                                   "全単語の番号を 1 から振り直しますか？"):
            return
        self.rows.sort(key=lambda r: int(r["#"]) if r["#"].isdigit() else 9999)
        for i, r in enumerate(self.rows, 1):
            r["#"] = str(i)
        save_csv(self.rows)
        self._refresh_list()
        self._refresh_count()
        messagebox.showinfo("完了", "番号を整理しました。")

    def _sort_col(self, col: str):
        data = [(self.tree.set(c, col), c) for c in self.tree.get_children("")]
        try:
            data.sort(key=lambda x: int(x[0]))
        except ValueError:
            data.sort(key=lambda x: x[0].lower())
        for i, (_, c) in enumerate(data):
            self.tree.move(c, "", i)


# ══════════════════════════════════════════════════════════
# 編集ダイアログ
# ══════════════════════════════════════════════════════════
class EditDialog(tk.Toplevel):
    def __init__(self, master: WordEditorApp, row: dict, on_save):
        super().__init__(master, bg=BG2)
        self.title(f"単語を編集  —  #{row['#']}  {row.get('ごい', '')}")
        self.resizable(False, False)
        self.grab_set()
        self._row = row
        self._on_save = on_save

        fields = [
            ("番号 (#)",        "#",      False),
            ("日本語（ごい）*", "ごい",   True),
            ("ローマ字 *",      "ローマ字", True),
            ("かな（読み）",    "かな",   True),
            ("品詞 *",          "Type",   True),
            ("英語の意味 *",    "Meaning", True),
        ]

        self.vars: dict[str, tk.StringVar] = {}
        inner = tk.Frame(self, bg=BG2, padx=24, pady=20)
        inner.pack(fill="both", expand=True)

        for i, (lbl_text, key, editable) in enumerate(fields):
            tk.Label(inner, text=lbl_text, font=FONT_SMALL,
                     bg=BG2, fg=TEXT_DIM, anchor="w",
                     width=18).grid(row=i, column=0, sticky="w", pady=4)
            var = tk.StringVar(value=row.get(key, ""))
            self.vars[key] = var

            if key == "Type":
                widget = ttk.Combobox(inner, textvariable=var,
                                      values=WORD_TYPES, font=FONT_SMALL,
                                      width=44, state="normal")
            else:
                widget = tk.Entry(inner, textvariable=var,
                                  font=FONT_MONO if key == "Meaning" else FONT_BODY,
                                  bg=BG3 if editable else BG,
                                  fg=TEXT if editable else TEXT_DIM,
                                  insertbackground=TEXT,
                                  relief="flat", bd=4, width=46,
                                  state="normal" if editable else "disabled")
            widget.grid(row=i, column=1, sticky="w", padx=(8, 0),
                        pady=4, ipady=3)

        tk.Label(inner,
                 text="意味は ; で複数可  例: to eat; to consume",
                 font=FONT_SMALL, bg=BG2, fg=TEXT_DIM).grid(
            row=len(fields), column=0, columnspan=2, sticky="w", pady=(4, 12))

        btn_row = tk.Frame(inner, bg=BG2)
        btn_row.grid(row=len(fields) + 1, column=0, columnspan=2, sticky="e")
        tk.Button(btn_row, text="💾 保存", command=self._save,
                  bg="#2d6a4f", fg=TEXT, font=FONT_HEAD,
                  relief="flat", cursor="hand2",
                  padx=16, pady=6).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="キャンセル", command=self.destroy,
                  bg=BG3, fg=TEXT_DIM, font=FONT_BODY,
                  relief="flat", cursor="hand2",
                  padx=12, pady=6).pack(side="left")

        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width()  - self.winfo_width())  // 2
        y = master.winfo_y() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _save(self):
        new_data = {k: v.get().strip() for k, v in self.vars.items()}
        errors = []
        if not new_data.get("ごい"):   errors.append("「日本語」が空です")
        if not new_data.get("ローマ字"): errors.append("「ローマ字」が空です")
        if not new_data.get("Type"):    errors.append("「品詞」が空です")
        if not new_data.get("Meaning"): errors.append("「英語の意味」が空です")
        if errors:
            messagebox.showerror("入力エラー",
                                 "\n".join(f"・{e}" for e in errors))
            return
        self._on_save(self._row["#"], new_data)
        messagebox.showinfo("保存完了", "単語を更新しました。")
        self.destroy()


# ── エントリポイント ──────────────────────────────────────
def main():
    if not os.path.exists(CSV_PATH):
        messagebox.showerror("エラー",
                             f"vocabulary.csv が見つかりません:\n{CSV_PATH}")
        sys.exit(1)
    app = WordEditorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
