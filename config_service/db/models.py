"""
Модели данных для работы с базой.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class ConfigurationModel:
    """Модель конфигурации сервиса."""
    
    def __init__(self, service: str, version: int, payload: Dict[str, Any], 
                 created_at: Optional[datetime] = None, id: Optional[int] = None):
        self.id = id
        self.service = service
        self.version = version
        self.payload = payload
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует в словарь для JSON ответа."""
        return {
            'id': self.id,
            'service': self.service,
            'version': self.version,
            'payload': self.payload,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_db_row(cls, row) -> 'ConfigurationModel':
        """Создает экземпляр из строки БД."""
        return cls(
            id=row[0],
            service=row[1], 
            version=row[2],
            payload=row[3],  # уже декодированный JSONB
            created_at=row[4]
        )


class ConfigHistoryItem:
    """Элемент истории конфигураций."""
    
    def __init__(self, version: int, created_at: datetime):
        self.version = version
        self.created_at = created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует в словарь."""
        return {
            'version': self.version,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod  
    def from_db_row(cls, row) -> 'ConfigHistoryItem':
        """Создает из строки БД."""
        return cls(
            version=row[0],
            created_at=row[1]
        )


class ApiResponse:
    """Стандартный ответ API."""
    
    def __init__(self, data: Any = None, error: Optional[str] = None, 
                 status_code: int = 200):
        self.data = data
        self.error = error
        self.status_code = status_code
    
    def to_json(self) -> str:
        """Преобразует в JSON строку."""
        if self.error:
            response_data = {'error': self.error}
        else:
            response_data = self.data
        
        return json.dumps(response_data, ensure_ascii=False, indent=2)
