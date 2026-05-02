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
    """Безопасно получает и парсит HTML-страницу."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException:
        return None


def get_full_article_text(article_url):
    """Загружает полный текст статьи по ссылке."""
    soup = fetch_and_parse(article_url)
    if not soup:
        return ''

    article_body = soup.find('div', class_='article-formatted-body')
    if article_body:
        for unwanted in article_body.find_all(['script', 'style', 'code', 'pre']):
            unwanted.decompose()
        return article_body.get_text(separator=' ', strip=True)
    return ''


def main():
    main_soup = fetch_and_parse(URL)
    if not main_soup:
        return

    articles = main_soup.find_all('article', class_='tm-articles-list__item')
    if not articles:
        return

    for article in articles:
        # Извлекаем дату
        date_tag = article.find('a', class_='tm-article-datetime-published')
        if not date_tag:
            continue
        time_tag = date_tag.find('time')
        if not time_tag or not time_tag.has_attr('datetime'):
            continue
        date = time_tag['datetime'].split('T')[0]

        # Извлекаем заголовок и ссылку
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

        # Извлекаем текст preview
        preview_tag = article.find('div', class_='article-formatted-body')
        if preview_tag:
            preview_text = preview_tag.get_text()
        else:
            paragraphs = article.find_all('p')
            preview_text = ' '.join(p.get_text(strip=True) for p in paragraphs)

        # Проверяем ключевые слова в preview
        combined_text = (title + ' ' + preview_text).lower()
        found_keywords = [kw for kw in KEYWORDS if kw.lower() in combined_text]

        # Если не нашли - проверяем полный текст
        if not found_keywords:
            full_text = get_full_article_text(link)
            if full_text:
                found_keywords = [kw for kw in KEYWORDS if kw.lower() in full_text.lower()]
            time.sleep(0.3)

        # Выводим только найденные статьи в нужном формате
        if found_keywords:
            print(f"{date} – {title} – {link}")


if __name__ == "__main__":
    main()