import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import os
from typing import Optional, Dict
import json
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.prompt import Prompt
from rich.text import Text
from rich import print as rprint
import typer
from rich.table import Table
from datetime import datetime
import ssl
import socket
import time
from config import Config

app = typer.Typer()
console = Console()

VERSION = "1.2"

# Инициализация конфигурации
config_manager = Config()

class ParsLinkAI:
    def __init__(self):
        """
        Инициализация парсера с конфигурацией
        """
        self.api_key = config_manager.get_api_key()
        if not self.api_key:
            raise ValueError("API ключ не найден. Используйте команду 'config' для настройки.")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(config_manager.get_model())

    def analyze_performance(self, soup, response):
        """
        Анализ производительности сайта
        """
        performance = {
            'page_size': len(response.content) / 1024,  # размер в КБ
            'scripts_count': len(soup.find_all('script')),
            'styles_count': len(soup.find_all('link', rel='stylesheet')),
            'images': []
        }
        
        # Анализ изображений
        for img in soup.find_all('img'):
            img_data = {
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'has_alt': bool(img.get('alt')),
            }
            performance['images'].append(img_data)
            
        return performance
        
    def analyze_seo(self, soup, url):
        """
        Расширенный SEO-анализ
        """
        seo_data = {
            'headings': {},
            'links': {'internal': [], 'external': []},
            'meta_tags': {},
            'sitemap': None,
            'robots': None
        }
        
        # Анализ заголовков
        for i in range(1, 7):
            seo_data['headings'][f'h{i}'] = len(soup.find_all(f'h{i}'))
            
        # Анализ ссылок
        domain = url.split('//')[1].split('/')[0]
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                if domain in href or href.startswith('/'):
                    seo_data['links']['internal'].append(href)
                else:
                    seo_data['links']['external'].append(href)
                    
        # Проверка sitemap и robots
        try:
            robots_resp = requests.get(f"{url.rstrip('/')}/robots.txt", timeout=5)
            if robots_resp.status_code == 200:
                seo_data['robots'] = robots_resp.text
                
            sitemap_resp = requests.get(f"{url.rstrip('/')}/sitemap.xml", timeout=5)
            if sitemap_resp.status_code == 200:
                seo_data['sitemap'] = True
        except:
            pass
            
        return seo_data
        
    def analyze_security(self, response):
        """
        Расширенный анализ безопасности
        """
        security = {
            'headers': {
                'HSTS': response.headers.get('Strict-Transport-Security'),
                'CSP': response.headers.get('Content-Security-Policy'),
                'X-Frame-Options': response.headers.get('X-Frame-Options'),
                'X-XSS-Protection': response.headers.get('X-XSS-Protection')
            },
            'cookies': {str(cookie): response.cookies[cookie] for cookie in response.cookies},
        }
        return security

    def parse_website(self, url: str) -> Optional[Dict]:
        """
        Парсинг веб-сайта и анализ через Gemini API
        """
        try:
            start_time = time.time()
            
            # Проверка SSL
            ssl_info = {'valid': False}
            try:
                hostname = url.split('//')[1].split('/')[0]
                context = ssl.create_default_context()
                with socket.create_connection((hostname, 443)) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        ssl_info['valid'] = True
                        ssl_info['issuer'] = dict(x[0] for x in cert['issuer'])
                        ssl_info['expires'] = cert['notAfter']
                        ssl_info['version'] = ssock.version()
                        ssl_info['cipher'] = ssock.cipher()
            except Exception as e:
                ssl_info['error'] = str(e)
            
            load_time = time.time() - start_time
            
            with Progress(
                SpinnerColumn(spinner_name='dots', style='blue'),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=50, complete_style='green', finished_style='bold green'),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                # Получаем содержимое сайта
                fetch_task = progress.add_task("[cyan]Загрузка сайта...", total=100)
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                if not url.startswith('http://') and not url.startswith('https://'):
                    url = 'https://' + url
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                progress.update(fetch_task, advance=50)
                
                # Парсим HTML
                parse_task = progress.add_task("[green]Парсинг содержимого...", total=100)
                soup = BeautifulSoup(response.text, 'html.parser')
                progress.update(parse_task, advance=50)
                
                # Анализ производительности
                perf_task = progress.add_task("[yellow]Анализ производительности...", total=100)
                performance_data = self.analyze_performance(soup, response)
                progress.update(perf_task, advance=100)
                
                # SEO анализ
                seo_task = progress.add_task("[blue]SEO анализ...", total=100)
                seo_data = self.analyze_seo(soup, url)
                progress.update(seo_task, advance=100)
                
                # Анализ безопасности
                security_task = progress.add_task("[red]Анализ безопасности...", total=100)
                security_data = self.analyze_security(response)
                progress.update(security_task, advance=100)
                
                # Основная информация
                title = soup.title.string if soup.title else "Заголовок не найден"
                meta_description = soup.find('meta', {'name': 'description'})
                description = meta_description['content'] if meta_description else "Описание не найдено"
                
                # Получаем текст из основного контента
                main_content = ' '.join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'article'])])
                
                # Формируем промпт для Gemini
                analysis_task = progress.add_task("[magenta]Анализ через Gemini AI...", total=100)
                prompt = f"""
                Проанализируй следующий веб-сайт и предоставь подробную информацию:
                URL: {url}
                Заголовок: {title}
                Описание: {description}
                Основной контент: {main_content[:1000]}...
                
                Производительность:
                - Размер страницы: {performance_data['page_size']:.2f} КБ
                - Количество скриптов: {performance_data['scripts_count']}
                - Количество стилей: {performance_data['styles_count']}
                
                SEO данные:
                - Структура заголовков: {seo_data['headings']}
                - Внутренние ссылки: {len(seo_data['links']['internal'])}
                - Внешние ссылки: {len(seo_data['links']['external'])}
                
                Пожалуйста, предоставь структурированный анализ, включающий:
                1. Основную тему и назначение сайта
                2. Ключевые темы и разделы
                3. Целевую аудиторию
                4. Качество и актуальность контента
                5. Рекомендации по улучшению производительности и SEO
                6. Оценку безопасности
                """
                
                # Получаем анализ от Gemini
                response_ai = self.model.generate_content(prompt)
                progress.update(analysis_task, advance=100)
                
                # Формируем результат
                result = {
                    "url": url,
                    "title": title,
                    "description": description,
                    "analysis": response_ai.text,
                    "timestamp": datetime.now().isoformat(),
                    "model": config_manager.get_model(),
                    "performance": performance_data,
                    "seo": seo_data,
                    "security": security_data,
                    "ssl_info": ssl_info,
                    "load_time": load_time
                }
                
                return result
                
        except Exception as e:
            console.print(f"[red]Ошибка при парсинге сайта {url}: {str(e)}")
            return None

