"""
EJTester - 英語・日本語単語テストプログラム
"""

import csv
import random
import os
import sys
from dataclasses import dataclass, field
from typing import Optional


# ──────────────────────────────────────────────
# データモデル
# ──────────────────────────────────────────────
@dataclass
class Word:
    number: int
    kanji: str          # 漢字・表記
    romaji: str         # ローマ字
    kana: str           # ひらがな/カタカナ
    word_type: str      # 品詞
    meaning: str        # 英語の意味

    def display_japanese(self) -> str:
        """日本語表示（漢字 + かな）"""
        if self.kana and self.kana != self.kanji:
            return f"{self.kanji}（{self.kana}）"
        return self.kanji

    def primary_meaning(self) -> str:
        """最初の意味だけを返す"""
        return self.meaning.split(";")[0].strip()


@dataclass
class QuizResult:
    total: int = 0
    correct: int = 0
    wrong_words: list = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        if self.total == 0:
            return 0.0
        return self.correct / self.total * 100


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
# 表示ユーティリティ
# ──────────────────────────────────────────────
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title: str):
    line = "═" * 50
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}")


def print_progress(current: int, total: int, correct: int):
    bar_len = 30
    filled = int(bar_len * current / total) if total else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    pct = current / total * 100 if total else 0
    print(f"\n  進捗: [{bar}] {current}/{total}  ({pct:.0f}%)")
    print(f"  正解: {correct}  不正解: {current - correct - (1 if current < total else 0)}")


# ──────────────────────────────────────────────
# クイズ問題生成
# ──────────────────────────────────────────────
def make_choices(words: list[Word], correct: Word, n: int = 4) -> list[str]:
    """ランダムな選択肢を作る（正解含む）"""
    others = [w for w in words if w.number != correct.number]
    distractors = random.sample(others, min(n - 1, len(others)))
    choices = [correct.meaning] + [d.meaning for d in distractors]
    random.shuffle(choices)
    return choices


# ──────────────────────────────────────────────
# 問題モード
# ──────────────────────────────────────────────
def quiz_en_to_jp(words: list[Word], result: QuizResult):
    """英語 → 日本語（意味を見て日本語を答える）"""
    q = random.choice(words)
    print(f"\n  問題: 「{q.meaning}」")
    print(f"  ヒント: {q.word_type}")
    answer = input("\n  日本語（漢字・ひらがな・カタカナいずれか）を入力: ").strip()
    correct_answers = [q.kanji, q.kana, q.romaji]
    correct_answers = [a for a in correct_answers if a]

    if answer in correct_answers:
        print("  ✅ 正解！")
        result.correct += 1
    else:
        print(f"  ❌ 不正解。正解は「{q.display_japanese()}」（{q.romaji}）")
        result.wrong_words.append(q)
    result.total += 1


def quiz_jp_to_en_typing(words: list[Word], result: QuizResult):
    """日本語 → 英語（タイピング）"""
    q = random.choice(words)
    print(f"\n  問題: 「{q.display_japanese()}」（{q.romaji}）")
    print(f"  ヒント: {q.word_type}")
    answer = input("\n  英語の意味を入力: ").strip().lower()

    # 意味のいずれかのキーワードが含まれていれば正解とする
    meanings = [m.strip().lower() for m in q.meaning.replace(";", ",").split(",")]
    if any(answer == m for m in meanings) or answer in q.meaning.lower():
        print("  ✅ 正解！")
        result.correct += 1
    else:
        print(f"  ❌ 不正解。正解は「{q.meaning}」")
        result.wrong_words.append(q)
    result.total += 1


def quiz_jp_to_en_choice(words: list[Word], result: QuizResult):
    """日本語 → 英語（4択）"""
    q = random.choice(words)
    choices = make_choices(words, q, n=4)

    print(f"\n  問題: 「{q.display_japanese()}」（{q.romaji}）")
    print(f"  ヒント: {q.word_type}\n")
    for i, choice in enumerate(choices, 1):
        print(f"    {i}. {choice}")

    while True:
        raw = input("\n  番号を選んでください (1-4): ").strip()
        if raw in {"1", "2", "3", "4"}:
            break
        print("  1〜4 の番号を入力してください。")

    selected = choices[int(raw) - 1]
    if selected == q.meaning:
        print("  ✅ 正解！")
        result.correct += 1
    else:
        print(f"  ❌ 不正解。正解は「{q.meaning}」")
        result.wrong_words.append(q)
    result.total += 1


