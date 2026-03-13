import asyncio
import serial
import serial_asyncio
import json
import logging
import re

logger = logging.getLogger(__name__)

class UARTManager:
    """
    Асинхронный менеджер UART для связи с ESP32
    """
    def __init__(self, port, baudrate, timeout, num_channels):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.num_channels = num_channels
        self.reader = None
        self.writer = None
        self.connected = False
        self._lock = asyncio.Lock()
        self._response_queue = asyncio.Queue()
        self._last_data = {}
        
    async def connect(self):
        """Подключение к UART порту"""
        try:
            self.reader, self.writer = await serial_asyncio.open_serial_connection(
                url=self.port, 
                baudrate=self.baudrate
            )
            self.connected = True
            logger.info(f"Connected to ESP32 on {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ESP32: {e}")
            self.connected = False
            return False
            
    def is_connected(self):
        return self.connected and self.writer is not None
        
    async def send_command(self, channel, command, value):
        """
        Отправка команды в ESP32
        
        Форматы:
        - P1:50  - установка мощности
        - T2:72.5 - установка температуры
        - M1:0    - установка режима
        - PID1:2.0,0.1,0.05 - PID коэффициенты
        - STATUS - запрос статуса
        """
        if not self.is_connected():
            await self.connect()
            
        if command == 'power':
            cmd_str = f"P{channel}:{value}\n"
        elif command == 'temp':
            cmd_str = f"T{channel}:{value}\n"
        elif command == 'mode':
            cmd_str = f"M{channel}:{value}\n"
        elif command == 'pid':
            kp, ki, kd = value
            cmd_str = f"PID{channel}:{kp},{ki},{kd}\n"
        elif command == 'status':
            cmd_str = "STATUS\n"
        else:
            logger.error(f"Unknown command: {command}")
            return False
            
        async with self._lock:
            try:
                self.writer.write(cmd_str.encode())
                await self.writer.drain()
                logger.debug(f"Sent: {cmd_str.strip()}")
                
                # Ждем ответ (OK или ERROR)
                response = await asyncio.wait_for(
                    self.reader.readline(), 
                    timeout=self.timeout
                )
                response = response.decode().strip()
                
                if response.startswith("OK"):
                    return True
                else:
                    logger.error(f"ESP32 error: {response}")
                    return False
                    
            except Exception as e:
                logger.error(f"UART communication error: {e}")
                self.connected = False
                return False
                
    async def read_telemetry(self):
        """
        Чтение телеметрии от ESP32 (автоматическая отправка)
        """
        if not self.is_connected():
            if not await self.connect():
                return None
                
        try:
            # Неблокирующее чтение
            if self.reader._transport is None:
                return None
                
            # Пытаемся прочитать строку (если есть)
            line = await asyncio.wait_for(
                self.reader.readline(), 
                timeout=0.1
            )
            
            if line:
                data_str = line.decode().strip()
                
                # Парсим JSON телеметрию
                if data_str.startswith('{'):
                    try:
                        data = json.loads(data_str)
                        self._last_data = data
                        return data
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON: {data_str}")
                        
                # Аварийные сообщения
                elif data_str.startswith('ALARM:'):
                    # ALARM:CH1,OVERCURRENT
                    parts = data_str[6:].split(',')
                    alarm = {
                        'ch': int(parts[0].replace('CH', '')),
                        'type': parts[1],
                        'msg': parts[2] if len(parts) > 2 else ''
                    }
                    return {'alarm': alarm}
                    
        except asyncio.TimeoutError:
            # Нет данных - нормально
            pass
        except Exception as e:
            logger.error(f"Read error: {e}")
            self.connected = False
            
        return None
        
    def close(self):
        """Закрытие соединения"""
        if self.writer:
            self.writer.close()
            self.connected = False