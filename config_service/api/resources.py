"""
Twisted Web Resources для REST API.
"""
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.internet import defer
from twisted.python import log
import json
import urllib.parse
from typing import Dict, Any, Optional

from .handlers import config_handler, health_handler


class BaseResource(Resource):
    """Базовый класс для всех ресурсов."""
    
    def __init__(self):
        super().__init__()
        self.isLeaf = False
    
    def _get_request_body(self, request) -> str:
        """Получает тело запроса как строку."""
        try:
            body = request.content.read()
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            return body
        except Exception as e:
            log.err(f"Error reading request body: {e}")
            return ""
    
    def _parse_query_params(self, request) -> Dict[str, Any]:
        """Парсит параметры запроса."""
        params = {}
        
        for key, values in request.args.items():
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            
            if len(values) == 1:
                value = values[0]
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                params[key] = value
            else:
                # Множественные значения
                decoded_values = []
                for v in values:
                    if isinstance(v, bytes):
                        v = v.decode('utf-8')
                    decoded_values.append(v)
                params[key] = decoded_values
        
        return params
    
    def _send_response(self, request, response):
        """Отправляет ответ клиенту."""
        try:
            request.setResponseCode(response.status_code)
            request.setHeader(b'Content-Type', b'application/json; charset=utf-8')
            request.setHeader(b'Access-Control-Allow-Origin', b'*')
            request.setHeader(b'Access-Control-Allow-Methods', b'GET, POST, PUT, DELETE, OPTIONS')
            request.setHeader(b'Access-Control-Allow-Headers', b'Content-Type')
            
            response_json = response.to_json()
            request.write(response_json.encode('utf-8'))
            request.finish()
            
        except Exception as e:
            log.err(f"Error sending response: {e}")
            request.setResponseCode(500)
            request.finish()
    
    def _handle_error(self, request, error_msg: str, status_code: int = 500):
        """Обрабатывает ошибки."""
        from ..db.models import ApiResponse
        response = ApiResponse(error=error_msg, status_code=status_code)
        self._send_response(request, response)


class ConfigResource(BaseResource):
    """Ресурс для работы с конфигурациями /config/{service}."""
    
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
        self.isLeaf = True  # это конечный ресурс
    
    def render_GET(self, request):
        """Обрабатывает GET запросы - получение конфигурации."""
        params = self._parse_query_params(request)
        
        # Извлекаем параметры
        version = params.get('version')
        if version:
            try:
                version = int(version)
            except (ValueError, TypeError):
                self._handle_error(request, "Invalid version parameter", 400)
                return NOT_DONE_YET
        
        use_template = params.get('template') == '1'
        
        # Подготавливаем параметры шаблона
        template_params = {}
        for key, value in params.items():
            if key not in ['version', 'template']:
                template_params[key] = value
        
        # Асинхронно получаем конфигурацию
        d = config_handler.get_configuration(
            self.service_name, 
            version=version,
            use_template=use_template,
            template_params=template_params
        )
        d.addCallback(lambda response: self._send_response(request, response))
        d.addErrback(lambda failure: self._handle_error(request, str(failure.value)))
        
        return NOT_DONE_YET
    
    def render_POST(self, request):
        """Обрабатывает POST запросы - создание конфигурации."""
        yaml_content = self._get_request_body(request)
        
        if not yaml_content.strip():
            self._handle_error(request, "Empty request body", 400)
            return NOT_DONE_YET
        
        # Асинхронно создаем конфигурацию
        d = config_handler.create_configuration(self.service_name, yaml_content)
        d.addCallback(lambda response: self._send_response(request, response))
        d.addErrback(lambda failure: self._handle_error(request, str(failure.value)))
        
        return NOT_DONE_YET


class ConfigHistoryResource(BaseResource):
    """Ресурс для истории конфигураций /config/{service}/history."""
    
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
        self.isLeaf = True
    
    def render_GET(self, request):
        """Получение истории версий."""
        d = config_handler.get_configuration_history(self.service_name)
        d.addCallback(lambda response: self._send_response(request, response))
        d.addErrback(lambda failure: self._handle_error(request, str(failure.value)))
        
        return NOT_DONE_YET


class ServiceResource(BaseResource):
    """Ресурс для конкретного сервиса /config/{service}."""
    
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name
        
        # Добавляем дочерние ресурсы
        self.putChild(b'history', ConfigHistoryResource(service_name))
    
    def getChild(self, name, request):
        """Обрабатывает дочерние пути."""
        if name == b'':
            # Если путь заканчивается на /config/{service}
            return ConfigResource(self.service_name)
        elif name == b'history':
            return ConfigHistoryResource(self.service_name)
        else:
            return BaseResource()  # 404


class ConfigRootResource(BaseResource):
    """Корневой ресурс для /config."""
    
    def getChild(self, name, request):
        """Динамически создает ресурсы для сервисов."""
        if name == b'':
            return self
        
        # Декодируем имя сервиса
        service_name = name.decode('utf-8') if isinstance(name, bytes) else name
        return ServiceResource(service_name)
    
    def render_GET(self, request):
        """Возвращает список доступных эндпоинтов."""
        from ..db.models import ApiResponse
        
        api_info = {
            'service': 'Configuration Management Service',
            'endpoints': {
                'POST /config/{service}': 'Create new configuration',
                'GET /config/{service}': 'Get configuration (latest or specific version)',
                'GET /config/{service}/history': 'Get configuration history'
            },
            'parameters': {
                'version': 'Specific version number (optional)',
                'template': 'Set to 1 to enable Jinja2 rendering (optional)'
            }
        }
        
        response = ApiResponse(data=api_info)
        self._send_response(request, response)
        return NOT_DONE_YET


class HealthResource(BaseResource):
    """Ресурс для проверки здоровья сервиса /health."""
    
    def __init__(self):
        super().__init__()
        self.isLeaf = True
    
    def render_GET(self, request):
        """Health check."""
        d = health_handler.check_health()
        d.addCallback(lambda response: self._send_response(request, response))
        d.addErrback(lambda failure: self._handle_error(request, str(failure.value)))
        
        return NOT_DONE_YET


class RootResource(BaseResource):
    """Корневой ресурс приложения."""
    
    def __init__(self):
        super().__init__()
        
        # Регистрируем основные пути
        self.putChild(b'config', ConfigRootResource())
        self.putChild(b'health', HealthResource())
    
    def render_GET(self, request):
        """Главная страница API."""
        from ..db.models import ApiResponse
        
        welcome_data = {
            'message': 'Configuration Management Service API',
            'version': '1.0.0',
            'endpoints': [
                '/config/{service}',
                '/health'
            ]
        }
        
        response = ApiResponse(data=welcome_data)
        self._send_response(request, response)
        return NOT_DONE_YET
