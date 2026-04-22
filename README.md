# Strat-tools Server Monitor

Легкая система оперативного мониторинга Linux/Raspberry Pi сервера, который может выполнять роль gateway/router, VPN endpoint или split-routing узла.

Система собирает метрики в память процесса, показывает их через web dashboard `Gateway Telemetry` и не создает базу данных или исторический архив на диске.

## Возможности

- In-memory хранение истории через фиксированные ring buffer на базе `collections.deque(maxlen=...)`.
- Метрики CPU, RAM, load average и температуры CPU.
- Графики сетевого трафика по интерфейсам, например `eth0`, `eth0.3`, `ppp0`.
- Проверки `ppp0`, `sstp-vpn.service`, default route через VPN, routing table `direct` и даты обновления RU-списка.
- REST API для текущего состояния и истории.
- Web dashboard в стиле infrastructure/network operations UI.
- Встроенная пользовательская справка по кнопке `Help`, включая схему маршрутизации gateway.
- Контекстные подсказки по основным метрикам и графикам.
- Несколько пользовательских сетевых графиков с собственным набором интерфейсов.
- Перетаскиваемая компоновка графиков по строкам, сохраняемая в браузере.
- Peak statistics по интерфейсам: максимальные RX/TX с момента старта сервиса или последнего сброса.
- Переключение отображения сетевого трафика между bytes/sec и bits/sec без изменения backend-данных.
- Без SQLite, PostgreSQL, InfluxDB, Prometheus, Grafana и Docker.

## Документация

- [ARCHITECTURE.md](ARCHITECTURE.md) — архитектурная и техническая документация для handover, сопровождения и оценки решений.
- [USER_GUIDE.md](USER_GUIDE.md) — пользовательское руководство по dashboard, метрикам, статусам и типовым проблемам.
- [Docs/deployment-linux.md](Docs/deployment-linux.md) — подробная пошаговая инструкция развертывания на Debian/Raspberry Pi OS.
- [Docs/routing-overview.md](Docs/routing-overview.md) — описание схемы маршрутизации gateway с диаграммой.
- [server_monitor/static/help.ru.html](server_monitor/static/help.ru.html), [server_monitor/static/help.en.html](server_monitor/static/help.en.html), [server_monitor/static/help.html](server_monitor/static/help.html) — встроенная справка, которая открывается в интерфейсе по кнопке `Help`.

## Структура проекта

```text
server_monitor/
  app.py
  collector.py
  buffer.py
  metrics.py
  config.py
  api.py
  templates/
    index.html
  static/
    app.js
    style.css
    help.html
    help.ru.html
    help.en.html
    routing-overview.svg
systemd/
  server-monitor.service
Docs/
  deployment-linux.md
  routing-overview.md
  assets/
    routing-overview.svg
requirements.txt
config.example.yaml
config.yaml
USER_GUIDE.md
README.md
```

## Требования

- Python 3.9+
- Linux или Raspberry Pi OS
- Доступные системные команды для расширенных проверок:
  - `ip`
  - `systemctl`
  - `vcgencmd`, если используется Raspberry Pi temperature sensor

## Быстрый запуск для проверки

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.yaml config.yaml
python3 -m server_monitor.app --config config.yaml
```

После запуска откройте:

```text
http://SERVER_IP:8080
```

На странице должен открыться dashboard `Gateway Telemetry` с брендом `Strat-tools`, summary-карточками, health-блоком, графиками и кнопкой `Help`.

В интерфейсе также доступны:

- `Traffic units`: переключение сетевого трафика между байтами/с и битами/с.
- `Add network chart`: добавление дополнительных сетевых графиков в блоке выбора интерфейсов.
- `Reset peak stats`: сброс максимальных значений RX/TX по интерфейсам.
- Иконки `i`: короткие контекстные подсказки без перехода в отдельную справку.

Встроенная справка содержит пользовательское руководство и раздел `Схема маршрутизации / Routing diagram`. Схема загружается как static-файл `/static/routing-overview.svg`, поэтому она доступна прямо в modal help без перехода к Markdown-документации.

## Конфигурация

Пример `config.yaml`:

```yaml
collect_interval_seconds: 10
history_window_hours: 168
interfaces:
  - eth0
  - eth0.3
  - ppp0
