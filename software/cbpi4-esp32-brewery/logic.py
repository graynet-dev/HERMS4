from cbpi.api import *
import logging

logger = logging.getLogger(__name__)

@parameters([
    Property.Select(label="Channel", options=[1,2,3,4], description="Номер канала на ESP32"),
    Property.Select(label="Mode", options=["power", "temp"], default="temp", description="Режим по умолчанию"),
    Property.Number(label="Kp", configurable=True, default=2.0, description="PID Kp"),
    Property.Number(label="Ki", configurable=True, default=0.1, description="PID Ki"),
    Property.Number(label="Kd", configurable=True, default=0.05, description="PID Kd"),
])
class ESP32KettleLogic(CBPiKettleLogic):
    """
    Логика котла для управления через ESP32
    """
    async def run(self):
        """
        Запуск логики (вызывается из шага рецепта)
        """
        self.channel = int(self.props.get("Channel", 1))
        self.mode = self.props.get("Mode", "temp")
        self.target_temp = self.get_target_temp()
        
        # Устанавливаем режим
        controller = self.cbpi.extension.get("ESP32Controller")
        if controller:
            mode_val = 1 if self.mode == "temp" else 0
            await controller.send_command(self.channel, "mode", mode_val)
            
            # Устанавливаем PID коэффициенты
            kp = float(self.props.get("Kp", 2.0))
            ki = float(self.props.get("Ki", 0.1))
            kd = float(self.props.get("Kd", 0.05))
            await controller.send_command(self.channel, "pid", (kp, ki, kd))
            
        logger.info(f"ESP32 KettleLogic started for channel {self.channel}")
        
        # Основной цикл
        while self.running:
            # ESP32 сам поддерживает температуру, мы только мониторим
            sensor = self.get_sensor(self.props.get("Sensor"))
            if sensor:
                current_temp = await sensor.get_value()
                
                # Проверяем достижение цели
                if abs(current_temp - self.target_temp) < 0.5:
                    logger.info(f"Target temperature reached: {current_temp}")
                    
            await asyncio.sleep(2)