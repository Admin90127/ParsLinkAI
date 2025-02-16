# ParsLinkAI - Умный анализатор веб-сайтов

## 📋 Описание
ParsLinkAI - это мощный инструмент для анализа веб-сайтов с использованием искусственного интеллекта (Gemini API). Программа автоматически анализирует содержимое сайта, проверяет SSL-сертификаты, измеряет время загрузки и предоставляет подробный отчет.

## 🌟 Основные функции
- Анализ контента сайта с помощью Gemini AI
- Проверка SSL сертификатов
- Измерение времени загрузки
- Анализ мета-тегов и SEO
- Экспорт отчетов в HTML формат
- Удобный CLI интерфейс

## 🔧 Требования
- Python 3.8+
- Установленные зависимости из requirements.txt
- Ключ API Gemini (получить можно на https://makersuite.google.com/)

## 📥 Установка

1. Клонируйте репозиторий:
```bash
git clone [url-репозитория]
cd parser-sit-ai
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте API ключ:
```bash
python main.py config
```

## 🚀 Использование

### Анализ сайта:
```bash
python main.py analyze https://example.com
```

### Сохранение отчета в HTML:
```bash
python main.py analyze https://example.com --html-output report.html
```

### Проверка версии:
```bash
python main.py version
```

## 🔨 Компиляция

### Для Windows (с помощью Nuitka):
```bash
python -m nuitka --follow-imports --standalone --onefile --include-data-file=config.py=config.py main.py
```

### Для Linux (с помощью Nuitka):
```bash
python -m nuitka --follow-imports --standalone --onefile --include-data-file=config.py=config.py main.py
```

## 📝 Примечания
- При первом запуске необходимо настроить API ключ
- HTML отчеты сохраняются в указанную директорию
- Поддерживается анализ сайтов с SSL сертификатами

## 🔄 Версии
- 1.1 - Добавлена проверка SSL, анализ времени загрузки, экспорт в HTML
- 1.0 - Первый релиз

## 📄 Лицензия
MIT License
