"""
Главное приложение Configuration Management Service.
"""
import sys
import os
from twisted.web import server
from twisted.internet import reactor, endpoints
from twisted.python import log
from twisted.application import service, internet

# Добавляем текущую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_service.api import RootResource
from config_service.config import config
from config_service.db import db_connection


class ConfigServiceApplication:
    """Основное приложение сервиса."""
    
    def __init__(self):
        self.config = config
        self.site = None
        self.db = db_connection
    
    def setup_logging(self):
        """Настраивает логирование."""
        if self.config.DEBUG:
            log.startLogging(sys.stdout)
        else:
            # В продакшене можно настроить логирование в файл
            log.startLogging(sys.stdout)
    
    def create_site(self):
        """Создает Twisted Web Site."""
        root_resource = RootResource()
        self.site = server.Site(root_resource)
        
        # Настройки сайта
        self.site.displayTracebacks = self.config.DEBUG
        
        log.msg("Twisted Web Site создан")
        return self.site
    
    def setup_database(self):
        """Настраивает подключение к базе данных."""
        try:
            # Проверяем что БД доступна при старте
            # (в реальном приложении можно добавить retry logic)
            log.msg(f"Подключение к базе данных: {self.config.DB_HOST}:{self.config.DB_PORT}")
            log.msg(f"База данных: {self.config.DB_NAME}")
            
            # db_connection уже создан при импорте
            log.msg("Database connection готово")
            
        except Exception as e:
            log.err(f"Ошибка настройки БД: {e}")
            raise
    
    def run_server(self):
        """Запускает сервер."""
        try:
            self.setup_logging()
            self.setup_database()
            self.create_site()
            
            # Создаем endpoint для HTTP сервера
            endpoint = endpoints.TCP4ServerEndpoint(
                reactor, 
                self.config.APP_PORT, 
                interface=self.config.APP_HOST
            )
            
            # Привязываем сайт к endpoint
            endpoint.listen(self.site)
            
            log.msg(f"🚀 Configuration Service запущен на http://{self.config.APP_HOST}:{self.config.APP_PORT}")
            log.msg(f"⚙️  Режим отладки: {'включен' if self.config.DEBUG else 'выключен'}")
            log.msg("📚 Доступные endpoints:")
            log.msg("   POST   /config/{service}")
            log.msg("   GET    /config/{service}[?version=N][&template=1]")
            log.msg("   GET    /config/{service}/history")
            log.msg("   GET    /health")
            
            # Запускаем reactor
            reactor.run()
            
        except Exception as e:
            log.err(f"Ошибка запуска сервера: {e}")
            sys.exit(1)
        finally:
            # Закрываем соединения с БД при завершении
            self.cleanup()
    
    def cleanup(self):
        """Очистка ресурсов при завершении."""
        try:
            if self.db:
                self.db.close()
                log.msg("Database connections закрыты")
        except Exception as e:
            log.err(f"Ошибка при очистке: {e}")


def create_application():
    """
    Создает Twisted Application для twistd.
    Можно использовать для запуска через twistd -y app.py
    """
    from twisted.application import service
    
    app = service.Application("config-service")
    
    # Настраиваем сервис
    config_app = ConfigServiceApplication()
    config_app.setup_logging()
    config_app.setup_database()
    site = config_app.create_site()
    
    # Создаем HTTP сервис
    web_service = internet.TCPServer(config.APP_PORT, site, interface=config.APP_HOST)
    web_service.setServiceParent(app)
    
    return app


def main():
    """Основная функция запуска."""
    log.msg("Запуск Configuration Management Service...")
    
    try:
        app = ConfigServiceApplication()
        app.run_server()
    except KeyboardInterrupt:
        log.msg("Получен сигнал прерывания, завершаем...")
    except Exception as e:
        log.err(f"Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()


# Для twistd
application = create_application()
