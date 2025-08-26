"""
Модуль для рендеринга конфигураций через Jinja2.
"""
from jinja2 import Environment, BaseLoader, TemplateError, meta
from typing import Dict, Any, Optional
import json
from twisted.python import log


class ConfigTemplateLoader(BaseLoader):
    """
    Loader для загрузки шаблонов из строк.
    """
    
    def __init__(self, template_source: str):
        self.template_source = template_source
    
    def get_source(self, environment, template):
        """Возвращает исходный код шаблона."""
        return self.template_source, None, lambda: True


class TemplateRenderer:
    """Класс для рендеринга конфигураций через Jinja2."""
    
    def __init__(self):
        # Настраиваем Jinja2 environment
        self.env = Environment(
            loader=None,
            autoescape=False,  # не экранируем HTML, работаем с конфигами
            trim_blocks=True,  # убираем лишние переносы строк
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        # Добавляем полезные фильтры
        self.env.filters['to_json'] = self._to_json_filter
        self.env.filters['from_json'] = self._from_json_filter
    
    @staticmethod
    def _to_json_filter(value: Any) -> str:
        """Фильтр для преобразования в JSON."""
        return json.dumps(value, ensure_ascii=False, indent=2)
    
    @staticmethod  
    def _from_json_filter(value: str) -> Any:
        """Фильтр для парсинга JSON."""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    def render_config_template(self, config_data: Dict[str, Any], 
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Рендерит конфигурацию как Jinja2 шаблон.
        
        Args:
            config_data: Данные конфигурации
            context: Контекст для рендеринга (переменные шаблона)
            
        Returns:
            Отрендеренная конфигурация
        """
        if context is None:
            context = {}
        
        try:
            # Преобразуем конфиг в JSON строку для рендеринга
            config_json = json.dumps(config_data, ensure_ascii=False, indent=2)
            
            # Создаем шаблон из JSON
            template = self.env.from_string(config_json)
            
            # Рендерим с контекстом
            rendered_json = template.render(**context)
            
            # Парсим обратно в Python объект
            rendered_config = json.loads(rendered_json)
            
            log.msg(f"Шаблон отрендерен с контекстом: {list(context.keys())}")
            return rendered_config
            
        except TemplateError as e:
            log.err(f"Jinja2 template error: {e}")
            raise ValueError(f"Template rendering failed: {str(e)}")
            
        except json.JSONDecodeError as e:
            log.err(f"JSON decode error after rendering: {e}")
            raise ValueError(f"Invalid JSON after template rendering: {str(e)}")
        
        except Exception as e:
            log.err(f"Unexpected template rendering error: {e}")
            raise ValueError(f"Template rendering error: {str(e)}")
    
    def render_string_template(self, template_string: str, 
                              context: Dict[str, Any]) -> str:
        """
        Рендерит строковый шаблон.
        
        Args:
            template_string: Строка с шаблоном
            context: Контекст для рендеринга
            
        Returns:
            Отрендеренная строка
        """
        try:
            template = self.env.from_string(template_string)
            return template.render(**context)
        except TemplateError as e:
            log.err(f"String template error: {e}")
            raise ValueError(f"String template rendering failed: {str(e)}")
    
    def extract_template_variables(self, config_data: Dict[str, Any]) -> set:
        """
        Извлекает переменные шаблона из конфигурации.
        
        Args:
            config_data: Данные конфигурации
            
        Returns:
            Множество имен переменных
        """
        try:
            config_json = json.dumps(config_data, ensure_ascii=False)
            ast = self.env.parse(config_json)
            variables = meta.find_undeclared_variables(ast)
            return variables
        except Exception as e:
            log.err(f"Error extracting template variables: {e}")
            return set()
    
    def validate_template_syntax(self, template_string: str) -> tuple[bool, Optional[str]]:
        """
        Проверяет синтаксис Jinja2 шаблона.
        
        Args:
            template_string: Строка шаблона
            
        Returns:
            (is_valid, error_message)
        """
        try:
            self.env.parse(template_string)
            return True, None
        except TemplateError as e:
            return False, str(e)


class ConfigTemplateProcessor:
    """Процессор для работы с шаблонами конфигураций."""
    
    def __init__(self):
        self.renderer = TemplateRenderer()
    
    def process_template_request(self, config_data: Dict[str, Any],
                               template_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Обрабатывает запрос на рендеринг шаблона.
        
        Args:
            config_data: Исходная конфигурация
            template_params: Параметры для шаблона (например, из query string)
            
        Returns:
            Обработанная конфигурация
        """
        if template_params is None:
            template_params = {}
        
        # Добавляем некоторые полезные переменные по умолчанию
        default_context = {
            'user': template_params.get('user', 'anonymous'),
            'env': template_params.get('env', 'development'),
            'timestamp': template_params.get('timestamp', ''),
        }
        
        # Объединяем с пользовательскими параметрами
        context = {**default_context, **template_params}
        
        return self.renderer.render_config_template(config_data, context)
    
    def has_template_syntax(self, config_data: Dict[str, Any]) -> bool:
        """Проверяет содержит ли конфигурация синтаксис шаблонов."""
        try:
            config_str = json.dumps(config_data, ensure_ascii=False)
            # Простая проверка на наличие Jinja2 синтаксиса
            return '{{' in config_str or '{%' in config_str
        except Exception:
            return False


# Глобальный экземпляр процессора шаблонов
template_processor = ConfigTemplateProcessor()
