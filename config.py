import json
import os
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

console = Console()

class Config:
    def __init__(self):
        self.config_file = Path.home() / '.parslinkai' / 'config.json'
        self.default_config = {
            'api_key': '',
            'model': 'gemini-pro',
            'available_models': [
                'gemini-pro',
                'gemini-2.0-flash-exp'
            ]
        }
        self.load_config()

    def load_config(self):
        """Загрузка конфигурации из файла"""
        try:
            if not self.config_file.exists():
                self.config_file.parent.mkdir(parents=True, exist_ok=True)
                self.save_config(self.default_config)
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            console.print(f"[red]Ошибка при загрузке конфигурации: {str(e)}[/red]")
            self.config = self.default_config

    def save_config(self, config_data):
        """Сохранение конфигурации в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            self.config = config_data
        except Exception as e:
            console.print(f"[red]Ошибка при сохранении конфигурации: {str(e)}[/red]")

    def setup(self):
        """Настройка конфигурации через интерактивный интерфейс"""
        console.print(Panel.fit(
            "[bold cyan]ParsLinkAI[/bold cyan] - [green]Настройка конфигурации[/green]",
            border_style="cyan"
        ))

        # API ключ
        api_key = Prompt.ask(
            "Введите API ключ Gemini",
            password=True,
            default=self.config.get('api_key', '')
        )

        # Выбор модели
        available_models = self.config.get('available_models', self.default_config['available_models'])
        current_model = self.config.get('model', self.default_config['model'])
        
        console.print("\n[cyan]Доступные модели:[/cyan]")
        for i, model in enumerate(available_models, 1):
            if model == current_model:
                console.print(f"{i}. [green]{model}[/green] (текущая)")
            else:
                console.print(f"{i}. {model}")

        model_index = Prompt.ask(
            "Выберите номер модели",
            default=str(available_models.index(current_model) + 1),
            choices=[str(i) for i in range(1, len(available_models) + 1)]
        )
        
        selected_model = available_models[int(model_index) - 1]

        # Сохраняем новую конфигурацию
        new_config = {
            'api_key': api_key,
            'model': selected_model,
            'available_models': available_models
        }
        
        self.save_config(new_config)
        console.print("[green]Конфигурация успешно сохранена![/green]")

    def get_api_key(self):
        """Получение API ключа"""
        return self.config.get('api_key') or os.getenv("GEMINI_API_KEY")

    def get_model(self):
        """Получение выбранной модели"""
        return self.config.get('model', self.default_config['model'])
