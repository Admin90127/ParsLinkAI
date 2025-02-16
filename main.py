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
from data.config import Config
import ssl
import socket
import time

app = typer.Typer()
console = Console()

# Определяем путь к конфигу в зависимости от режима запуска
if getattr(sys, 'frozen', False):
    # Если приложение запущено как собранный exe
    config_dir = os.path.join(sys._MEIPASS, 'data')
else:
    # В режиме разработки
    config_dir = os.path.dirname(os.path.abspath(__file__))

config_path = os.path.join(config_dir, 'config.json')
config_manager = Config(config_path)

VERSION = "1.1"

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
                # Добавляем схему, если ее нет
                if not url.startswith('http://') and not url.startswith('https://'):
                    url = 'https://' + url
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                progress.update(fetch_task, advance=50)
                
                # Парсим HTML
                parse_task = progress.add_task("[green]Парсинг содержимого...", total=100)
                soup = BeautifulSoup(response.text, 'html.parser')
                progress.update(parse_task, advance=50)
                
                # Собираем основную информацию
                title = soup.title.string if soup.title else "Заголовок не найден"
                meta_description = soup.find('meta', {'name': 'description'})
                description = meta_description['content'] if meta_description else "Описание не найдено"
                progress.update(parse_task, advance=50)
                
                # Получаем текст из основного контента
                content_task = progress.add_task("[yellow]Извлечение контента...", total=100)
                main_content = ' '.join([p.text for p in soup.find_all(['p', 'h1', 'h2', 'h3', 'article'])])
                progress.update(content_task, advance=100)
                
                # Формируем промпт для Gemini
                analysis_task = progress.add_task("[magenta]Анализ через Gemini AI...", total=100)
                prompt = f"""
                Проанализируй следующий веб-сайт и предоставь подробную информацию:
                URL: {url}
                Заголовок: {title}
                Описание: {description}
                Основной контент: {main_content[:1000]}...
                
                Пожалуйста, предоставь структурированный анализ, включающий:
                1. Основную тему и назначение сайта
                2. Ключевые темы и разделы
                3. Целевую аудиторию
                4. Качество и актуальность контента
                5. Рекомендации по улучшению
                """
                
                # Получаем анализ от Gemini
                response = self.model.generate_content(prompt)
                progress.update(analysis_task, advance=100)
                
                # Новая функциональность: Анализ мета-тегов
                meta_tags = {
                    'viewport': soup.find('meta', {'name': 'viewport'}),
                    'og:title': soup.find('meta', property='og:title'),
                    'og:description': soup.find('meta', property='og:description')
                }
                
                # Новая функциональность: Извлечение ключевых слов
                keywords_tag = soup.find('meta', {'name': 'keywords'})
                keywords = keywords_tag['content'].split(',') if keywords_tag else []

                # Формируем результат
                result = {
                    "url": url,
                    "title": title,
                    "description": description,
                    "analysis": response.text,
                    "timestamp": datetime.now().isoformat(),
                    "model": config_manager.get_model(),
                    "meta_tags": {k: v['content'] if v else None for k, v in meta_tags.items()},
                    "keywords": keywords,
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
    table.add_row("SSL", "✅ Valid" if result['ssl_info']['valid'] else "❌ Invalid")

    # Отображаем результаты
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]ParsLinkAI[/bold cyan] - [green]Результаты анализа[/green]",
        border_style="green"
    ))
    console.print(table)
    
    # Отображаем анализ от Gemini
    console.print("\n[bold cyan]Анализ от Gemini AI:[/bold cyan]")
    console.print(Panel(result['analysis'], border_style="cyan"))

    # Новая панель для ключевых слов
    console.print("\n[bold cyan]Ключевые слова:[/bold cyan]")
    console.print(Panel(', '.join(result['keywords']) if result['keywords'] else "Не найдено", 
                       title="SEO Keywords"))

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