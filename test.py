from playwright.sync_api import sync_playwright
import time
import csv
from datetime import datetime


class YandexMarketParser:
    def __init__(self):
        self.results = []

    def search(self, query, max_pages=1):
        """
        Поиск товаров на Яндекс Маркете
        query: что ищем
        max_pages: сколько страниц смотреть
        """
        print(f"🔍 Начинаю поиск: {query}")

        with sync_playwright() as p:
            # Запускаем браузер
            browser = p.chromium.launch(headless=False)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()

            try:
                # Переходим на Яндекс Маркет
                print("📱 Открываю Яндекс Маркет...")
                page.goto("https://market.yandex.ru")
                page.wait_for_timeout(3000)

                # Ищем поле поиска
                print("🔎 Ищу поле поиска...")
                search_input = page.locator("input[name='text']").first

                if not search_input.count():
                    print("❌ Не нашел поле поиска!")
                    return []

                # Вводим запрос
                print(f"✏️ Ввожу запрос: {query}")
                search_input.fill(query)
                page.wait_for_timeout(1000)

                # Нажимаем Enter
                search_input.press("Enter")

                # Ждем загрузки результатов
                print("⏳ Жду загрузки результатов...")
                page.wait_for_timeout(5000)

                # Собираем товары с первой страницы
                self.parse_current_page(page)

                # Сохраняем результаты
                self.save_results(query)

                print(f"✅ Найдено товаров: {len(self.results)}")

                # Показываем браузер еще 10 секунд
                time.sleep(10)

            except Exception as e:
                print(f"❌ Ошибка: {e}")

            finally:
                browser.close()

        return self.results

    def parse_current_page(self, page):
        """Парсим текущую страницу с товарами"""
        print("📦 Парсю товары...")

        # Пробуем разные селекторы для товаров
        product_selectors = [
            '[data-autotest-id="product-snippet"]',
            '[class*="snippet"]',
            '[class*="product"]',
            'article'
        ]

        products = []
        for selector in product_selectors:
            products = page.locator(selector).all()
            if len(products) > 0:
                print(f"   Нашел товары по селектору: {selector}")
                break

        if not products:
            print("   Не нашел товары на странице!")
            # Сохраняем HTML для отладки
            html = page.content()
            with open("debug.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("   Сохранил HTML в debug.html")
            return

        print(f"   Обрабатываю {min(len(products), 10)} товаров...")

        # Берем первые 10 товаров
        for product in products[:10]:
            try:
                # Пробуем найти название
                name = "Название не найдено"
                name_selectors = ['[class*="title"]', 'h3', 'a']
                for sel in name_selectors:
                    name_elem = product.locator(sel).first
                    if name_elem.count():
                        name = name_elem.text_content() or name
                        break

                # Пробуем найти цену
                price = "Цена не найдена"
                price_selectors = ['[class*="price"]', '[class*="Price"]']
                for sel in price_selectors:
                    price_elem = product.locator(sel).first
                    if price_elem.count():
                        price = price_elem.text_content() or price
                        break

                # Пробуем найти ссылку
                link = ""
                link_elem = product.locator('a').first
                if link_elem.count():
                    link = link_elem.get_attribute('href') or ""
                    if link and not link.startswith('http'):
                        link = "https://market.yandex.ru" + link

                self.results.append({
                    'name': name.strip(),
                    'price': price.strip(),
                    'url': link,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

                print(f"   ✓ {name[:50]}...")

            except Exception as e:
                print(f"   ✗ Ошибка при парсинге товара: {e}")
                continue

    def save_results(self, query):
        """Сохраняем результаты в CSV файл"""
        if not self.results:
            return

        # Создаем имя файла с датой
        filename = f"results_{query}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'price', 'url', 'timestamp'])
            writer.writeheader()
            writer.writerows(self.results)

        print(f"💾 Результаты сохранены в {filename}")


if __name__ == "__main__":
    print("=" * 50)
    print("ПАРСЕР ЯНДЕКС МАРКЕТА")
    print("=" * 50)

    # Создаем парсер
    parser = YandexMarketParser()

    # Что ищем?
    query = input("Введите запрос (например: тормозные колодки): ")

    if query:
        # Ищем
        results = parser.search(query)

        # Показываем результаты
        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТЫ ПОИСКА:")
        print("=" * 50)
        for i, item in enumerate(results, 1):
            print(f"{i}. {item['name']}")
            print(f"   Цена: {item['price']}")
            print(f"   Ссылка: {item['url']}")
            print()
    else:
        print("Запрос не введен!")