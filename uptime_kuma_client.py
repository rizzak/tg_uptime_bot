import os
import logging
from typing import Optional, List, Dict, Any
from uptime_kuma_api import UptimeKumaApi, MonitorType
from dotenv import load_dotenv
import asyncio

# Настройка логгера
logger = logging.getLogger(__name__)

class UptimeKumaClient:
    def __init__(self):
        load_dotenv()
        self.url = os.getenv("UPTIME_KUMA_URL")
        self.username = os.getenv("UPTIME_KUMA_USERNAME")
        self.password = os.getenv("UPTIME_KUMA_PASSWORD")
        self.api: Optional[UptimeKumaApi] = None
        logger.info("UptimeKumaClient инициализирован")

    async def connect(self) -> None:
        """Установка соединения с Uptime Kuma"""
        try:
            logger.info(f"Подключение к Uptime Kuma: {self.url}")
            self.api = UptimeKumaApi(self.url)
            await asyncio.to_thread(self.api.login, self.username, self.password)
            logger.info("Успешное подключение к Uptime Kuma")
        except Exception as e:
            logger.error(f"Ошибка подключения к Uptime Kuma: {str(e)}")
            self.api = None
            raise ConnectionError(f"Ошибка подключения к Uptime Kuma: {str(e)}")

    async def disconnect(self) -> None:
        """Закрытие соединения с Uptime Kuma"""
        if self.api:
            api_to_disconnect = self.api
            self.api = None
            try:
                logger.info("Отключение от Uptime Kuma")
                await asyncio.to_thread(api_to_disconnect.disconnect)
                logger.info("Успешное отключение от Uptime Kuma")
            except Exception as e:
                logger.error(f"Ошибка при отключении от Uptime Kuma: {str(e)}")

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
        
    async def get_monitors(self) -> List[Dict[str, Any]]:
        """Получение списка мониторов с их статусами"""
        if not self.api:
            logger.error("Попытка получить мониторы без активного соединения.")
            raise ConnectionError("Соединение с Uptime Kuma не установлено.")
            
        try:
            logger.info("Получение списка мониторов")
            monitors_data = await asyncio.to_thread(self.api.get_monitors)
            
            result = []
            for monitor in monitors_data:
                status = 1
                if not monitor.get("active", True) or monitor.get("status", 1) == 0:
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
            
            logger.info(f"Получено {len(result)} мониторов")
            return result
        except Exception as e:
            logger.error(f"Ошибка при получении списка мониторов: {str(e)}")
            raise ConnectionError(f"Ошибка при получении списка мониторов: {str(e)}")
    
    async def get_monitor_by_id(self, monitor_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о конкретном мониторе по его ID"""
        logger.info(f"Поиск монитора по ID: {monitor_id}")
        monitors = await self.get_monitors()
        
        for monitor in monitors:
            if str(monitor.get("id")) == str(monitor_id):
                logger.info(f"Найден монитор: {monitor.get('name')}")
                return monitor
        
        logger.warning(f"Монитор с ID {monitor_id} не найден")
        return None
    
    async def get_monitor_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Получение информации о конкретном мониторе по его имени"""
        logger.info(f"Поиск монитора по имени: {name}")
        monitors = await self.get_monitors()
        
        for monitor in monitors:
            if monitor.get("name") == name:
                logger.info(f"Найден монитор: {name}")
                return monitor
        
        logger.warning(f"Монитор с именем {name} не найден")
        return None
    
    async def get_incidents(self) -> List[Dict[str, Any]]:
        """Получение списка инцидентов"""
        if not self.api:
            logger.error("Попытка получить инциденты без активного соединения.")
            raise ConnectionError("Соединение с Uptime Kuma не установлено.")
            
        try:
            logger.info("Получение списка инцидентов")
            incidents_data = await asyncio.to_thread(self.api.get_incidents)
            
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
            
            logger.info(f"Получено {len(result)} инцидентов")
            return result
        except Exception as e:
            logger.warning(f"Не удалось получить инциденты напрямую: {str(e)}, создаем из мониторов")
            return await self._create_incidents_from_monitors()
    
    async def _create_incidents_from_monitors(self) -> List[Dict[str, Any]]:
        """Создание списка инцидентов на основе неработающих мониторов"""
        logger.info("Создание инцидентов из неработающих мониторов")
        monitors = await self.get_monitors()
        
        incidents = []
        for monitor in monitors:
            if monitor.get("status") == 0 and monitor.get("active", True) and not monitor.get("maintenance", False):
                incidents.append({
                    "id": monitor.get("id"),
                    "title": f"Проблема с {monitor.get('name')}",
                    "monitor_name": monitor.get("name"),
                    "status": "down",
                    "started_at": "Недавно",
                    "resolved_at": ""
                })
        
        logger.info(f"Создано {len(incidents)} инцидентов из мониторов")
        return incidents
    
    async def get_status_summary(self) -> Dict[str, Any]:
        """Получение сводки о статусе всех мониторов"""
        logger.info("Получение сводки о статусе мониторов")
        monitors = await self.get_monitors()
        
        total = len(monitors)
        up = sum(1 for m in monitors if m.get("status") == 1 and m.get("active", True))
        down = sum(1 for m in monitors if m.get("status") == 0 and m.get("active", True) and not m.get("maintenance", False))
        maintenance = sum(1 for m in monitors if m.get("maintenance", False) and m.get("active", True))
        
        active_monitors = sum(1 for m in monitors if m.get("active", True))
        uptime = (up / active_monitors * 100) if active_monitors > 0 else 100
        
        summary = {
            "total": total,
            "up": up,
            "down": down,
            "maintenance": maintenance,
            "uptime": round(uptime, 2)
        }
        
        logger.info(f"Статус мониторов: всего {total}, работают {up}, не работают {down}, на обслуживании {maintenance}, uptime {uptime}%")
        return summary
