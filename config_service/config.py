"""
Конфигурация приложения.
"""
import os
from typing import Dict, Any


class Config:
    """Основные настройки приложения."""
    
    # Database settings
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_NAME: str = os.getenv('DB_NAME', 'config_service_db')
    DB_USER: str = os.getenv('DB_USER', 'config_user')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', 'config_password')
    
    # App settings
    APP_HOST: str = os.getenv('APP_HOST', '0.0.0.0')
    APP_PORT: int = int(os.getenv('APP_PORT', '8080'))
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    
    @property
    def database_url(self) -> str:
        """Возвращает URL подключения к базе данных."""
        return f"host={self.DB_HOST} port={self.DB_PORT} dbname={self.DB_NAME} user={self.DB_USER} password={self.DB_PASSWORD}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Возвращает настройки в виде словаря."""
        return {
            'db_host': self.DB_HOST,
            'db_port': self.DB_PORT,
            'db_name': self.DB_NAME,
            'app_host': self.APP_HOST,
            'app_port': self.APP_PORT,
            'debug': self.DEBUG
        }


# Глобальный экземпляр конфигурации
config = Config()
