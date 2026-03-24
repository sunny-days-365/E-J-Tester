"""
EJTester - 単語別間違え回数ログ
mistake_log.json に { "単語番号(str)": 間違え回数(int) } を保存する。
"""

import json
import os

_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mistake_log.json")


def load_log() -> dict[str, int]:
    """間違えログを読み込んで返す。ファイルがなければ空 dict。"""
    if not os.path.exists(_LOG_PATH):
        return {}
    try:
        with open(_LOG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return {str(k): int(v) for k, v in data.items()}
    except Exception:
        return {}


def save_log(log: dict[str, int]):
    """間違えログをファイルに保存する。"""
    with open(_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def record_results(wrong_word_numbers: list[int], correct_word_numbers: list[int]):
    """
    テスト結果を受け取り、ログを更新して保存する。
    - 間違えた単語: +1
    - 正解した単語: 回数は減らさない（蓄積型）
    """
    log = load_log()
    for num in wrong_word_numbers:
        key = str(num)
        log[key] = log.get(key, 0) + 1
    save_log(log)


def get_mistake_count(word_number: int, log: dict[str, int] | None = None) -> int:
    """指定した単語番号の間違え回数を返す。"""
    if log is None:
        log = load_log()
    return log.get(str(word_number), 0)


def reset_log():
    """間違えログを全てリセットする。"""
    save_log({})


def reset_word(word_number: int):
    """指定した単語番号のログだけリセットする。"""
    log = load_log()
    key = str(word_number)
    if key in log:
        del log[key]
    save_log(log)
