"""
Configuration Management Service

REST API сервис для управления конфигурациями распределенных сервисов.
Использует Twisted framework, PostgreSQL, YAML валидацию и Jinja2 шаблонизацию.
"""

__version__ = '1.0.0'
__author__ = 'Configuration Service Team'

from .config import config
from .app import ConfigServiceApplication

__all__ = ['config', 'ConfigServiceApplication']
