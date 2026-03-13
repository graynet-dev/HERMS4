# -*- coding: utf-8 -*-
import logging
from cbpi.api import *
from .actor import ESP32Actor
from .sensor import ESP32Sensor, ESP32TemperatureSensor
from .logic import ESP32KettleLogic
from .uart_manager import UARTManager

logger = logging.getLogger(__name__)

version = "0.1.0"

@parameters([
    Property.Select(label="Port", options=["/dev/ttyS0", "/dev/ttyUSB0", "/dev/ttyAMA0"], description="UART порт для связи с ESP32"),
    Property.Number(label="Baudrate", configurable=True, default=115200, description="Скорость UART"),
    Property.Number(label="Timeout", configurable=True, default=1.0, description="Таймаут ответа (сек)"),
    Property.Number(label="Channels", configurable=True, default=4, description="Количество каналов ESP32"),
])
class ESP32Controller(CBPiExtension):
    """
    Главный контроллер для связи с ESP32
    """
    def __init__(self, cbpi, **kwargs):
        self.cbpi = cbpi
        self.uart = None
        self.channels = {}
        self._running = True
        
    async def init(self):
        """Инициализация при старте"""
        self.port = await self.cbpi.config.get("ESP32_PORT", "/dev/ttyS0")
        self.baud = int(await self.cbpi.config.get("ESP32_BAUD", 115200))
        self.timeout = float(await self.cbpi.config.get("ESP32_TIMEOUT", 1.0))
        self.num_channels = int(await self.cbpi.config.get("ESP32_CHANNELS", 4))
        
        # Создаем менеджер UART
        self.uart = UARTManager(self.port, self.baud, self.timeout, self.num_channels)
        
        # Запускаем фоновую задачу для чтения данных
        asyncio.create_task(self._read_loop())
        
        logger.info(f"ESP32 Controller initialized on {self.port} at {self.baud} baud")
        
    async def _read_loop(self):
        """Фоновая задача для чтения данных от ESP32"""
        while self._running:
            if self.uart and self.uart.is_connected():
                # Читаем телеметрию
                data = await self.uart.read_telemetry()
                if data:
                    # Обновляем сенсоры
                    for i, ch in enumerate(data.get("channels", [])):
                        channel_id = i + 1
                        sensor_name = f"esp32_ch{channel_id}_power"
                        # TODO: обновить значение сенсора в CBPi4
                        
                    # Обрабатываем аварии
                    if "alarm" in data:
                        await self._handle_alarm(data["alarm"])
                        
            await asyncio.sleep(0.1)  # 10 Гц
            
    async def _handle_alarm(self, alarm):
        """Обработка аварийных сообщений"""
        logger.warning(f"ESP32 Alarm: {alarm}")
        await self.cbpi.notify(f"ESP32 Alarm CH{alarm.get('ch')}", 
                               alarm.get('msg'), 
                               type="danger")
        
    async def send_command(self, channel, command, value):
        """Отправка команды в ESP32"""
        if self.uart:
            return await self.uart.send_command(channel, command, value)
        return False
        
    async def stop(self):
        """Остановка при завершении"""
        self._running = False
        if self.uart:
            self.uart.close()

def setup(cbpi):
    """
    Регистрация плагина в CBPi4
    """
    # Регистрируем расширение (глобальный контроллер)
    cbpi.extension.add("ESP32Controller", ESP32Controller)
    
    # Регистрируем актуаторы
    cbpi.plugin.register("ESP32Actor", ESP32Actor)
    
    # Регистрируем сенсоры
    cbpi.plugin.register("ESP32Sensor", ESP32Sensor)
    cbpi.plugin.register("ESP32TemperatureSensor", ESP32TemperatureSensor)
    
    # Регистрируем логику котла
    cbpi.plugin.register("ESP32KettleLogic", ESP32KettleLogic)
    
    logger.info("ESP32 Brewery plugin loaded successfully")