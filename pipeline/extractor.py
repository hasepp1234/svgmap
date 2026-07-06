"""
extractor.py
公式サイトの本文テキストから料金・レンタル・タイプ情報を抽出するヒューリスティック抽出器 (v1)。

v1はAPIキー不要で動く正規表現ベースの抽出器。
本番運用では、この抽出結果を Claude API による自然言語構造化抽出 (extract_with_llm) に
差し替える／併用することで、表記ゆれや複雑な料金体系にも対応できるようにする拡張ポイントを用意している。
"""
import re
import json
import sys

PRICE_RE = re.compile(r"([￥¥]\s?[\d,]{3,7}-?|[\d,]{3,7}\s?円)")
RENTAL_KEYWORDS = ["レンタル", "貸出", "貸し出し"]
INDOOR_KEYWORDS = ["屋内", "インドア", "ビル", "スタジオ"]
OUTDOOR_KEYWORDS = ["屋外", "森林", "アウトドア", "山", "野外"]
CHARTER_KEYWORDS = ["貸切"]
HOURS_RE = re.compile(r"営業時間[^\n]{0,40}")


def extract_price_lines(text: str):
    """価格を含む行を「ラベル: 金額」の形で抽出する"""
    results = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        matches = PRICE_RE.findall(line)
        if matches:
            results.append({"line": line, "prices": matches})
    return results


def detect_rental(text: str) -> bool:
    return any(kw in text for kw in RENTAL_KEYWORDS)


def detect_type(text: str) -> str:
    indoor = any(kw in text for kw in INDOOR_KEYWORDS)
    outdoor = any(kw in text for kw in OUTDOOR_KEYWORDS)
    if indoor and outdoor:
        return "屋内/屋外"
    if indoor:
        return "屋内"
    if outdoor:
        return "屋外"
    return "要確認"


def detect_charter(text: str) -> bool:
    return any(kw in text for kw in CHARTER_KEYWORDS)


def detect_hours(text: str):
    m = HOURS_RE.search(text)
    return m.group(0) if m else None


def extract_with_llm(text: str, api_key: str = None):
    """
    [拡張ポイント] Claude APIを使った高精度抽出のスタブ。
    本番では以下のようにAnthropic SDKを呼び出し、料金体系・レンタル項目・
    営業日など複雑な自然文をJSON Schemaに沿って構造化する。

        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            messages=[{"role": "user", "content": f"次のフィールド公式サイト本文から料金/レンタル/屋内外/営業時間をJSONで抽出して:\n{text}"}]
        )
        return json.loads(resp.content[0].text)

    このスタブはAPIキー未設定時にNoneを返し、呼び出し側はv1(正規表現)結果にフォールバックする。
    """
    if not api_key:
        return None
    raise NotImplementedError("本番環境でAnthropic SDKを組み込んでください")


def extract(text: str, api_key: str = None) -> dict:
    llm_result = extract_with_llm(text, api_key)
    if llm_result:
        return llm_result

    price_lines = extract_price_lines(text)
    top_prices = [p["line"] for p in price_lines[:5]]
    return {
        "price_summary": " ／ ".join(top_prices) if top_prices else "要確認",
        "rental_detected": detect_rental(text),
        "type_guess": detect_type(text),
        "charter_available": detect_charter(text),
        "hours": detect_hours(text),
        "raw_price_line_count": len(price_lines),
    }


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    if not path:
        print("usage: python extractor.py <fixture_text_file>")
        sys.exit(1)
    text = open(path, encoding="utf-8").read()
    result = extract(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
