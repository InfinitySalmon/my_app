import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time

class SiteCrawler:
    def __init__(self, base_url, search_text, max_pages=10000):
        self.base_url = base_url
        self.search_text = search_text
        self.max_pages = max_pages
        self.visited = set()
        self.to_visit = deque([base_url])
        self.found_pages = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Парсим базовый URL для проверки домена
        self.base_domain = urlparse(base_url).netloc

    def is_same_domain(self, url):
        """Проверяет, принадлежит ли URL тому же домену"""
        parsed_url = urlparse(url)
        return parsed_url.netloc == self.base_domain

    def get_links(self, html, current_url):
        """Извлекает все ссылки со страницы"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(current_url, href)
            
            # Фильтруем только ссылки того же домена
            if self.is_same_domain(full_url):
                links.append(full_url)
                
        return links

    def search_text_in_page(self, html, url):
        """Ищет текст в содержимом страницы"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Удаляем скрипты и стили
        for script in soup(["script", "style"]):
            script.decompose()
            
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        clean_text = ' '.join(line for line in lines if line)
        
        if self.search_text.lower() in clean_text.lower():
            return True, clean_text
        return False, clean_text

    def crawl(self):
        """Основной метод обхода сайта"""
        while self.to_visit and len(self.visited) < self.max_pages:
            current_url = self.to_visit.popleft()
            
            if current_url in self.visited:
                continue
                
            try:
                print(f"Посещаем: {current_url}")
                
                response = self.session.get(current_url, timeout=10)
                response.raise_for_status()
                
                # Проверяем кодировку
                if response.encoding.lower() != 'utf-8':
                    response.encoding = 'utf-8'
                
                # Ищем текст
                found, content = self.search_text_in_page(response.text, current_url)
                
                if found:
                    print(f"✓ Найдено на: {current_url}")
                    self.found_pages.append({
                        'url': current_url,
                        'content_preview': content[:200] + '...'
                    })
                    fff=open("sitelist.txt", "a")
                    fff.write(current_url+"\n")
                    fff.close
                
                # Добавляем новые ссылки в очередь
                new_links = self.get_links(response.text, current_url)
                for link in new_links:
                    if link not in self.visited and link not in self.to_visit:
                        self.to_visit.append(link)
                
                self.visited.add(current_url)
                time.sleep(1)  # Пауза между запросами
                
            except Exception as e:
                print(f"Ошибка при обработке {current_url}: {e}")
                self.visited.add(current_url)
                continue
        
        return self.found_pages

    def generate_report(self):
        """Генерирует отчет о найденных страницах"""
        report = f"Отчет поиска: '{self.search_text}'\n"
        report += f"Всего проверено страниц: {len(self.visited)}\n"
        report += f"Найдено совпадений: {len(self.found_pages)}\n\n"
        
        for i, page in enumerate(self.found_pages, 1):
            report += f"{i}. URL: {page['url']}\n"
            report += f"   Предпросмотр: {page['content_preview']}\n\n"
            
        return report

# Использование
if __name__ == "__main__":
    # Настройки
    BASE_URL = "https://classinform.ru/profstandarty.html"
    SEARCH_TEXT = "2.27.00"
    
    # Создаем краулер
    crawler = SiteCrawler(BASE_URL, SEARCH_TEXT, max_pages=10000)
    
    # Запускаем обход
    print("Начинаем обход сайта...")
    found_pages = crawler.crawl()
    
    # Выводим отчет
    report = crawler.generate_report()
    print(report)
    
    # Сохраняем в файл
    with open("search_report.txt", "w", encoding="utf-8") as f:
        f.write(report)