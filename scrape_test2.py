"""
Тестовый скрипт №2: используем headless-браузер (Playwright/Chromium),
чтобы страница форума реально выполнила JS-проверку Cloudflare, как в обычном браузере,
и мы получили настоящий HTML с постами, а не страницу "Just a moment...".
"""

import json
import sys
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

TOPIC_URL = "https://antio.ru/index.php?showtopic=85035"


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Открываю (headless-браузер): {TOPIC_URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
        )
        page = context.new_page()

        page.goto(TOPIC_URL, wait_until="domcontentloaded", timeout=30000)

        # Даём странице шанс пройти проверку Cloudflare самостоятельно
        # (она обычно делает редирект/перезагрузку через несколько секунд).
        try:
            page.wait_for_selector('div.post_block[id^="post_id_"]', timeout=20000)
            passed = True
        except Exception:
            passed = False

        title = page.title()
        html = page.content()
        print(f"Заголовок страницы: {title}")
        print(f"Прошли проверку и увидели посты: {passed}")

        if not passed:
            with open("test_result.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("Посты не найдены — сохранил HTML в test_result.html для разбора.")
            browser.close()
            sys.exit(0)

        browser.close()

    soup = BeautifulSoup(html, "html.parser")
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
            "text": text[:300],
        })

    for p_ in posts:
        print("—" * 40)
        print(f"#{p_['post_id']} | {p_['author']} | {p_['timestamp']}")
        print(p_["text"])

    with open("test_result.json", "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print("—" * 40)
    print(f"Готово. Сохранено {len(posts)} постов в test_result.json")


if __name__ == "__main__":
    main()
