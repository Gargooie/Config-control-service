"""
Тесты для модуля валидации.
"""
import unittest
from config_service.validation import config_validator, YAMLValidator


class TestYAMLValidation(unittest.TestCase):
    """Тесты валидации YAML."""
    
    def test_valid_yaml_parsing(self):
        """Тест парсинга корректного YAML."""
        yaml_content = """
version: 1
database:
  host: "localhost"
  port: 5432
features:
  enable_auth: true
  enable_cache: false
"""
        
        success, data, error = YAMLValidator.parse_yaml(yaml_content)
        
        self.assertTrue(success)
        self.assertIsNotNone(data)
        self.assertIsNone(error)
        self.assertEqual(data['version'], 1)
        self.assertEqual(data['database']['host'], 'localhost')
    
    def test_invalid_yaml_parsing(self):
        """Тест парсинга некорректного YAML."""
        invalid_yaml = """
version: 1
database:
  host: "localhost
  port: 5432  # незакрытая кавычка выше
"""
        
        success, data, error = YAMLValidator.parse_yaml(invalid_yaml)
        
        self.assertFalse(success)
        self.assertIsNone(data)
        self.assertIsNotNone(error)
    
    def test_empty_yaml(self):
        """Тест пустого YAML."""
        success, data, error = YAMLValidator.parse_yaml("")
        
        self.assertFalse(success)
        self.assertIsNone(data)
        self.assertIsNotNone(error)
    
    def test_schema_validation(self):
        """Тест валидации схемы."""
        # Корректная конфигурация
        valid_config = {
            'version': 1,
            'database': {
                'host': 'localhost',
                'port': 5432
            },
            'features': {
                'enable_auth': True
            }
        }
        
        is_valid, errors = config_validator.validator.validate(valid_config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Некорректная конфигурация (нет version)
        invalid_config = {
            'database': {
                'host': 'localhost',
                'port': 5432
            }
        }
        
        is_valid, errors = config_validator.validator.validate(invalid_config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestTemplateValidation(unittest.TestCase):
    """Тесты валидации шаблонов."""
    
    def test_template_syntax_detection(self):
        """Тест обнаружения синтаксиса шаблонов."""
        from config_service.templates import template_processor
        
        # Конфиг с шаблонами
        config_with_template = {
            'version': 1,
            'welcome_message': 'Hello {{ user }}!',
            'database': {
                'host': '{{ db_host }}',
                'port': 5432
            }
        }
        
        has_templates = template_processor.has_template_syntax(config_with_template)
        self.assertTrue(has_templates)
        
        # Конфиг без шаблонов
        config_without_template = {
            'version': 1,
            'database': {
                'host': 'localhost',
                'port': 5432
            }
        }
        
        has_templates = template_processor.has_template_syntax(config_without_template)
        self.assertFalse(has_templates)


if __name__ == '__main__':
    unittest.main()
