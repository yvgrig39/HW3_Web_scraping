import requests
from bs4 import BeautifulSoup
import time

# Список ключевых слов для поиска
KEYWORDS = ['дизайн', 'фото', 'web', 'python']
URL = 'https://habr.com/ru/articles/'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

def fetch_and_parse(url):
    """
    Безопасно получает и парсит HTML-страницу.
    Возвращает объект BeautifulSoup или None в случае ошибки.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Проверяем статус ответа (200, 404, 500...)
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при загрузке страницы {url}: {e}")
        return None

def get_full_article_text(article_url):
    """Загружает полный текст статьи по ссылке."""
    soup = fetch_and_parse(article_url)
    if not soup:
        return ''

    # Ищем блок с полным текстом статьи
    article_body = soup.find('div', class_='article-formatted-body')
    if article_body:
        # Убираем шум (скрипты, стили и блоки с кодом)
        for unwanted in article_body.find_all(['script', 'style', 'code', 'pre']):
            unwanted.decompose()
        return article_body.get_text(separator=' ', strip=True)
    return ''

def main():
    # 1. Получаем и парсим главную страницу
    main_soup = fetch_and_parse(URL)
    if not main_soup:
        print("Не удалось загрузить главную страницу. Проверьте соединение или URL.")
        return

    # 2. Находим все блоки статей на главной
    articles = main_soup.find_all('article', class_='tm-articles-list__item')
    if not articles:
        print("На главной странице не найдено статей. Возможно, изменилась структура HTML.")
        return

    print(f"Поиск по ключевым словам: {', '.join(KEYWORDS)}")
    print("=" * 80)

    found_count = 0
    for article in articles:
        # --- Извлекаем дату ---
        # <a class="tm-article-datetime-published"> внутри <time datetime="...">
        date_tag = article.find('a', class_='tm-article-datetime-published')
        if not date_tag:
            continue
        time_tag = date_tag.find('time')
        if not time_tag or not time_tag.has_attr('datetime'):
            continue
        date = time_tag['datetime'].split('T')[0]

        # --- Извлекаем заголовок и ссылку ---
        # <h2 class="tm-title tm-title_h2"> внутри <a class="tm-title__link">
        title_tag = article.find('h2', class_='tm-title')
        if not title_tag:
            continue
        link_tag = title_tag.find('a', class_='tm-title__link')
        if not link_tag:
            continue

        title = link_tag.get_text(strip=True)
        link = link_tag['href']
        if not link.startswith('http'):
            link = 'https://habr.com' + link

        # --- Извлекаем текст preview ---
        preview_tag = article.find('div', class_='article-formatted-body')
        if not preview_tag:
            # Запасной вариант: собираем текст из всех параграфов
            paragraphs = article.find_all('p')
            preview_text = ' '.join(p.get_text(strip=True) for p in paragraphs)
        else:
            preview_text = preview_tag.get_text()

        # --- Проверяем ключевые слова (сначала быстро в заголовке и preview) ---
        combined_text = (title + ' ' + preview_text).lower()
        found_keywords = [kw for kw in KEYWORDS if kw.lower() in combined_text]

        if not found_keywords:
            # --- Если не нашли — загружаем и проверяем полный текст ---
            full_text = get_full_article_text(link)
            full_text_lower = full_text.lower()
            found_keywords = [kw for kw in KEYWORDS if kw.lower() in full_text_lower]
            time.sleep(0.3)  # небольшая задержка, чтобы не перегружать сервер

        # --- Выводим результат в строгом формате, только если ключевые слова найдены ---
        if found_keywords:
            print(f"{date} – {title} – {link}")
            found_count += 1

    print("=" * 80)
    print(f"Найдено статей: {found_count}")

if __name__ == "__main__":
    main()