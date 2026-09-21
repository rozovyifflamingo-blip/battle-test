"""
Тестовый скрипт: проверяет, видит ли GitHub Actions тему форума AntiO,
и парсит текст постов (без сравнения с предыдущим состоянием — просто разовая проверка).
"""

import json
import sys
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

TOPIC_URL = "https://antio.ru/index.php?showtopic=85035"

HEADERS = {
    # Многие форумы блокируют запросы без нормального User-Agent
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru,en;q=0.8",
}


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Запрашиваю: {TOPIC_URL}")

    try:
        resp = requests.get(TOPIC_URL, headers=HEADERS, timeout=20)
    except Exception as e:
        print(f"ОШИБКА СЕТИ: {e}")
        sys.exit(1)

    print(f"HTTP статус: {resp.status_code}")
    print(f"Размер ответа: {len(resp.text)} байт")

    if resp.status_code != 200:
        print("Страница не отдалась с кодом 200 — возможно, форум блокирует дата-центр GitHub, "
              "либо нужна авторизация/капча.")
        # Сохраним, что пришло, чтобы посмотреть глазами
        with open("test_result.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
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

        posts.append({
            "post_id": post_id,
            "author": author,
            "timestamp": timestamp,
            "text": text[:300],  # обрезаем для теста, чтобы не захламлять вывод
        })

    # Печатаем в лог Actions — это и есть "проверка, что видно"
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
