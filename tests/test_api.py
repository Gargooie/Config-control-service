"""
Тесты для API endpoints.
"""
import pytest
from twisted.trial import unittest
from twisted.web.test.requesthelper import DummyRequest
from twisted.internet import defer

from config_service.api.resources import RootResource, ConfigResource
from config_service.api.handlers import config_handler


class TestConfigAPI(unittest.TestCase):
    """Тесты для API конфигураций."""
    
    def setUp(self):
        """Настройка перед каждым тестом."""
        self.root = RootResource()
    
    def test_root_resource_get(self):
        """Тест главной страницы API."""
        request = DummyRequest([b''])
        request.method = b'GET'
        
        result = self.root.render_GET(request)
        
        # Проверяем что возвращается NOT_DONE_YET (асинхронный ответ)
        from twisted.web.server import NOT_DONE_YET
        self.assertEqual(result, NOT_DONE_YET)
    
    def test_config_resource_creation(self):
        """Тест создания ресурса конфигурации."""
        service_name = "test_service"
        config_resource = ConfigResource(service_name)
        
        self.assertEqual(config_resource.service_name, service_name)
        self.assertTrue(config_resource.isLeaf)
    
    @defer.inlineCallbacks
    def test_yaml_validation(self):
        """Тест валидации YAML."""
        from config_service.validation import config_validator
        
        valid_yaml = """
version: 1
database:
  host: "localhost"
  port: 5432
features:
  enable_auth: true
"""
        
        is_valid, data, errors = config_validator.validate_yaml_config(valid_yaml)
        self.assertTrue(is_valid)
        self.assertIsNotNone(data)
        self.assertEqual(len(errors), 0)
        
        # Тест невалидного YAML
        invalid_yaml = "invalid: yaml: content:"
        is_valid, data, errors = config_validator.validate_yaml_config(invalid_yaml)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


if __name__ == '__main__':
    import sys
    from twisted.trial.runner import TrialRunner
    
    runner = TrialRunner()
    suite = unittest.TestLoader().loadTestsFromTestCase(TestConfigAPI)
    runner.run(suite)
