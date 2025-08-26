"""
Модуль для асинхронной работы с PostgreSQL через adbapi.
"""
from twisted.enterprise import adbapi
from twisted.internet import defer
from twisted.python import log
from typing import List, Optional, Dict, Any
import json

from .models import ConfigurationModel, ConfigHistoryItem
from ..config import config


class DatabaseConnection:
    """Класс для работы с базой данных."""
    
    def __init__(self):
        self.dbpool = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Настраивает пул соединений с БД."""
        try:
            # Создаем пул соединений через adbapi
            self.dbpool = adbapi.ConnectionPool(
                'psycopg2',
                host=config.DB_HOST,
                port=config.DB_PORT,
                database=config.DB_NAME,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                cp_min=1,  # минимум соединений
                cp_max=10,  # максимум соединений
                cp_reconnect=True,  # автоматическое переподключение
                cp_good_sql="SELECT 1"  # SQL для проверки соединения
            )
            log.msg("Database connection pool создан")
            
        except Exception as e:
            log.err(f"Ошибка при подключении к базе: {e}")
            raise
    
    @defer.inlineCallbacks
    def save_configuration(self, service: str, payload: Dict[str, Any]) -> ConfigurationModel:
        """
        Сохраняет новую конфигурацию в базу.
        Автоматически назначает версию если не указана.
        """
        try:
            # Извлекаем версию из payload или назначаем автоматически
            version = payload.get('version')
            
            if version is None:
                # Получаем максимальную версию для данного сервиса
                max_version = yield self.dbpool.runQuery(
                    "SELECT COALESCE(MAX(version), 0) FROM configurations WHERE service = %s",
                    (service,)
                )
                version = max_version[0][0] + 1
                payload['version'] = version
            
            # Сохраняем конфигурацию
            result = yield self.dbpool.runQuery(
                """INSERT INTO configurations (service, version, payload) 
                   VALUES (%s, %s, %s) RETURNING id, created_at""",
                (service, version, json.dumps(payload))
            )
            
            row = result[0]
            config_model = ConfigurationModel(
                id=row[0],
                service=service,
                version=version,
                payload=payload,
                created_at=row[1]
            )
            
            log.msg(f"Сохранена конфигурация для {service}, version {version}")
            defer.returnValue(config_model)
            
        except Exception as e:
            log.err(f"Ошибка при сохранении конфигурации: {e}")
            raise
    
    @defer.inlineCallbacks
    def get_configuration(self, service: str, version: Optional[int] = None) -> Optional[ConfigurationModel]:
        """
        Получает конфигурацию сервиса.
        Если версия не указана, возвращает последнюю.
        """
        try:
            if version is None:
                # Получаем последнюю версию
                result = yield self.dbpool.runQuery(
                    """SELECT id, service, version, payload, created_at 
                       FROM configurations 
                       WHERE service = %s 
                       ORDER BY version DESC LIMIT 1""",
                    (service,)
                )
            else:
                # Получаем конкретную версию
                result = yield self.dbpool.runQuery(
                    """SELECT id, service, version, payload, created_at 
                       FROM configurations 
                       WHERE service = %s AND version = %s""",
                    (service, version)
                )
            
            if not result:
                defer.returnValue(None)
            
            row = result[0]
            # Преобразуем JSON строку обратно в dict если нужно
            payload = row[3] if isinstance(row[3], dict) else json.loads(row[3])
            
            config_model = ConfigurationModel(
                id=row[0],
                service=row[1],
                version=row[2], 
                payload=payload,
                created_at=row[4]
            )
            
            defer.returnValue(config_model)
            
        except Exception as e:
            log.err(f"Ошибка при получении конфигурации: {e}")
            raise
    
    @defer.inlineCallbacks
    def get_configuration_history(self, service: str) -> List[ConfigHistoryItem]:
        """Получает историю версий для сервиса."""
        try:
            result = yield self.dbpool.runQuery(
                """SELECT version, created_at 
                   FROM configurations 
                   WHERE service = %s 
                   ORDER BY version DESC""",
                (service,)
            )
            
            history = [ConfigHistoryItem.from_db_row(row) for row in result]
            defer.returnValue(history)
            
        except Exception as e:
            log.err(f"Ошибка при получении истории: {e}")
            raise
    
    def close(self):
        """Закрывает пул соединений."""
        if self.dbpool:
            self.dbpool.close()
            log.msg("Database connection pool закрыт")


# Глобальный экземпляр подключения к БД
db_connection = DatabaseConnection()
