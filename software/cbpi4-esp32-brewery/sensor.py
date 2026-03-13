from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

@parameters([
    Property.Select(label="Channel", options=[1,2,3,4], description="Номер канала на ESP32"),
    Property.Select(label="ValueType", options=["power", "voltage", "current", "target"], 
                    default="power", description="Тип значения"),
    Property.Number(label="Factor", configurable=True, default=1.0, description="Множитель"),
    Property.Number(label="Offset", configurable=True, default=0.0, description="Смещение"),
])
class ESP32Sensor(CBPiSensor):
    """
    Сенсор для чтения данных канала ESP32
    """
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.channel = int(props.get("Channel", 1))
        self.value_type = props.get("ValueType", "power")
        self.factor = float(props.get("Factor", 1.0))
        self.offset = float(props.get("Offset", 0.0))
        self.last_value = 0
        
    async def read(self):
        """Чтение значения"""
        controller = self.cbpi.extension.get("ESP32Controller")
        if not controller or not controller.uart:
            return self.last_value
            
        # Берем последние полученные данные
        data = controller.uart._last_data
        
        if data and "channels" in data:
            for ch in data["channels"]:
                if ch.get("ch") == self.channel - 1:  # ESP32 индексы с 0
                    if self.value_type == "power":
                        val = ch.get("p", 0)
                    elif self.value_type == "voltage":
                        val = ch.get("v", 0)
                    elif self.value_type == "current":
                        val = ch.get("c", 0)
                    elif self.value_type == "target":
                        val = ch.get("t", 0)
                    else:
                        val = 0
                        
                    self.last_value = (val * self.factor) + self.offset
                    return self.last_value
                    
        return self.last_value


@parameters([
    Property.Select(label="Index", options=[0,1,2,3,4,5,6,7], description="Индекс PT100 датчика"),
    Property.Number(label="Factor", configurable=True, default=1.0, description="Множитель"),
    Property.Number(label="Offset", configurable=True, default=0.0, description="Смещение"),
])
class ESP32TemperatureSensor(CBPiSensor):
    """
    Сенсор для чтения PT100 температур
    """
    def __init__(self, cbpi, id, props):
        super().__init__(cbpi, id, props)
        self.index = int(props.get("Index", 0))
        self.factor = float(props.get("Factor", 1.0))
        self.offset = float(props.get("Offset", 0.0))
        self.last_value = 20.0  # комнатная температура по умолчанию
        
    async def read(self):
        controller = self.cbpi.extension.get("ESP32Controller")
        if not controller or not controller.uart:
            return self.last_value
            
        data = controller.uart._last_data
        if data and "temps" in data and "pt100" in data["temps"]:
            pt100 = data["temps"]["pt100"]
            if self.index < len(pt100):
                self.last_value = (pt100[self.index] * self.factor) + self.offset
                
        return self.last_value