web_host: 0.0.0.0
web_port: 8080
route_test_target: 8.8.8.8
ru_update_file: /var/lib/ru-nft-last-update
vpn_service_name: sstp-vpn.service
log_level: INFO
```

Параметры:

- `collect_interval_seconds`: интервал сбора метрик.
- `history_window_hours`: глубина ring buffer в часах.
- `interfaces`: интерфейсы, отображаемые в статусе и графике сети.
- `web_host`, `web_port`: адрес и порт web-сервера.
- `route_test_target`: адрес для проверки default route через `ip route get`.
- `ru_update_file`: файл, по времени изменения которого определяется обновление RU-списка.
- `vpn_service_name`: сервис, проверяемый через `systemctl is-active`.

## API

### `GET /api/status`

Возвращает текущее состояние:

- `cpu`
- `ram`
- `load1`
- `temperature`
- состояние настроенных интерфейсов
- `vpn_service_active`
- `default_route_via_vpn`
- `table_direct_exists`
- `ru_update_timestamp`
- `history_memory`: оценка памяти, занятой in-memory history buffers, включая текущую заполненность и максимальную емкость окна.
- `disk_usage`: общий, занятый и свободный объем дискового пространства для корневой файловой системы `/`.

### `GET /api/metrics`

Возвращает список доступных метрик и metadata для сетевых интерфейсов.

### `GET /api/history`

Query params:

- `metric`: `cpu`, `ram`, `load1`, `temperature`, `net`
- `period`: `1h`, `24h`, `7d`
- `step`: `raw`, `1m`, `5m`, `15m`
- `interface`: обязателен для `metric=net`

Примеры:

```text
/api/history?metric=cpu&period=24h&step=raw
/api/history?metric=net&period=7d&step=5m&interface=ppp0
```

Агрегация:

- CPU, RAM, load, temperature: среднее значение внутри bucket.
- Network traffic: средняя скорость bytes/sec внутри bucket.

### `GET /api/peak-stats`

Возвращает in-memory peak statistics по сетевым интерфейсам:

- `max_rx`: максимальная зафиксированная скорость RX в bytes/sec.
- `max_tx`: максимальная зафиксированная скорость TX в bytes/sec.
- `max_rx_timestamp`: время достижения максимального RX, если доступно.
- `max_tx_timestamp`: время достижения максимального TX, если доступно.

### `POST /api/peak-stats/reset`

Сбрасывает peak statistics в памяти процесса. После сброса максимумы начинают считаться заново.

## systemd deployment

Кратко:

1. Скопируйте проект в `/opt/server-monitor`.
2. Создайте `/opt/server-monitor/config.yaml`.
3. Установите зависимости в virtualenv.
4. Скопируйте `systemd/server-monitor.service` в `/etc/systemd/system/server-monitor.service`.
5. Перечитайте systemd и запустите сервис:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now server-monitor.service
sudo systemctl status server-monitor.service
```

Подробная инструкция: [Docs/deployment-linux.md](Docs/deployment-linux.md).

## Проверка после запуска

```bash
curl http://127.0.0.1:8080/api/status
curl http://127.0.0.1:8080/api/metrics
curl http://127.0.0.1:8080/static/help.html
curl http://127.0.0.1:8080/static/help.ru.html
curl http://127.0.0.1:8080/static/routing-overview.svg
```

Ожидаемо:

- API возвращает JSON.
- `/static/help.html` и `/static/help.ru.html` возвращают HTML встроенной справки.
- `/static/routing-overview.svg` возвращает SVG-схему маршрутизации для modal help.
- Web UI открывается по `http://SERVER_IP:8080`.

## Важные ограничения

- История метрик хранится только в памяти процесса.
- После перезапуска сервиса или сервера история графиков очищается.
- Peak statistics также хранится только в памяти и очищается после перезапуска.
- Система не является долгосрочным архивом мониторинга.
- Метрики не пишутся на диск.
- Пользовательские настройки UI, например язык, единицы трафика, выбранные интерфейсы и layout графиков, хранятся только в `localStorage` браузера.
- Показатель `History memory` является оценкой объема данных в ring buffers, а не полной RSS-памятью Python-процесса.
- Если интерфейс, датчик или системная команда недоступны, соответствующий показатель может быть `n/a`, `unknown` или пустым, но приложение должно продолжать работать.
