# CBPi4 ESP32 Brewery Plugin

Плагин для интеграции ESP32 Brewery Controller с CraftBeerPi 4.

## Возможности

- ✅ Управление 4 каналами (мощность, температура)
- ✅ PID-регулирование на ESP32
- ✅ Автоматическая телеметрия (раз в секунду)
- ✅ Аварийные уведомления
- ✅ Поддержка PT100 и DS18B20
- ✅ Работа через UART

## Установка

```bash
cd ~/cbpi4-plugins
git clone https://github.com/graynet-dev/HERMS4.git
cd HERMS4/software/cbpi4-esp32-brewery
pip install -e .