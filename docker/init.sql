-- Создание таблицы конфигураций
CREATE TABLE IF NOT EXISTS configurations (
    id SERIAL PRIMARY KEY,
    service TEXT NOT NULL,
    version INTEGER NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(service, version)
);

-- Создаем индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_configurations_service ON configurations(service);
CREATE INDEX IF NOT EXISTS idx_configurations_service_version ON configurations(service, version);
CREATE INDEX IF NOT EXISTS idx_configurations_created_at ON configurations(created_at);

-- Вставляем тестовые данные
INSERT INTO configurations (service, version, payload) VALUES 
('test_service', 1, '{"version": 1, "database": {"host": "localhost", "port": 5432}, "features": {"enable_auth": true, "enable_cache": false}}'),
('another_service', 1, '{"version": 1, "api": {"timeout": 30}, "logging": {"level": "INFO"}}')
ON CONFLICT (service, version) DO NOTHING;
