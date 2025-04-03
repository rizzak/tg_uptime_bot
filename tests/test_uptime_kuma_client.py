import pytest
import asyncio
from uptime_kuma_client import UptimeKumaClient

# Тест для проверки подключения и получения списка мониторов
@pytest.mark.asyncio
@pytest.mark.uptime_kuma
async def test_get_monitors():
    """Тестирование получения списка мониторов от реального сервера"""
    async with UptimeKumaClient() as client:
        monitors = await client.get_monitors()
        
        # Проверяем, что список мониторов не пустой
        assert monitors, "Список мониторов не должен быть пустым"
        
        # Проверяем структуру данных монитора
        for monitor in monitors:
            assert "id" in monitor, "У монитора должно быть ID"
            assert "name" in monitor, "У монитора должно быть имя"
            assert "status" in monitor, "У монитора должен быть статус"
            assert "active" in monitor, "У монитора должно быть поле active"

# Тест для получения статуса
@pytest.mark.asyncio
@pytest.mark.uptime_kuma
async def test_get_status_summary():
    """Тестирование получения сводки о статусе мониторов"""
    async with UptimeKumaClient() as client:
        summary = await client.get_status_summary()
        
        # Проверяем, что сводка содержит все необходимые поля
        assert "total" in summary, "В сводке должно быть поле total"
        assert "up" in summary, "В сводке должно быть поле up"
        assert "down" in summary, "В сводке должно быть поле down"
        assert "maintenance" in summary, "В сводке должно быть поле maintenance"
        assert "uptime" in summary, "В сводке должно быть поле uptime"
        
        # Проверяем, что общее количество мониторов соответствует сумме остальных
        assert summary["total"] == summary["up"] + summary["down"] + summary["maintenance"], \
            "Общее количество мониторов должно быть равно сумме up, down и maintenance"

# Тест для проверки получения монитора по ID
@pytest.mark.asyncio
@pytest.mark.uptime_kuma
async def test_get_monitor_by_id():
    """Тестирование получения информации о мониторе по ID"""
    async with UptimeKumaClient() as client:
        # Получаем список мониторов
        monitors = await client.get_monitors()
        
        # Если есть хотя бы один монитор
        if monitors:
            # Берем ID первого монитора
            monitor_id = monitors[0]["id"]
            
            # Получаем монитор по ID
            monitor = await client.get_monitor_by_id(monitor_id)
            
            # Проверяем, что монитор найден
            assert monitor, f"Монитор с ID {monitor_id} не найден"
            assert monitor["id"] == monitor_id, "ID монитора должен совпадать с запрошенным"

# Тест для проверки получения монитора по имени
@pytest.mark.asyncio
@pytest.mark.uptime_kuma
async def test_get_monitor_by_name():
    """Тестирование получения информации о мониторе по имени"""
    async with UptimeKumaClient() as client:
        # Получаем список мониторов
        monitors = await client.get_monitors()
        
        # Если есть хотя бы один монитор
        if monitors:
            # Берем имя первого монитора
            monitor_name = monitors[0]["name"]
            
            # Получаем монитор по имени
            monitor = await client.get_monitor_by_name(monitor_name)
            
            # Проверяем, что монитор найден
            assert monitor, f"Монитор с именем {monitor_name} не найден"
            assert monitor["name"] == monitor_name, "Имя монитора должно совпадать с запрошенным"

# Тест для проверки получения инцидентов
@pytest.mark.asyncio
@pytest.mark.uptime_kuma
async def test_get_incidents():
    """Тестирование получения списка инцидентов"""
    async with UptimeKumaClient() as client:
        incidents = await client.get_incidents()
        
        # Мы не знаем, есть ли инциденты, но проверим структуру, если они есть
        for incident in incidents:
            assert "id" in incident, "У инцидента должно быть ID"
            assert "title" in incident, "У инцидента должен быть заголовок"
            assert "monitor_name" in incident, "У инцидента должно быть имя монитора"
            assert "status" in incident, "У инцидента должен быть статус"
            assert "started_at" in incident, "У инцидента должно быть время начала" 