from cbpi.api.config import ConfigType
from cbpi.api import *

@parameters([])
class ESP32Config(CBPiExtension):
    """
    Конфигурация плагина (добавляет настройки в CBPi4)
    """
    def __init__(self, cbpi):
        self.cbpi = cbpi
        
    async def init(self):
        """Добавление параметров в настройки CBPi4"""
        
        await self.cbpi.config.add(
            "ESP32_PORT", 
            "/dev/ttyS0", 
            ConfigType.STRING, 
            "UART порт для ESP32"
        )
        
        await self.cbpi.config.add(
            "ESP32_BAUD", 
            "115200", 
            ConfigType.STRING, 
            "Скорость UART"
        )
        
        await self.cbpi.config.add(
            "ESP32_TIMEOUT", 
            "1.0", 
            ConfigType.STRING, 
            "Таймаут ответа (сек)"
        )
        
        await self.cbpi.config.add(
            "ESP32_CHANNELS", 
            "4", 
            ConfigType.STRING, 
            "Количество каналов"
        )
        
        await self.cbpi.config.add(
            "ESP32_AUTO_RECONNECT", 
            "Yes", 
            ConfigType.SELECT, 
            "Автопереподключение", 
            options=["Yes", "No"]
        )

def setup(cbpi):
    cbpi.plugin.register("ESP32Config", ESP32Config)