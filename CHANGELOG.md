# Журнал изменений (Changelog)

Все заметные изменения в проекте ParsLinkAI будут документироваться в этом файле.

## [1.2.0] - 2025-02-17

### Добавлено
- Анализ производительности сайта
  - Измерение размера страницы
  - Подсчет количества скриптов и стилей
  - Анализ изображений и их атрибутов
- Расширенный SEO-анализ
  - Анализ структуры заголовков (h1-h6)
  - Подсчет внутренних и внешних ссылок
  - Проверка наличия sitemap.xml и robots.txt
- Улучшенный анализ безопасности
  - Проверка заголовков безопасности (HSTS, CSP, X-Frame-Options, X-XSS-Protection)
  - Расширенная информация о SSL (версия, шифр)
  - Анализ cookies
- Улучшенный вывод результатов
  - Отдельные таблицы для SEO и безопасности
  - Улучшенное форматирование с использованием цветов
  - Статусы с эмодзи (✅/❌)

### Изменено
- Обновлен формат вывода результатов анализа
- Расширен промпт для Gemini AI с включением данных о производительности и SEO
- Улучшена обработка SSL/TLS информации

## [1.1.0] - 2025-02-16

### 🚀 Новые функции
- Добавлена проверка SSL сертификатов
- Реализовано измерение времени загрузки сайта
- Добавлен экспорт отчетов в HTML формат
- Улучшен анализ мета-тегов
- Добавлено извлечение ключевых слов

### 🔧 Улучшения
- Обновлен интерфейс командной строки
- Улучшена обработка ошибок
- Добавлены цветные индикаторы прогресса
- Оптимизирована работа с конфигурационным файлом

### 🐛 Исправления
- Исправлена обработка URL без схемы
- Улучшена обработка кодировки
- Исправлена работа с SSL сертификатами
- Оптимизирована работа с памятью

### 📦 Зависимости
- Обновлена версия rich до 13.7.1
- Добавлена поддержка новых версий Python
- Оптимизированы зависимости проекта

## [1.0.0] - 2025-02-15

### 🎉 Первый релиз
- Базовый анализ веб-сайтов
- Интеграция с Gemini AI
- Базовый CLI интерфейс
- Система конфигурации
- Поддержка сохранения результатов

### 🔧 Особенности первой версии
- Анализ контента сайта
- Базовая обработка ошибок
- Конфигурация через файл config.json
- Поддержка командной строки
- Базовый вывод результатов

## Планируемые улучшения

### Версия 1.3.0 [Планируется]
- [ ] Графический интерфейс
- [ ] Система плагинов
- [ ] Расширенная аналитика
- [ ] API для интеграции
- [ ] Поддержка прокси
