import os
from typing import Optional, List, Dict, Any
from uptime_kuma_api import UptimeKumaApi, MonitorType
from dotenv import load_dotenv

class UptimeKumaClient:
    def __init__(self):
        load_dotenv()
        self.url = os.getenv("UPTIME_KUMA_URL")
        self.username = os.getenv("UPTIME_KUMA_USERNAME")
        self.password = os.getenv("UPTIME_KUMA_PASSWORD")
        self.api_key = os.getenv("UPTIME_KUMA_API_KEY")
        self.api: Optional[UptimeKumaApi] = None

    async def connect(self) -> None:
        """Установка соединения с Uptime Kuma"""
        try:
            self.api = UptimeKumaApi(self.url)
            self.api.login(self.username, self.password)
        except Exception as e:
            raise ConnectionError(f"Ошибка подключения к Uptime Kuma: {str(e)}")

    async def disconnect(self) -> None:
        """Закрытие соединения с Uptime Kuma"""
        if self.api:
            try:
                # Попробуем вызвать без await, т.к. это не корутина
                self.api.disconnect()
            except Exception as e:
                raise ConnectionError(f"Ошибка при отключении от Uptime Kuma: {str(e)}")
            self.api = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        
    async def get_monitors(self) -> List[Dict[str, Any]]:
        """Получение списка мониторов с их статусами
        
        Returns:
            List[Dict[str, Any]]: Список мониторов с полями:
                - id: ID монитора
                - name: Имя монитора
                - status: Статус (1 - активен, 0 - неактивен)
                - active: Активен ли монитор
                - url: URL монитора
                - type: Тип монитора
                - maintenance: В режиме обслуживания ли монитор
        """
        if not self.api:
            await self.connect()
            
        try:
            # Вызываем без await, т.к. это не корутина
            monitors_data = self.api.get_monitors()
            
            # Преобразуем в удобный формат
            result = []
            for monitor in monitors_data:
                # Определяем статус (1 - вверх, 0 - вниз)
                status = 1
                if not monitor.get("active", True) or monitor.get("status") == 0:
                    status = 0
                if monitor.get("maintenance", False):
                    status = 0
                    
                result.append({
                    "id": str(monitor.get("id")),
                    "name": monitor.get("name", "Unknown"),
                    "status": status,
                    "active": monitor.get("active", True),
                    "url": monitor.get("url", ""),
                    "type": monitor.get("type", "unknown"),
                    "maintenance": monitor.get("maintenance", False)
                })
                
            return result
        except Exception as e:
            raise ConnectionError(f"Ошибка при получении списка мониторов: {str(e)}")
    
    async def get_monitor_by_id(self, monitor_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о конкретном мониторе по его ID
        
        Args:
            monitor_id: ID монитора
            
        Returns:
            Optional[Dict[str, Any]]: Информация о мониторе или None, если монитор не найден
        """
        monitors = await self.get_monitors()
        
        for monitor in monitors:
            if str(monitor.get("id")) == str(monitor_id):
                return monitor
                
        return None
    
    async def get_monitor_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Получение информации о конкретном мониторе по его имени
        
        Args:
            name: Имя монитора
            
        Returns:
            Optional[Dict[str, Any]]: Информация о мониторе или None, если монитор не найден
        """
        monitors = await self.get_monitors()
        
        for monitor in monitors:
            if monitor.get("name") == name:
                return monitor
                
        return None
    
    async def get_incidents(self) -> List[Dict[str, Any]]:
        """Получение списка инцидентов
        
        Returns:
            List[Dict[str, Any]]: Список инцидентов
        """
        if not self.api:
            await self.connect()
            
        try:
            # Вызываем без await, т.к. это не корутина
            incidents_data = self.api.get_incidents()
            
            # Преобразуем в удобный формат
            result = []
            for incident in incidents_data:
                result.append({
                    "id": incident.get("id", ""),
                    "title": incident.get("title", "Неизвестный инцидент"),
                    "monitor_name": incident.get("monitor_name", ""),
                    "status": incident.get("status", "unknown"),
                    "started_at": incident.get("started_at", ""),
                    "resolved_at": incident.get("resolved_at", "")
                })
                
            return result
        except Exception as e:
            # Если не удалось получить инциденты напрямую, создаем их из мониторов
            return await self._create_incidents_from_monitors()
    
    async def _create_incidents_from_monitors(self) -> List[Dict[str, Any]]:
        """Создание списка инцидентов на основе неработающих мониторов
        
        Returns:
            List[Dict[str, Any]]: Список инцидентов
        """
        monitors = await self.get_monitors()
        
        incidents = []
        for monitor in monitors:
            if monitor.get("status") == 0 and monitor.get("active", True):
                incidents.append({
                    "id": monitor.get("id"),
                    "title": f"Проблема с {monitor.get('name')}",
                    "monitor_name": monitor.get("name"),
                    "status": "down",
                    "started_at": "Недавно",
                    "resolved_at": ""
                })
                
        return incidents
    
    async def get_status_summary(self) -> Dict[str, Any]:
        """Получение сводки о статусе всех мониторов
        
        Returns:
            Dict[str, Any]: Сводка о статусе
                - total: Общее количество мониторов
                - up: Количество работающих мониторов
                - down: Количество неработающих мониторов
                - maintenance: Количество мониторов на обслуживании
                - uptime: Процент работающих мониторов
        """
        monitors = await self.get_monitors()
        
        total = len(monitors)
        up = sum(1 for m in monitors if m.get("status") == 1 and m.get("active", True))
        down = sum(1 for m in monitors if m.get("status") == 0 and m.get("active", True) and not m.get("maintenance", False))
        maintenance = sum(1 for m in monitors if m.get("maintenance", False) and m.get("active", True))
        
        # Расчет процента работающих мониторов
        active_monitors = sum(1 for m in monitors if m.get("active", True))
        uptime = (up / active_monitors * 100) if active_monitors > 0 else 100
        
        return {
            "total": total,
            "up": up,
            "down": down,
            "maintenance": maintenance,
            "uptime": round(uptime, 2)
        }
