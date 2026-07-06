"""
crawl.py
[本番用] 対象URLリスト(urls.csv)を巡回し、本文テキストを取得するクローラー。

このスクリプトは実際のインターネットアクセスが必要なため、開発サンドボックス内では
実行できない(アウトバウンド通信が制限されているため)。GitHub Actions等、
通常のインターネットアクセスがある環境で実行することを想定している。

必要パッケージ: requests, beautifulsoup4
    pip install requests beautifulsoup4

使い方:
    python crawl.py urls.csv fixtures_out/

urls.csv フォーマート: field_name,url
"""
import csv
import os
import re
import sys
import time


def fetch_text(url: str, timeout=15) -> str:
    import requests
    from bs4 import BeautifulSoup

    headers = {"User-Agent": "SabageFieldDB-Bot/0.1 (+contact: operator@example.com)"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def crawl_all(urls_csv: str, out_dir: str, delay_sec: float = 2.0):
    """
    robots.txt を尊重し、サーバー負荷を避けるため各リクエストの間に delay_sec 秒あける。
    (本番実装では urllib.robotparser で robots.txt を都度チェックすることを推奨)
    """
    os.makedirs(out_dir, exist_ok=True)
    results = []
    with open(urls_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name, url = row["field_name"], row["url"]
            try:
                text = fetch_text(url)
                out_path = os.path.join(out_dir, f"{name}.txt")
                with open(out_path, "w", encoding="utf-8") as out:
                    out.write(text)
                results.append((name, url, "OK"))
            except Exception as e:
                results.append((name, url, f"ERROR: {e}"))
            time.sleep(delay_sec)
    return results


if __name__ == "__main__":
    urls_csv, out_dir = sys.argv[1], sys.argv[2]
    results = crawl_all(urls_csv, out_dir)
    for name, url, status in results:
        print(f"{status:10s} {name} ({url})")