def display_results(result: Dict):
    """Отображение результатов анализа"""
    if not result:
        return

    # Создаем таблицу с основной информацией
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Параметр", style="cyan")
    table.add_column("Значение", style="green")
    
    table.add_row("URL", result['url'])
    table.add_row("Заголовок", result['title'])
    table.add_row("Описание", result['description'])
    table.add_row("Модель", result['model'])
    table.add_row("Время загрузки", f"{result['load_time']:.2f} сек")
    table.add_row("Размер страницы", f"{result['performance']['page_size']:.2f} КБ")
    table.add_row("Скрипты/Стили", f"{result['performance']['scripts_count']}/{result['performance']['styles_count']}")
    table.add_row("SSL", "✅ Valid" if result['ssl_info']['valid'] else "❌ Invalid")

    # Отображаем результаты
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]ParsLinkAI v1.2[/bold cyan] - [green]Результаты анализа[/green]",
        border_style="green"
    ))
    console.print(table)
    
    # SEO информация
    seo_table = Table(show_header=True, header_style="bold blue", title="SEO Анализ")
    seo_table.add_column("Параметр", style="cyan")
    seo_table.add_column("Значение", style="green")
    
    seo_table.add_row("Внутренние ссылки", str(len(result['seo']['links']['internal'])))
    seo_table.add_row("Внешние ссылки", str(len(result['seo']['links']['external'])))
    seo_table.add_row("Sitemap.xml", "✅ Найден" if result['seo']['sitemap'] else "❌ Не найден")
    seo_table.add_row("Robots.txt", "✅ Найден" if result['seo']['robots'] else "❌ Не найден")
    
    console.print("\n")
    console.print(seo_table)
    
    # Безопасность
    security_table = Table(show_header=True, header_style="bold red", title="Анализ безопасности")
    security_table.add_column("Заголовок", style="cyan")
    security_table.add_column("Статус", style="green")
    
    for header, value in result['security']['headers'].items():
        security_table.add_row(header, "✅ Установлен" if value else "❌ Отсутствует")
    
    console.print("\n")
    console.print(security_table)
    
    # Отображаем анализ от Gemini
    console.print("\n[bold cyan]Анализ от Gemini AI:[/bold cyan]")
    console.print(Panel(result['analysis'], border_style="cyan"))

def save_html_report(result: Dict, filename: str):
    ssl_status = '✅ Valid' if result['ssl_info']['valid'] else f'❌ Invalid ({result["ssl_info"].get("error", "Unknown error")})'
    html_content = f"""
    <html>
    <head>
        <title>ParsLinkAI Report - {result["url"]}</title>
    </head>
    <body>
        <h1>Анализ сайта: {result["url"]}</h1>
        <h2>Основные метрики:</h2>
        <p>Время загрузки: {result['load_time']:.2f} сек</p>
        <p>SSL: {ssl_status}</p>
        <h2>SEO-анализ:</h2>
        <p>Ключевые слова: {', '.join(result['keywords']) if result['keywords'] else 'Не найдено'}</p>
        <p>Описание: {result['meta_tags'].get('description', 'Отсутствует')}</p>
    </body>
    </html>
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
    except Exception as e:
        raise ValueError(f"Ошибка сохранения HTML: {str(e)}")

@app.command()
def version():
    """Выводит текущую версию приложения"""
    console.print(f"ParsLinkAI версия: [bold green]{VERSION}[/bold green]")

@app.command()
def config():
    """
    Настройка конфигурации ParsLinkAI
    """
    config_manager.setup()

@app.command()
def analyze(
    url: str = typer.Argument(..., help="URL сайта для анализа"),
    output: str = typer.Option(None, "--output", "-o", help="Путь для сохранения результатов в JSON"),
    html_output: str = typer.Option(None, "--html-output", "-ho", help="Путь для сохранения отчета в HTML")
):
    """
    Анализ веб-сайта с помощью ParsLinkAI
    """
    # Создаем заголовок
    console.print(Panel.fit(
        "[bold cyan]ParsLinkAI[/bold cyan] - [green]Умный анализатор веб-сайтов[/green]",
        border_style="cyan"
    ))
    
    try:
        parser = ParsLinkAI()
        result = parser.parse_website(url)
        
        if result:
            display_results(result)
            
            # Сохраняем результат в файл, если указан путь
            if output:
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                console.print(f"\n[green]Результаты сохранены в файл: {output}[/green]")
            
            # Сохраняем отчет в HTML, если указан путь
            if html_output:
                save_html_report(result, html_output)
                console.print(f"\n[green]Отчет сохранен в файл: {html_output}[/green]")
    except ValueError as e:
        console.print(f"[red]{str(e)}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()