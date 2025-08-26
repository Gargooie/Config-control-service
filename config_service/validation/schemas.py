"""
Схемы валидации для конфигураций.
"""
from schema import Schema, And, Or, Optional, SchemaError
from typing import Dict, Any


# Базовая схема для всех конфигураций
BASE_CONFIG_SCHEMA = Schema({
    'version': And(int, lambda v: v > 0),  # версия должна быть положительным числом
    
    # Database секция обязательна
    Optional('database'): {
        'host': And(str, len),
        'port': And(int, lambda p: 1 <= p <= 65535)
    },
    
    # Features секция опциональна  
    Optional('features'): {
        str: Or(bool, str, int, float)  # любые настройки
    },
    
    # Любые дополнительные поля
    Optional(str): object
})


# Схема для проверки обязательных полей
REQUIRED_FIELDS_SCHEMA = Schema({
    'version': int,
    # Можно добавить другие обязательные поля по необходимости
    Optional(str): object
})


def validate_config_schema(config_data: Dict[str, Any]) -> bool:
    """
    Проверяет конфигурацию на соответствие схеме.
    
    Args:
        config_data: Данные конфигурации для проверки
        
    Returns:
        True если валидная, иначе raises SchemaError
        
    Raises:
        SchemaError: Если конфигурация не соответствует схеме
    """
    try:
        # Сначала проверяем обязательные поля
        REQUIRED_FIELDS_SCHEMA.validate(config_data)
        
        # Потом проверяем полную схему если есть database секция
        if 'database' in config_data:
            BASE_CONFIG_SCHEMA.validate(config_data)
        
        return True
        
    except SchemaError as e:
        # Перебрасываем ошибку с более понятным сообщением
        raise SchemaError(f"Validation error: {str(e)}")


def get_validation_errors(config_data: Dict[str, Any]) -> list:
    """
    Возвращает список ошибок валидации вместо исключения.
    
    Args:
        config_data: Данные для проверки
        
    Returns:
        Список строк с описанием ошибок, пустой если все ок
    """
    errors = []
    
    try:
        validate_config_schema(config_data)
    except SchemaError as e:
        errors.append(str(e))
    
    # Дополнительные проверки
    if 'database' in config_data:
        db_config = config_data['database']
        
        # Проверяем host
        if not db_config.get('host') or not isinstance(db_config.get('host'), str):
            errors.append("database.host must be a non-empty string")
            
        # Проверяем port
        port = db_config.get('port')
        if not isinstance(port, int) or not (1 <= port <= 65535):
            errors.append("database.port must be an integer between 1 and 65535")
    
    return errors


class ConfigValidator:
    """Класс для валидации конфигураций с дополнительной логикой."""
    
    def __init__(self):
        self.schema = BASE_CONFIG_SCHEMA
    
    def validate(self, config_data: Dict[str, Any]) -> tuple[bool, list]:
        """
        Валидирует конфигурацию.
        
        Returns:
            (is_valid, errors_list)
        """
        errors = get_validation_errors(config_data)
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def validate_required_fields(self, config_data: Dict[str, Any]) -> bool:
        """Проверяет только обязательные поля."""
        try:
            REQUIRED_FIELDS_SCHEMA.validate(config_data)
            return True
        except SchemaError:
            return False


# Глобальный валидатор
validator = ConfigValidator()
