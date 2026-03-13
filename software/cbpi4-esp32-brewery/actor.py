from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

@parameters([
    Property.Select(label="Channel", options=[1,2,3,4], description="Номер канала на ESP32"),
    Property.Select(label="Type", options=["power", "temp"], description="Тип управления"),
    Property.Number(label="Timeout", configurable=True, default=1.0, description="Таймаут команды (сек)"),
])
class ESP32Actor(CBPiActor):
    """
    Актуатор для управления каналом ESP32
    """
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.channel = int(props.get("Channel", 1))
        self.type = props.get("Type", "power")
        self.timeout = float(props.get("Timeout", 1.0))
        self.state = False
        self.power = 0
        
    async def on_start(self):
        """Инициализация при старте"""
        # Получаем контроллер ESP32
        self.controller = self.cbpi.extension.get("ESP32Controller")
        if not self.controller:
            logger.error("ESP32Controller not found")
            
    async def on(self, power=None):
        """
        Включение канала с заданной мощностью/температурой
        """
        if self.type == "power":
            # Режим мощности (0-100%)
            target = power if power is not None else self.power
            target = max(0, min(100, target))
            success = await self.controller.send_command(
                self.channel, "power", target
            )
            if success:
                self.power = target
                self.state = True
                
        else:  # temp mode
            # Режим температуры (градусы)
            target = power if power is not None else self.power
            success = await self.controller.send_command(
                self.channel, "temp", target
            )
            if success:
                self.power = target
                self.state = True
                
    async def off(self):
        """Выключение канала"""
        success = await self.controller.send_command(
            self.channel, "power", 0
        )
        if success:
            self.state = False
            self.power = 0
            
    def get_state(self):
        return self.state
        
    def set_power(self, power):
        """Установка мощности (для совместимости с PID)"""
        self.power = power
        if self.state:
            asyncio.create_task(self.on(power))