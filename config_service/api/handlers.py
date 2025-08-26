"""
Обработчики бизнес-логики для API endpoints.
"""
from twisted.internet import defer
from twisted.python import log
from typing import Dict, Any, Optional, Tuple
import json

from ..db import db_connection, ApiResponse
from ..validation import config_validator
from ..templates import template_processor


class ConfigurationHandler:
    """Обработчик операций с конфигурациями."""
    
    def __init__(self):
        self.db = db_connection
        self.validator = config_validator
        self.template_processor = template_processor
    
    @defer.inlineCallbacks
    def create_configuration(self, service: str, yaml_content: str) -> ApiResponse:
        """
        Создает новую конфигурацию для сервиса.
        
        Args:
            service: Название сервиса
            yaml_content: YAML содержимое конфигурации
            
        Returns:
            ApiResponse с результатом операции
        """
        try:
            # Валидируем YAML
            is_valid, config_data, errors = self.validator.validate_yaml_config(yaml_content)
            
            if not is_valid:
                log.msg(f"Validation failed for service {service}: {errors}")
                response = ApiResponse(
                    error=f"Validation errors: {'; '.join(errors)}",
                    status_code=422
                )
                defer.returnValue(response)
            
            # Сохраняем в базу
            config_model = yield self.db.save_configuration(service, config_data)
            
            # Формируем ответ
            response_data = {
                'service': service,
                'version': config_model.version,
                'status': 'saved'
            }
            
            response = ApiResponse(data=response_data, status_code=201)
            defer.returnValue(response)
            
        except Exception as e:
            log.err(f"Error creating configuration for {service}: {e}")
            response = ApiResponse(
                error=f"Internal server error: {str(e)}",
                status_code=500
            )
            defer.returnValue(response)
    
    @defer.inlineCallbacks  
    def get_configuration(self, service: str, version: Optional[int] = None,
                         use_template: bool = False, 
                         template_params: Optional[Dict[str, Any]] = None) -> ApiResponse:
        """
        Получает конфигурацию сервиса.
        
        Args:
            service: Название сервиса
            version: Версия конфигурации (если None - последняя)
            use_template: Использовать ли Jinja2 рендеринг
            template_params: Параметры для шаблона
            
        Returns:
            ApiResponse с конфигурацией
        """
        try:
            # Получаем конфигурацию из БД
            config_model = yield self.db.get_configuration(service, version)
            
            if config_model is None:
                response = ApiResponse(
                    error=f"Configuration not found for service '{service}'"
                            + (f" version {version}" if version else ""),
                    status_code=404
                )
                defer.returnValue(response)
            
            config_data = config_model.payload
            
            # Применяем шаблонизацию если нужно
            if use_template:
                try:
                    config_data = self.template_processor.process_template_request(
                        config_data, template_params or {}
                    )
                except ValueError as template_error:
                    log.err(f"Template processing error: {template_error}")
                    response = ApiResponse(
                        error=f"Template processing failed: {str(template_error)}",
                        status_code=400
                    )
                    defer.returnValue(response)
            
            response = ApiResponse(data=config_data, status_code=200)
            defer.returnValue(response)
            
        except Exception as e:
            log.err(f"Error getting configuration for {service}: {e}")
            response = ApiResponse(
                error=f"Internal server error: {str(e)}",
                status_code=500
            )
            defer.returnValue(response)
    
    @defer.inlineCallbacks
    def get_configuration_history(self, service: str) -> ApiResponse:
        """
        Получает историю версий конфигурации сервиса.
        
        Args:
            service: Название сервиса
            
        Returns:
            ApiResponse со списком версий
        """
        try:
            history = yield self.db.get_configuration_history(service)
            
            if not history:
                response = ApiResponse(
                    error=f"No configuration history found for service '{service}'",
                    status_code=404
                )
                defer.returnValue(response)
            
            # Преобразуем в список словарей
            history_data = [item.to_dict() for item in history]
            
            response = ApiResponse(data=history_data, status_code=200)
            defer.returnValue(response)
            
        except Exception as e:
            log.err(f"Error getting history for {service}: {e}")
            response = ApiResponse(
                error=f"Internal server error: {str(e)}",
                status_code=500
            )
            defer.returnValue(response)


class HealthHandler:
    """Обработчик для проверки работоспособности."""
    
    def __init__(self):
        self.db = db_connection
    
    @defer.inlineCallbacks
    def check_health(self) -> ApiResponse:
        """Проверяет работоспособность сервиса."""
        try:
            # Проверяем подключение к БД
            yield self.db.dbpool.runQuery("SELECT 1")
            
            health_data = {
                'status': 'healthy',
                'database': 'connected',
                'service': 'config-service'
            }
            
            response = ApiResponse(data=health_data, status_code=200)
            defer.returnValue(response)
            
        except Exception as e:
            log.err(f"Health check failed: {e}")
            health_data = {
                'status': 'unhealthy', 
                'database': 'disconnected',
                'service': 'config-service',
                'error': str(e)
            }
            
            response = ApiResponse(data=health_data, status_code=503)
            defer.returnValue(response)


# Глобальные экземпляры обработчиков
config_handler = ConfigurationHandler()
health_handler = HealthHandler()