def quiz_romaji_to_jp(words: list[Word], result: QuizResult):
    """ローマ字 → 日本語（4択）"""
    q = random.choice(words)
    others = [w for w in words if w.number != q.number]
    distractors = random.sample(others, min(3, len(others)))
    choices = [q.display_japanese()] + [d.display_japanese() for d in distractors]
    random.shuffle(choices)

    print(f"\n  問題: 「{q.romaji}」の意味は？")
    print(f"  英語: {q.meaning}\n")
    for i, choice in enumerate(choices, 1):
        print(f"    {i}. {choice}")

    while True:
        raw = input("\n  番号を選んでください (1-4): ").strip()
        if raw in {"1", "2", "3", "4"}:
            break
        print("  1〜4 の番号を入力してください。")

    selected = choices[int(raw) - 1]
    if selected == q.display_japanese():
        print("  ✅ 正解！")
        result.correct += 1
    else:
        print(f"  ❌ 不正解。正解は「{q.display_japanese()}」")
        result.wrong_words.append(q)
    result.total += 1


# ──────────────────────────────────────────────
# 結果表示
# ──────────────────────────────────────────────
def show_result(result: QuizResult):
    print_header("テスト結果")
    print(f"\n  問題数  : {result.total}")
    print(f"  正解数  : {result.correct}")
    print(f"  不正解  : {result.total - result.correct}")
    print(f"  正解率  : {result.accuracy:.1f}%")

    if result.accuracy == 100:
        print("\n  🎉 パーフェクト！素晴らしいです！")
    elif result.accuracy >= 80:
        print("\n  👍 よくできました！")
    elif result.accuracy >= 60:
        print("\n  📚 もう少し練習しましょう！")
    else:
        print("\n  💪 もっと頑張りましょう！")

    if result.wrong_words:
        print("\n  ── 間違えた単語 ──────────────────────")
        for w in result.wrong_words:
            print(f"    • {w.display_japanese()} ({w.romaji}) ： {w.meaning}")
    print()


# ──────────────────────────────────────────────
# 単語一覧表示
# ──────────────────────────────────────────────
def show_word_list(words: list[Word]):
    print_header("単語一覧")
    print(f"\n  {'No.':<5} {'日本語':<20} {'ローマ字':<20} {'意味'}")
    print("  " + "─" * 70)
    for w in words:
        jp = w.display_japanese()
        print(f"  {w.number:<5} {jp:<20} {w.romaji:<20} {w.primary_meaning()}")
    print()
    input("  [Enter] でメニューに戻る... ")


# ──────────────────────────────────────────────
# フィルタ設定
# ──────────────────────────────────────────────
def filter_menu(words: list[Word]) -> list[Word]:
    print_header("単語フィルタ設定")
    types = sorted(set(w.word_type for w in words))
    print("\n  品詞で絞り込む場合は番号を入力（複数はカンマ区切り）")
    print("  すべての単語を使う場合は [Enter] をそのまま押す\n")
    for i, t in enumerate(types, 1):
        count = sum(1 for w in words if w.word_type == t)
        print(f"    {i:>2}. {t}  ({count}語)")

    raw = input("\n  選択 (例: 1,3): ").strip()
    if not raw:
        print(f"\n  すべての単語 {len(words)} 語を使用します。")
        return words

    try:
        indices = [int(x.strip()) - 1 for x in raw.split(",")]
        selected_types = [types[i] for i in indices if 0 <= i < len(types)]
        filtered = [w for w in words if w.word_type in selected_types]
        if not filtered:
            print("  絞り込み結果が 0 語でした。全単語を使用します。")
            return words
        print(f"\n  選択された単語: {len(filtered)} 語")
        return filtered
    except (ValueError, IndexError):
        print("  入力が正しくありません。全単語を使用します。")
        return words


# ──────────────────────────────────────────────
# テスト設定
# ──────────────────────────────────────────────
def select_quiz_count(max_count: int) -> int:
    print(f"\n  問題数を入力してください (1〜{max_count}、デフォルト: 10): ", end="")
    raw = input().strip()
    if not raw:
        return min(10, max_count)
    try:
        n = int(raw)
        return max(1, min(n, max_count))
    except ValueError:
        return min(10, max_count)


def select_quiz_mode() -> str:
    print("\n  出題モードを選んでください:")
    print("    1. 日本語 → 英語（4択）")
    print("    2. 日本語 → 英語（記述）")
    print("    3. 英語 → 日本語（記述）")
    print("    4. ローマ字 → 日本語（4択）")
    print("    5. ランダム（全モード混合）")
    while True:
        raw = input("\n  番号を入力: ").strip()
        if raw in {"1", "2", "3", "4", "5"}:
            return raw
        print("  1〜5 の番号を入力してください。")


