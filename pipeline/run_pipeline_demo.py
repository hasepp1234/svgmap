"""
run_pipeline_demo.py
このセッションで実際に取得した4フィールドの公式サイト本文(fixtures/)を使い、
「抽出 → 既存DBとの差分検知 → レビューキュー出力」までの一連の流れを実行するデモ。

本番では crawl.py が fixtures/ の中身を毎月自動生成する。
"""
import json
import os
from extractor import extract
from diff_check import build_review_queue

FIXTURE_MAP = {
    "isgf.txt": "ISGF(糸島サバイバルゲームフィールド)",
    "fukuoka_sabage_land.txt": "福岡サバゲーランド",
    "hokkaido_hsp.txt": "北海道サバイバルゲームパーク",
    "tokyo_sabage_park.txt": "東京サバゲパーク",
}

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    crawl_results = {}
    for fname, field_name in FIXTURE_MAP.items():
        text = open(os.path.join(HERE, "fixtures", fname), encoding="utf-8").read()
        crawl_results[field_name] = extract(text)

    crawl_out_path = os.path.join(HERE, "crawl_results.json")
    with open(crawl_out_path, "w", encoding="utf-8") as f:
        json.dump(crawl_results, f, ensure_ascii=False, indent=2)
    print(f"抽出結果を {crawl_out_path} に保存しました\n")

    baseline_path = os.path.join(HERE, "..", "fields.json")
    review_csv = os.path.join(HERE, "review_queue.csv")
    rows = build_review_queue(baseline_path, crawl_out_path, review_csv)
    print(f"\nレビューキュー: {len(rows)} 件 -> {review_csv}")


if __name__ == "__main__":
    main()
