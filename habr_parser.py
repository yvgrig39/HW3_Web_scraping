import requests
from bs4 import BeautifulSoup
import time

# Определяем список ключевых слов:
KEYWORDS = ['дизайн', 'фото', 'web', 'python']

URL = 'https://habr.com/ru/articles/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

def get_full_article_text(article_url):
    """
    Загружает полный текст статьи по ссылке
    Полный текст лежит в <div class="article-formatted-body">
    """
    try:
        response = requests.get(article_url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Полный текст лежит в <div class="article-formatted-body">
        article_body = soup.find('div', class_='article-formatted-body')

        if article_body:
            # Убираем лишние элементы (скрипты, стили, код)
            for unwanted in article_body.find_all(['script', 'style', 'code', 'pre']):
                unwanted.decompose()

            return article_body.get_text(separator=' ', strip=True)
        return ''

    except Exception as e:
        print(f"  Ошибка при загрузке статьи: {e}")
        return ''

print(f"Поиск по ключевым словам: {', '.join(KEYWORDS)}")
print("=" * 80)

# Получаем главную страницу со списком статей
response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')

# Статьи лежат в теге <article> с классом tm-articles-list__item
articles = soup.find_all('article', class_='tm-articles-list__item')

print(f"Найдено статей на странице: {len(articles)}")
print("=" * 80)

found_count = 0
full_check_count = 0

for article in articles:
    # Дата лежит в <a class="tm-article-datetime-published">, внутри него <time>
    date_tag = article.find('a', class_='tm-article-datetime-published')
    if date_tag:
        time_tag = date_tag.find('time')
        # Дата в атрибуте datetime, берем только первую часть (год-месяц-день)
        date = time_tag.get('datetime', '').split('T')[0] if time_tag else ''
    else:
        continue

    # Заголовок лежит в <h2 class="tm-title tm-title_h2">
    title_tag = article.find('h2', class_='tm-title')
    if not title_tag:
        continue

    # Ссылка лежит в <a class="tm-title__link"> внутри заголовка
    link_tag = title_tag.find('a', class_='tm-title__link')
    if not link_tag:
        continue

    title = link_tag.get_text(strip=True)
    link = link_tag.get('href')
    # Если ссылка относительная, добавляем домен
    if not link.startswith('http'):
        link = 'https://habr.com' + link

    # ===== ШАГ 1: Проверяем PREVIEW =====
    # Preview текст лежит в <div class="article-formatted-body article-formatted-body_version-2">
    preview_div = article.find('div', class_='article-formatted-body')
    if preview_div:
        preview_text = preview_div.get_text()
    else:
        # Запасной вариант: собираем текст из всех параграфов <p>
        paragraphs = article.find_all('p')
        preview_text = ' '.join([p.get_text() for p in paragraphs])

    # Проверяем ключевые слова в заголовке и preview (приводим к нижнему регистру)
    preview_lower = (title + ' ' + preview_text).lower()
    preview_found = [kw for kw in KEYWORDS if kw.lower() in preview_lower]

    if preview_found:
        found_count += 1
        print(f"{date} – {title} – {link}")
        print(f"  [найдено в preview: {', '.join(preview_found)}]")
        print("-" * 80)
        continue  # Уже нашли, переходим к следующей статье

    # ===== ШАГ 2: Если в preview не нашли — проверяем ПОЛНЫЙ ТЕКСТ =====
    print(f"Проверяем полный текст: {title[:50]}...")
    full_text = get_full_article_text(link)
    time.sleep(0.3)  # Задержка, чтобы не нагружать сервер

    full_lower = full_text.lower()
    full_found = [kw for kw in KEYWORDS if kw.lower() in full_lower]

    if full_found:
        found_count += 1
        full_check_count += 1
        print(f"{date} – {title} – {link}")
        print(f"  [найдено в полном тексте: {', '.join(full_found)}]")
        print("-" * 80)
    else:
        print(f"  [не найдено]")

print("=" * 80)
print(f"Всего найдено статей: {found_count}")
print(f"Из них: найдено в preview: {found_count - full_check_count}")
print(f"       найдено в полном тексте: {full_check_count}")