# ──────────────────────────────────────────────
# テスト実行
# ──────────────────────────────────────────────
def run_quiz(words: list[Word]):
    filtered = filter_menu(words)
    count = select_quiz_count(len(filtered))
    mode = select_quiz_mode()

    mode_funcs = {
        "1": quiz_jp_to_en_choice,
        "2": quiz_jp_to_en_typing,
        "3": quiz_en_to_jp,
        "4": quiz_romaji_to_jp,
    }

    result = QuizResult()
    quiz_words = random.sample(filtered, count)

    for i, _ in enumerate(quiz_words):
        clear_screen()
        print_header("英語・日本語 単語テスト")
        print_progress(i, count, result.correct)

        if mode == "5":
            func = random.choice(list(mode_funcs.values()))
        else:
            func = mode_funcs[mode]

        # 問題プールは filtered 全体を使い、正解は quiz_words から選ぶ
        # 一時的に正解を差し替えて呼ぶ
        current_word = quiz_words[i]

        # 各関数を直接呼ぶ代わりに、単語を特定して出題する
        _run_single(mode if mode != "5" else random.choice(["1", "2", "3", "4"]),
                    filtered, current_word, result)

    clear_screen()
    show_result(result)

    input("  [Enter] でメニューに戻る... ")


def _run_single(mode: str, all_words: list[Word], q: Word, result: QuizResult):
    """指定単語を正解として出題する"""
    if mode == "1":
        # 4択: 日本語 → 英語
        choices = make_choices(all_words, q, n=4)
        print(f"\n  問題: 「{q.display_japanese()}」（{q.romaji}）")
        print(f"  ヒント: {q.word_type}\n")
        for i, choice in enumerate(choices, 1):
            print(f"    {i}. {choice}")
        while True:
            raw = input("\n  番号を選んでください (1-4): ").strip()
            if raw in {"1", "2", "3", "4"}:
                break
            print("  1〜4 の番号を入力してください。")
        selected = choices[int(raw) - 1]
        if selected == q.meaning:
            print("  ✅ 正解！")
            result.correct += 1
        else:
            print(f"  ❌ 不正解。正解は「{q.meaning}」")
            result.wrong_words.append(q)

    elif mode == "2":
        # 記述: 日本語 → 英語
        print(f"\n  問題: 「{q.display_japanese()}」（{q.romaji}）")
        print(f"  ヒント: {q.word_type}")
        answer = input("\n  英語の意味を入力: ").strip().lower()
        meanings = [m.strip().lower() for m in q.meaning.replace(";", ",").split(",")]
        if any(answer == m for m in meanings) or answer in q.meaning.lower():
            print("  ✅ 正解！")
            result.correct += 1
        else:
            print(f"  ❌ 不正解。正解は「{q.meaning}」")
            result.wrong_words.append(q)

    elif mode == "3":
        # 記述: 英語 → 日本語
        print(f"\n  問題: 「{q.meaning}」")
        print(f"  ヒント: {q.word_type}")
        answer = input("\n  日本語（漢字・ひらがな・カタカナいずれか）を入力: ").strip()
        correct_answers = [a for a in [q.kanji, q.kana, q.romaji] if a]
        if answer in correct_answers:
            print("  ✅ 正解！")
            result.correct += 1
        else:
            print(f"  ❌ 不正解。正解は「{q.display_japanese()}」（{q.romaji}）")
            result.wrong_words.append(q)

    elif mode == "4":
        # 4択: ローマ字 → 日本語
        others = [w for w in all_words if w.number != q.number]
        distractors = random.sample(others, min(3, len(others)))
        choices = [q.display_japanese()] + [d.display_japanese() for d in distractors]
        random.shuffle(choices)
        print(f"\n  問題: 「{q.romaji}」の意味は？")
        print(f"  英語: {q.meaning}\n")
        for i, choice in enumerate(choices, 1):
            print(f"    {i}. {choice}")
        while True:
            raw = input("\n  番号を選んでください (1-4): ").strip()
            if raw in {"1", "2", "3", "4"}:
                break
            print("  1〜4 の番号を入力してください。")
        selected = choices[int(raw) - 1]
        if selected == q.display_japanese():
            print("  ✅ 正解！")
            result.correct += 1
        else:
            print(f"  ❌ 不正解。正解は「{q.display_japanese()}」")
            result.wrong_words.append(q)

    result.total += 1
    input("\n  [Enter] で次へ... ")


# ──────────────────────────────────────────────
# メインメニュー
# ──────────────────────────────────────────────
def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "vocabulary.csv")

    if not os.path.exists(csv_path):
        print(f"エラー: vocabulary.csv が見つかりません ({csv_path})")
        sys.exit(1)

    words = load_vocabulary(csv_path)

    while True:
        clear_screen()
        print_header("🗾 英語・日本語 単語テスト")
        print(f"\n  単語数: {len(words)} 語\n")
        print("  1. テストを開始する")
        print("  2. 単語一覧を見る")
        print("  3. 終了")
        print()

        choice = input("  番号を選んでください: ").strip()

        if choice == "1":
            run_quiz(words)
        elif choice == "2":
            clear_screen()
            show_word_list(words)
        elif choice == "3":
            print("\n  さようなら！またね！👋\n")
            break
        else:
            print("  1〜3 の番号を入力してください。")
            input("  [Enter] で続ける... ")


if __name__ == "__main__":
    main()
