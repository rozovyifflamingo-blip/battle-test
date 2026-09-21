"""
Тест №3: заходим на тему через прокси.
"""

import json
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

TOPIC_URL = "https://antio.ru/index.php?showtopic=85035"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru,en;q=0.8",
}

PROXY_HOST = "dc03.steelproxy.com"
PROXY_PORT = "3071"
PROXY_USER = "5caDYcWX"
PROXY_PASS = "c8tV1Bt8"


def build_proxy_url():
    return f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"


def main():
    proxy_url = build_proxy_url()
    proxies = {"http": proxy_url, "https": proxy_url}

    print(f"[{datetime.now(timezone.utc).isoformat()}] Запрашиваю через прокси: {TOPIC_URL}")

    try:
        resp = requests.get(TOPIC_URL, headers=HEADERS, proxies=proxies, timeout=25)
    except Exception as e:
        print(f"ОШИБКА СЕТИ (возможно, прокси недоступен): {e}")
        sys.exit(1)

    print(f"HTTP статус: {resp.status_code}")
    print(f"Размер ответа: {len(resp.text)} байт")

    with open("test_result.html", "w", encoding="utf-8") as f:
        f.write(resp.text)

    if "Just a moment" in resp.text or "Один момент" in resp.text:
        print("Всё ещё упёрлись в Cloudflare-проверку, даже через прокси.")
        sys.exit(0)

    if resp.status_code != 200:
        print("Не 200 — смотрим test_result.html в артефакте.")
        sys.exit(0)

    soup = BeautifulSoup(resp.text, "html.parser")
    post_blocks = soup.select('div.post_block[id^="post_id_"]')
    print(f"Найдено блоков постов: {len(post_blocks)}")

    posts = []
    for block in post_blocks:
        post_id = block.get("id", "").replace("post_id_", "")
        author_el = block.select_one('span[itemprop="creator name"] span[itemprop="name"]')
        author = author_el.get_text(strip=True) if author_el else "???"
        time_el = block.select_one("abbr.published")
        timestamp = time_el.get("title") if time_el else None
        text_el = block.select_one('div[itemprop="commentText"]')
        text = text_el.get_text(" ", strip=True) if text_el else ""
        posts.append({"post_id": post_id, "author": author, "timestamp": timestamp, "text": text[:300]})

    for p in posts:
        print("—" * 40)
        print(f"#{p['post_id']} | {p['author']} | {p['timestamp']}")
        print(p["text"])

    with open("test_result.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print("—" * 40)
    print(f"Готово. Сохранено {len(posts)} постов в test_result.json")


if __name__ == "__main__":
    main()
