"""
Валидаторы для YAML конфигураций.
"""
import yaml
from yaml.scanner import ScannerError
from yaml.parser import ParserError
from typing import Dict, Any, Tuple, Optional
from twisted.python import log

from .schemas import validator


class YAMLValidator:
    """Валидатор YAML конфигураций."""
    
    @staticmethod
    def parse_yaml(yaml_content: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Парсит YAML строку.
        
        Args:
            yaml_content: YAML строка для парсинга
            
        Returns:
            (success, parsed_data, error_message)
        """
        if not yaml_content or not yaml_content.strip():
            return False, None, "Empty YAML content"
        
        try:
            # Парсим YAML с безопасным loader'ом
            data = yaml.safe_load(yaml_content)
            
            # Проверяем что получился словарь
            if not isinstance(data, dict):
                return False, None, "YAML must represent a dictionary/object"
            
            return True, data, None
            
        except ScannerError as e:
            log.msg(f"YAML Scanner Error: {e}")
            return False, None, f"YAML syntax error: {str(e)}"
            
        except ParserError as e:
            log.msg(f"YAML Parser Error: {e}")  
            return False, None, f"YAML parsing error: {str(e)}"
            
        except Exception as e:
            log.msg(f"Unexpected YAML error: {e}")
            return False, None, f"YAML processing error: {str(e)}"
    
    @staticmethod
    def validate_config(yaml_content: str) -> Tuple[bool, Optional[Dict[str, Any]], list]:
        """
        Полная валидация YAML конфигурации.
        
        Args:
            yaml_content: YAML строка
            
        Returns:
            (is_valid, parsed_data, error_list)
        """
        # Сначала парсим YAML
        success, data, parse_error = YAMLValidator.parse_yaml(yaml_content)
        
        if not success:
            return False, None, [parse_error] if parse_error else ["Unknown parsing error"]
        
        # Валидируем структуру
        is_valid, schema_errors = validator.validate(data)
        
        if not is_valid:
            log.msg(f"Schema validation failed: {schema_errors}")
        
        return is_valid, data, schema_errors
    
    @staticmethod
    def quick_yaml_check(yaml_content: str) -> bool:
        """Быстрая проверка - можно ли распарсить YAML."""
        success, _, _ = YAMLValidator.parse_yaml(yaml_content)
        return success


class ConfigurationValidator:
    """Основной валидатор конфигураций."""
    
    def __init__(self):
        self.yaml_validator = YAMLValidator()
    
    def validate_yaml_config(self, yaml_content: str) -> Tuple[bool, Optional[Dict[str, Any]], list]:
        """
        Основной метод валидации YAML конфигурации.
        
        Returns:
            (is_valid, parsed_config, errors)
        """
        return self.yaml_validator.validate_config(yaml_content)
    
    def check_required_fields(self, config: Dict[str, Any]) -> list:
        """Проверяет обязательные поля."""
        errors = []
        
        # version обязателен
        if 'version' not in config:
            errors.append("Missing required field: version")
        elif not isinstance(config['version'], int) or config['version'] < 1:
            errors.append("Field 'version' must be a positive integer")
        
        # Если есть database секция, проверяем её
        if 'database' in config:
            db = config['database']
            if not isinstance(db, dict):
                errors.append("Field 'database' must be an object")
            else:
                if 'host' not in db:
                    errors.append("Missing required field: database.host")
                if 'port' not in db:
                    errors.append("Missing required field: database.port")
        
        return errors


# Глобальный экземпляр валидатора
config_validator = ConfigurationValidator()
