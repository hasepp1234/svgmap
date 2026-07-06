"""
diff_check.py
既存DB(fields.json)と最新クロール結果を比較し、差分のみをレビューキューに出力する。
運用工数を月2〜3時間に抑える設計の中核: 「全件を人が見る」のではなく「変化した点だけ」を見る。
"""
import json
import sys
import csv

REVIEW_NEEDED_MARKERS = ["要確認", "要公式サイト確認", ""]


def needs_review(baseline_value: str) -> bool:
    return baseline_value is None or any(m == baseline_value for m in REVIEW_NEEDED_MARKERS)


def build_review_queue(baseline_path: str, crawl_results_path: str, out_csv: str):
    baseline = {f["name"]: f for f in json.load(open(baseline_path, encoding="utf-8"))}
    crawl_results = json.load(open(crawl_results_path, encoding="utf-8"))

    rows = []
    for name, extracted in crawl_results.items():
        base = baseline.get(name)
        if base is None:
            rows.append({
                "field_name": name,
                "status": "新規フィールド候補",
                "baseline_price": "-",
                "crawled_price_summary": extracted.get("price_summary", ""),
                "action": "レビューして新規追加",
            })
            continue

        if needs_review(base.get("price")):
            rows.append({
                "field_name": name,
                "status": "料金情報が未確認 → 新規取得あり",
                "baseline_price": base.get("price"),
                "crawled_price_summary": extracted.get("price_summary", ""),
                "action": "内容確認のうえ承認すればDBへ反映",
            })
        elif base.get("price") != extracted.get("price_summary"):
            rows.append({
                "field_name": name,
                "status": "料金情報が変化した可能性 → 要レビュー",
                "baseline_price": base.get("price"),
                "crawled_price_summary": extracted.get("price_summary", ""),
                "action": "差分を確認して承認/却下",
            })
        # 一致している場合は何も出力しない = レビュー不要

    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["field_name", "status", "baseline_price", "crawled_price_summary", "action"])
        writer.writeheader()
        writer.writerows(rows)

    return rows


if __name__ == "__main__":
    baseline_path, crawl_results_path, out_csv = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = build_review_queue(baseline_path, crawl_results_path, out_csv)
    print(f"レビュー対象 {len(rows)} 件を {out_csv} に出力しました")
    for r in rows:
        print(" -", r["field_name"], ":", r["status"])
