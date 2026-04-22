# Развертывание Strat-tools Server Monitor на Debian / Raspberry Pi OS

Эта инструкция описывает установку системы мониторинга сервера Strat-tools Server Monitor на Linux с нуля. Она подходит для Raspberry Pi OS / Debian bullseye и рассчитана на пользователя без опыта администрирования Linux.

Система мониторинга:

- собирает CPU, RAM, load average, температуру, сетевой трафик и VPN-статус;
- показывает данные в web dashboard `Gateway Telemetry`;
- содержит встроенную пользовательскую справку по кнопке `Help`;
- хранит историю только в памяти процесса;
- не использует SQLite, PostgreSQL, InfluxDB, Prometheus, Grafana или Docker;
- теряет историю после перезапуска сервиса, и это нормальное поведение.

## 1. Что нужно заранее

Нужны:

- сервер или Raspberry Pi с Debian / Raspberry Pi OS;
- доступ к серверу по SSH;
- пользователь с правом выполнять команды через `sudo`;
- файлы проекта `server-monitor`;
- компьютер или телефон в той же сети, чтобы открыть веб-интерфейс.

В инструкции ниже предполагается, что приложение будет установлено в:

```text
/opt/server-monitor
```

Веб-интерфейс будет доступен на порту:

```text
8080
```

## 2. Подключение к серверу

Выполните команду на своем компьютере:

```bash
ssh USERNAME@SERVER_IP
```

Что произошло:

Вы подключились к Linux-серверу по SSH.

Ожидаемый результат:

Вы увидите командную строку сервера.

Пример:

```text
USERNAME@raspberrypi:~ $
```

Если появилась ошибка `Connection refused`:

SSH на сервере не запущен или недоступен.

Что сделать:

```bash
sudo systemctl status ssh
```

Если появилась ошибка `No route to host`:

Компьютер не видит сервер по сети.

Что сделать:

- проверьте IP-адрес сервера;
- проверьте, что Raspberry Pi включен;
- проверьте кабель Ethernet или Wi-Fi;
- попробуйте подключиться еще раз.

## 3. Обновление системы

Выполните:

```bash
sudo apt update
```

Что произошло:

Система обновила список доступных пакетов.

Ожидаемый результат:

Команда завершится без ошибок и снова появится приглашение командной строки.

Если появилась ошибка сети:

Проверьте доступ в интернет:

```bash
ping -c 4 8.8.8.8
```

Ожидаемый результат:

Вы увидите ответы вида `64 bytes from 8.8.8.8`.

Если ответов нет:

Проверьте сетевое подключение сервера.

Теперь обновите установленные пакеты:

```bash
sudo apt upgrade -y
```

Что произошло:

Система установила обновления.

Ожидаемый результат:

Команда завершится без ошибок.

Если система попросит перезагрузку:

```bash
sudo reboot
```

Что произошло:

Сервер перезагрузится.

Ожидаемый результат:

Через 1-2 минуты можно снова подключиться по SSH.

## 4. Установка Python и базовых инструментов

Выполните:

```bash
sudo apt install -y python3 python3-pip python3-venv curl nano iproute2 procps
```

Что произошло:

Установлены:

- `python3` — язык Python для запуска приложения;
- `python3-pip` — установщик Python-библиотек;
- `python3-venv` — инструмент для отдельного окружения приложения;
- `curl` — утилита для проверки HTTP API;
- `nano` — простой текстовый редактор;
- `iproute2` — команда `ip` для проверки сетевых интерфейсов и маршрутов;
- `procps` — системные утилиты.

Ожидаемый результат:

Пакеты установятся без ошибок.

Если появилась ошибка `Unable to locate package`:

Повторите обновление списка пакетов:

```bash
sudo apt update
```

Затем повторите установку:

```bash
sudo apt install -y python3 python3-pip python3-venv curl nano iproute2 procps
```

Проверьте версию Python:

```bash
python3 --version
```

Что произошло:

Система показала установленную версию Python.

Ожидаемый результат:

Например:

```text
Python 3.9.2
```

Если появилась ошибка `python3: command not found`:

Python не установлен. Повторите команду установки из этого раздела.

## 5. Создание папки приложения

Создайте директорию:

```bash
sudo mkdir -p /opt/server-monitor
```

Что произошло:

Создана папка `/opt/server-monitor`.

Ожидаемый результат:

Команда ничего не выведет. Это нормально.

Выдайте текущему пользователю права на папку:

```bash
sudo chown -R $USER:$USER /opt/server-monitor
```

Что произошло:

Текущий пользователь стал владельцем папки `/opt/server-monitor`.

Ожидаемый результат:

Команда ничего не выведет.

Проверьте папку:

```bash
ls -la /opt
```

Что произошло:

Система показала содержимое `/opt`.

Ожидаемый результат:

В списке должна быть папка `server-monitor`.

## 6. Размещение файлов проекта

Выберите один из вариантов.

### Вариант 1. Копирование через Git

Если проект хранится в Git-репозитории, установите Git:

```bash
sudo apt install -y git
```

Что произошло:

Установлена команда `git`.

Ожидаемый результат:

Команда завершится без ошибок.

Скачайте проект:

```bash
git clone REPOSITORY_URL /opt/server-monitor
```

Что произошло:

Git скачал файлы проекта в `/opt/server-monitor`.

Ожидаемый результат:

В папке появятся файлы `requirements.txt`, `config.example.yaml`, `README.md` и папка `server_monitor`.

Если появилась ошибка `destination path already exists and is not an empty directory`:

Папка уже содержит файлы.

Что сделать:

Проверьте содержимое:

```bash
ls -la /opt/server-monitor
```

Если там старые ненужные файлы, удалите их:

```bash
rm -rf /opt/server-monitor/*
```

После этого повторите:

```bash
git clone REPOSITORY_URL /opt/server-monitor
```

### Вариант 2. Копирование через SCP с Linux или macOS

Команду нужно выполнять на вашем компьютере, не на сервере:

```bash
scp -r /LOCAL/PATH/server-monitor/* USERNAME@SERVER_IP:/opt/server-monitor/
```

Что произошло:

Файлы проекта скопированы с вашего компьютера на сервер.

Ожидаемый результат:

Команда завершится без ошибок.

Если появилась ошибка `Permission denied`:

Проверьте:

- правильное имя пользователя;
- правильный IP сервера;
- что папка `/opt/server-monitor` создана;
- что на шаге 5 выполнена команда `sudo chown -R $USER:$USER /opt/server-monitor`.

### Вариант 3. Копирование через SCP с Windows PowerShell

Команду нужно выполнять на Windows-компьютере в PowerShell:

```powershell
scp -r "C:\PATH\TO\server-monitor\*" USERNAME@SERVER_IP:/opt/server-monitor/
```

Что произошло:

Файлы проекта скопированы с Windows на сервер.

Ожидаемый результат:

Команда завершится без ошибок.

Если Windows не знает команду `scp`:

Установите компонент OpenSSH Client в Windows или используйте WinSCP.

## 7. Проверка файлов проекта

На сервере выполните:

```bash
ls -la /opt/server-monitor
```

Что произошло:

Показано содержимое папки проекта.

Ожидаемый результат:

Вы должны увидеть:

```text
requirements.txt
config.example.yaml
README.md
USER_GUIDE.md
Docs
server_monitor
systemd
```

Проверьте папку приложения:

```bash
ls -la /opt/server-monitor/server_monitor
```

Что произошло:

Показаны Python-файлы приложения.

Ожидаемый результат:

Вы должны увидеть:

```text
app.py
api.py
collector.py
buffer.py
config.py
metrics.py
static
templates
```

Проверьте статические файлы интерфейса:

```bash
ls -la /opt/server-monitor/server_monitor/static
```

Что произошло:

Показаны JavaScript, CSS, встроенная справка dashboard и SVG-схема маршрутизации.

Ожидаемый результат:

Вы должны увидеть:

```text
app.js
style.css
help.html
help.ru.html
help.en.html
routing-overview.svg
```

Если файлов нет:

Проект скопирован не полностью. Вернитесь к разделу 6.

## 8. Создание виртуального окружения Python

Выполните:

```bash
python3 -m venv /opt/server-monitor/venv
```

Что произошло:

Создано отдельное Python-окружение в `/opt/server-monitor/venv`.

Ожидаемый результат:

Команда ничего не выведет.

Проверьте:

```bash
ls -la /opt/server-monitor/venv
```

Ожидаемый результат:

Вы должны увидеть папки `bin`, `lib`, `include`.

Если появилась ошибка про `ensurepip`:

Установите пакет `python3-venv`:

```bash
sudo apt install -y python3-venv
```

Повторите создание окружения:

```bash
python3 -m venv /opt/server-monitor/venv
```

## 9. Активация виртуального окружения

Выполните:

```bash
source /opt/server-monitor/venv/bin/activate
```

Что произошло:

Текущая SSH-сессия начала использовать Python и pip из окружения приложения.

Ожидаемый результат:

В начале командной строки может появиться:

```text
(venv)
```

Если появилась ошибка `No such file or directory`:

Виртуальное окружение не создано. Повторите раздел 8.

Проверьте, какой Python используется:

```bash
which python
```

Ожидаемый результат:

```text
/opt/server-monitor/venv/bin/python
```

## 10. Установка зависимостей Python

Обновите pip:

```bash
pip install --upgrade pip
```

Что произошло:

Обновлен установщик Python-библиотек внутри виртуального окружения.

Ожидаемый результат:

Появится сообщение об успешной установке pip.

Установите зависимости:

```bash
pip install -r /opt/server-monitor/requirements.txt
```

Что произошло:

pip прочитал файл `requirements.txt` и установил нужные библиотеки.

Что такое `requirements.txt`:

Это обычный текстовый файл со списком Python-библиотек, которые нужны приложению.

Ожидаемый результат:

Будут установлены библиотеки:

- `fastapi`;
- `uvicorn`;
- `psutil`;
- `PyYAML`;
- `Jinja2`.

Если появилась ошибка `No such file or directory`:

Файл `/opt/server-monitor/requirements.txt` отсутствует. Проверьте копирование проекта.

Если появилась ошибка сети:

Проверьте интернет:

```bash
ping -c 4 pypi.org
```

Если ответа нет:

Проверьте DNS и интернет-соединение сервера.

## 11. Создание конфигурации

Скопируйте пример конфига:

```bash
cp /opt/server-monitor/config.example.yaml /opt/server-monitor/config.yaml
```

Что произошло:

Создан рабочий конфигурационный файл `/opt/server-monitor/config.yaml`.

Ожидаемый результат:

Команда ничего не выведет.

Откройте файл:

```bash
nano /opt/server-monitor/config.yaml
```

Что произошло:

Открылся редактор `nano`.

Ожидаемый результат:

Вы видите настройки приложения.

Пример содержимого:

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

Как сохранить в `nano`:

Нажмите `Ctrl+O`.

Нажмите `Enter`.

Как выйти из `nano`:

Нажмите `Ctrl+X`.

Что означает каждое поле:

- `collect_interval_seconds`: как часто собирать метрики, например `10` означает каждые 10 секунд.
- `history_window_hours`: сколько часов истории держать в памяти, например `168` означает 7 дней.
- `interfaces`: список сетевых интерфейсов для графиков.
- `web_host`: адрес, на котором слушает веб-сервер. Значение `0.0.0.0` означает доступ с других устройств в сети.
- `web_port`: порт веб-интерфейса.
- `route_test_target`: адрес, до которого проверяется маршрут через VPN.
- `ru_update_file`: файл с датой последнего обновления RU-списка.
- `vpn_service_name`: имя VPN-сервиса systemd.
- `log_level`: уровень логирования.

## 12. Проверка сетевых интерфейсов

Выполните:

```bash
ip a
```

Что произошло:

Linux показал сетевые интерфейсы сервера.

Ожидаемый результат:

Вы увидите список интерфейсов, например:

```text
eth0
eth0.3
ppp0
lo
```

Если интерфейса `ppp0` нет:

Это может быть нормально, если VPN сейчас не подключен.

Если интерфейса `eth0.3` нет:

Проверьте, нужен ли он именно на вашем сервере.

Если в конфиге указан несуществующий интерфейс:

Откройте конфиг:

```bash
nano /opt/server-monitor/config.yaml
```

Удалите или замените интерфейс в блоке:

```yaml
interfaces:
  - eth0
  - eth0.3
  - ppp0
```

Сохраните файл.

## 13. Тестовый запуск вручную

Перейдите в папку проекта:

```bash
cd /opt/server-monitor
```

Что произошло:

Текущая директория стала `/opt/server-monitor`.

Ожидаемый результат:

Команда ничего не выведет.

Активируйте окружение:

```bash
source /opt/server-monitor/venv/bin/activate
```

Что произошло:

Активировано Python-окружение приложения.

Ожидаемый результат:

В командной строке может быть `(venv)`.

Запустите приложение:

```bash
python -m server_monitor.app --config /opt/server-monitor/config.yaml
```

Что произошло:

Приложение запущено вручную.

Ожидаемый результат:

Вы увидите текст примерно такого вида:

```text
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

Если появилась ошибка `ModuleNotFoundError`:

Зависимости не установлены или окружение не активировано.

Исправление:

```bash
source /opt/server-monitor/venv/bin/activate
```

```bash
pip install -r /opt/server-monitor/requirements.txt
```

Если появилась ошибка `Address already in use`:

Порт уже занят.

Проверьте, кто занимает порт:

```bash
sudo ss -ltnp | grep 8080
```

Можно изменить порт в конфиге:

```bash
nano /opt/server-monitor/config.yaml
```

Например:

```yaml
web_port: 8090
```

## 14. Определение IP-адреса сервера

Откройте второе SSH-окно или остановите ручной запуск клавишами `Ctrl+C`.

Выполните:

```bash
ip a
```

Что произошло:

Показаны IP-адреса сервера.

Ожидаемый результат:

Найдите адрес вида:

```text
192.168.1.25
```

или:

```text
10.0.0.15
```

Это IP сервера в локальной сети.

Если IP не виден:

Сервер не подключен к сети или сетевой интерфейс не получил адрес.

## 15. Открытие веб-интерфейса

На компьютере или телефоне в той же сети откройте браузер.

Введите адрес:

```text
http://SERVER_IP:8080
```

Пример:

```text
http://192.168.1.25:8080
```

Что произошло:

Браузер подключился к веб-интерфейсу мониторинга.

Ожидаемый результат:

Вы увидите dashboard:

- бренд `Strat-tools`;
- заголовок `Gateway Telemetry`;
- текущий CPU;
- текущую RAM;
- load average;
- температуру;
- состояние `ppp0`;
- IP `ppp0`;
- состояние VPN-сервиса;
- default route via VPN;
- дату обновления RU-списка;
- графики CPU, RAM, температуры и сети;
- кнопку `Help` для открытия встроенной справки.

Если страница не открывается:

Перейдите к разделу 26.

## 16. Проверка API вручную

Если приложение запущено вручную, откройте вторую SSH-сессию.

Проверьте статус:

```bash
curl http://127.0.0.1:8080/api/status
```

Что произошло:

Сервер запросил собственный API.

Ожидаемый результат:

Вы увидите JSON с текущими метриками.

Проверьте список метрик:

```bash
curl http://127.0.0.1:8080/api/metrics
```

Ожидаемый результат:

Вы увидите JSON со списком доступных метрик.

Проверьте историю CPU:

```bash
curl "http://127.0.0.1:8080/api/history?metric=cpu&period=1h&step=raw"
```

Ожидаемый результат:

Вы увидите JSON с массивом точек.

Если массив пустой:

Подождите 30-60 секунд и повторите команду.

Проверьте сеть:

```bash
curl "http://127.0.0.1:8080/api/history?metric=net&period=1h&step=raw&interface=ppp0"
```

Ожидаемый результат:

Вы увидите JSON с сериями `rx` и `tx`.

Если массивы пустые:

Подождите минимум два интервала сбора. Для сети первая скорость появляется после второго измерения.

## 17. Остановка ручного запуска

В окне, где запущено приложение, нажмите:

```text
Ctrl+C
```

Что произошло:

Ручной процесс приложения остановлен.

Ожидаемый результат:

Вы снова увидите командную строку.

Важно:

После остановки история метрик в памяти потеряна. Это ожидаемое поведение.

## 18. Что такое systemd

`systemd` — это встроенный механизм Linux для запуска фоновых сервисов.

Он нужен, чтобы:

- приложение запускалось без открытого SSH-окна;
- приложение стартовало после перезагрузки сервера;
- приложение автоматически перезапускалось при сбое;
- можно было смотреть статус и логи.

Сервис systemd описывается в unit-файле.

Для нашего приложения unit-файл будет:

```text
/etc/systemd/system/server-monitor.service
```

## 19. Создание systemd service

Откройте unit-файл:

```bash
sudo nano /etc/systemd/system/server-monitor.service
```

Что произошло:

Открылся редактор `nano` для создания service-файла.

Ожидаемый результат:

Вы видите пустой файл.

Вставьте:

```ini
[Unit]
Description=In-memory Server Monitor
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/server-monitor
ExecStart=/opt/server-monitor/venv/bin/python -m server_monitor.app --config /opt/server-monitor/config.yaml
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Сохраните файл:

Нажмите `Ctrl+O`.

Нажмите `Enter`.

Выйдите:

Нажмите `Ctrl+X`.

Что означает блок `[Unit]`:

- `Description` — понятное описание сервиса.
- `After=network-online.target` — запускать после появления сети.
- `Wants=network-online.target` — попросить systemd дождаться сети.

Что означает блок `[Service]`:

- `Type=simple` — обычный долгоживущий процесс.
- `User=root` — запуск от root, чтобы читать системные данные и выполнять проверки `ip`/`systemctl`.
- `WorkingDirectory=/opt/server-monitor` — рабочая папка приложения.
- `ExecStart=...` — точная команда запуска.
- `Restart=always` — перезапускать при падении.
- `RestartSec=5` — ждать 5 секунд перед перезапуском.
- `Environment=PYTHONUNBUFFERED=1` — сразу писать логи без задержки.

Что означает блок `[Install]`:

- `WantedBy=multi-user.target` — разрешает включить автозапуск при обычной загрузке Linux.

## 20. Перечитывание systemd

Выполните:

```bash
sudo systemctl daemon-reexec
```

Что произошло:

systemd перезапустил свой управляющий процесс.

Ожидаемый результат:

Команда ничего не выведет.

Выполните:

```bash
sudo systemctl daemon-reload
```

Что произошло:

systemd перечитал service-файлы.

Ожидаемый результат:

Команда ничего не выведет.

Если появилась ошибка:

Проверьте файл:

```bash
sudo systemctl status server-monitor
```

И перечитайте содержимое:

```bash
sudo cat /etc/systemd/system/server-monitor.service
```

## 21. Включение автозапуска

Выполните:

```bash
sudo systemctl enable server-monitor
```

Что произошло:

Сервис добавлен в автозагрузку.

Ожидаемый результат:

Вы увидите сообщение о создании символической ссылки.

Если появилась ошибка `Unit server-monitor.service does not exist`:

Файл сервиса создан не там или назван иначе.

Проверьте:

```bash
ls -la /etc/systemd/system/server-monitor.service
```

## 22. Запуск сервиса

Выполните:

```bash
sudo systemctl start server-monitor
```

Что произошло:

systemd запустил приложение в фоне.

Ожидаемый результат:

Команда ничего не выведет.

## 23. Проверка статуса сервиса

Выполните:

```bash
sudo systemctl status server-monitor
```

Что произошло:

systemd показал состояние сервиса.

Ожидаемый результат:

В выводе должна быть строка:

```text
Active: active (running)
```

Для выхода из просмотра нажмите:

```text
q
```

Если статус `failed`:

Перейдите к разделу 27.

## 24. Просмотр логов

Показать последние логи:

```bash
sudo journalctl -u server-monitor -n 100 --no-pager
```

Что произошло:

Показаны последние 100 строк логов сервиса.

Ожидаемый результат:

Вы увидите запуск приложения или текст ошибки.

Смотреть логи в реальном времени:

```bash
sudo journalctl -u server-monitor -f
```

Что произошло:

Открыта живая лента логов.

Ожидаемый результат:

Новые сообщения будут появляться сразу.

Для выхода нажмите:

```text
Ctrl+C
```

Что искать в логах:

- `ERROR`;
- `Traceback`;
- `ModuleNotFoundError`;
- `Address already in use`;
- ошибки чтения интерфейсов;
- ошибки `ip`;
- ошибки `systemctl`;
- ошибки чтения температуры.

Важно:

Ошибки отдельных метрик не должны валить приложение. Например, если нет `vcgencmd`, температура может быть `n/a`, но сервис продолжит работать.

## 25. Финальная проверка работоспособности

Проверьте, что сервис активен:

```bash
sudo systemctl is-active server-monitor
```

Ожидаемый результат:

```text
active
```

Проверьте API:

```bash
curl http://127.0.0.1:8080/api/status
```

Ожидаемый результат:

JSON с текущим статусом.

Проверьте список метрик:

```bash
curl http://127.0.0.1:8080/api/metrics
```

Ожидаемый результат:

JSON со списком метрик.

Проверьте историю CPU:

```bash
curl "http://127.0.0.1:8080/api/history?metric=cpu&period=1h&step=raw"
```

Ожидаемый результат:

JSON с точками CPU.

Проверьте историю сети:

```bash
curl "http://127.0.0.1:8080/api/history?metric=net&period=1h&step=raw&interface=ppp0"
```

Ожидаемый результат:

JSON с точками `rx` и `tx`.

Проверьте встроенную справку:

```bash
curl http://127.0.0.1:8080/static/help.html
```

Ожидаемый результат:

HTML-фрагмент справки с разделами `О системе`, `Описание метрик`, `FAQ`.

Проверьте русскую справку и схему маршрутизации:

```bash
curl http://127.0.0.1:8080/static/help.ru.html
```

Что произошло:

Сервер вернул русскую версию встроенной справки.

```bash
curl http://127.0.0.1:8080/static/routing-overview.svg
```

Что произошло:

Сервер вернул SVG-картинку, которая отображается в разделе `Схема маршрутизации` внутри окна `Help`.

Откройте веб-интерфейс:

```text
http://SERVER_IP:8080
```

Ожидаемый результат:

Dashboard `Gateway Telemetry` с графиками, текущими статусами и кнопкой `Help`. Внутри `Help` должен быть раздел `Схема маршрутизации` с изображением gateway-схемы.

## 26. Диагностика: веб-интерфейс не открывается

Проверьте статус сервиса:

```bash
sudo systemctl status server-monitor
```

Ожидаемый результат:

```text
Active: active (running)
```

Если сервис не активен:

Переходите к разделу 27.

Проверьте, слушает ли приложение порт:

```bash
sudo ss -ltnp | grep 8080
```

Что произошло:

Команда ищет процесс, который слушает порт `8080`.

Ожидаемый результат:

Строка вида:

```text
LISTEN 0  ... 0.0.0.0:8080 ...
```

Если строки нет:

Приложение не слушает порт. Проверьте логи:

```bash
sudo journalctl -u server-monitor -n 100 --no-pager
```

Проверьте локальный API:

```bash
curl http://127.0.0.1:8080/api/status
```

Если локально работает, но с другого устройства не открывается:

Проблема в сети или firewall.

Проверьте IP сервера:

```bash
ip a
```

Проверьте firewall `ufw`:

```bash
sudo ufw status
```

Если `Status: active`, разрешите порт:

```bash
sudo ufw allow 8080/tcp
```

Что произошло:

Firewall разрешил входящие подключения на порт `8080`.

Ожидаемый результат:

После этого веб-интерфейс должен открыться по адресу `http://SERVER_IP:8080`.

## 27. Диагностика: сервис не стартует

Проверьте статус:

```bash
sudo systemctl status server-monitor
```

Что произошло:

Вы увидите краткую причину ошибки.

Покажите подробные логи:

```bash
sudo journalctl -u server-monitor -n 100 --no-pager
```

Если ошибка `ModuleNotFoundError`:

Зависимости не установлены.

Исправление:

```bash
/opt/server-monitor/venv/bin/pip install -r /opt/server-monitor/requirements.txt
```

Затем:

```bash
sudo systemctl restart server-monitor
```

Если ошибка `No module named server_monitor`:

systemd запускается не из той папки или проект скопирован не полностью.

Проверьте:

```bash
ls -la /opt/server-monitor/server_monitor
```

Проверьте unit-файл:

```bash
sudo cat /etc/systemd/system/server-monitor.service
```

В нем должно быть:

```text
WorkingDirectory=/opt/server-monitor
```

Если ошибка `Address already in use`:

Порт занят другим процессом.

Проверьте:

```bash
sudo ss -ltnp | grep 8080
```

Измените порт:

```bash
nano /opt/server-monitor/config.yaml
```

Например:

```yaml
web_port: 8090
```

Перезапустите:

```bash
sudo systemctl restart server-monitor
```

Если ошибка YAML:

Проверьте файл:

```bash
nano /opt/server-monitor/config.yaml
```

Важно:

В YAML отступы имеют значение. Для списка интерфейсов используйте такой формат:

```yaml
interfaces:
  - eth0
  - eth0.3
  - ppp0
```

## 28. Диагностика: нет данных на графиках

Подождите 1-2 минуты.

Что произошло:

Сборщик должен накопить несколько точек.

Проверьте API CPU:

```bash
curl "http://127.0.0.1:8080/api/history?metric=cpu&period=1h&step=raw"
```

Ожидаемый результат:

В JSON должен быть массив `points`.

Если массив пустой:

Проверьте логи:

```bash
sudo journalctl -u server-monitor -n 100 --no-pager
```

Проверьте API сети:

```bash
curl "http://127.0.0.1:8080/api/history?metric=net&period=1h&step=raw&interface=ppp0"
```

Если `rx` и `tx` пустые:

Это возможно сразу после старта. Для сетевой скорости нужны минимум два измерения.

Проверьте интерфейсы:

```bash
ip a
```

Если интерфейса нет:

Исправьте `/opt/server-monitor/config.yaml`.

Перезапустите сервис:

```bash
sudo systemctl restart server-monitor
```

Если температура показывает `n/a`:

Проверьте Raspberry Pi-команду:

```bash
vcgencmd measure_temp
```

Если команда не найдена:

```bash
sudo apt install -y libraspberrypi-bin
```

Если температура все равно недоступна:

Это не критично. Остальные графики должны работать.

## 29. Управление сервисом

Остановить сервис:

```bash
sudo systemctl stop server-monitor
```

Что произошло:

Мониторинг остановлен.

Ожидаемый результат:

История метрик в памяти потеряна.

Запустить сервис:

```bash
sudo systemctl start server-monitor
```

Что произошло:

Мониторинг запущен.

Ожидаемый результат:

Сервис снова собирает метрики с нуля.

Перезапустить сервис:

```bash
sudo systemctl restart server-monitor
```

Что произошло:

Сервис остановлен и запущен заново.

Ожидаемый результат:

История очищена, новые данные начинают собираться заново.

Проверить статус:

```bash
sudo systemctl status server-monitor
```

Что произошло:

Показано текущее состояние сервиса.

## 30. Обновление приложения

Остановите сервис:

```bash
sudo systemctl stop server-monitor
```

Что произошло:

Приложение остановлено.

Если проект установлен через Git, перейдите в папку:

```bash
cd /opt/server-monitor
```

Что произошло:

Вы перешли в папку проекта.

Скачайте изменения:

```bash
git pull
```

Что произошло:

Git обновил файлы проекта.

Если проект обновляется вручную:

Скопируйте новые файлы проекта в `/opt/server-monitor` тем же способом, которым копировали при установке.

Активируйте окружение:

```bash
source /opt/server-monitor/venv/bin/activate
```

Что произошло:

Активировано Python-окружение.

Обновите зависимости:

```bash
pip install -r /opt/server-monitor/requirements.txt
```

Что произошло:

pip установил или обновил нужные библиотеки.

Запустите сервис:

```bash
sudo systemctl start server-monitor
```

Что произошло:

Мониторинг снова запущен.

Проверьте статус:

```bash
sudo systemctl status server-monitor
```

Ожидаемый результат:

```text
Active: active (running)
```

## 31. Частые ошибки

### Ошибка `ModuleNotFoundError: fastapi`

Причина:

Python-библиотеки не установлены в виртуальное окружение.

Исправление:

```bash
/opt/server-monitor/venv/bin/pip install -r /opt/server-monitor/requirements.txt
```

Перезапустите:

```bash
sudo systemctl restart server-monitor
```

### Ошибка `Permission denied`

Причина:

Недостаточно прав на файлы проекта.

Исправление:

```bash
sudo chown -R $USER:$USER /opt/server-monitor
```

Если сервис запускается от `root`, ему обычно хватает прав на чтение.

### Ошибка `Address already in use`

Причина:

Порт уже занят другим процессом.

Проверка:

```bash
sudo ss -ltnp | grep 8080
```

Исправление:

Измените порт в конфиге:

```bash
nano /opt/server-monitor/config.yaml
```

Например:

```yaml
web_port: 8090
```

Перезапустите:

```bash
sudo systemctl restart server-monitor
```

### На dashboard `ppp0 down`

Причина:

VPN-интерфейс не поднят.

Проверка:

```bash
ip a
```

Проверка VPN-сервиса:

```bash
sudo systemctl status sstp-vpn.service
```

### На dashboard `temperature n/a`

Причина:

Температура недоступна через системные источники.

Проверка:

```bash
vcgencmd measure_temp
```

Если команда не найдена:

```bash
sudo apt install -y libraspberrypi-bin
```

### Нет даты обновления RU-списка

Причина:

Файл `/var/lib/ru-nft-last-update` отсутствует.

Проверка:

```bash
ls -la /var/lib/ru-nft-last-update
```

Если файла нет:

Это означает, что список еще не обновлялся или используется другой путь.

Исправление:

Укажите правильный путь в:

```bash
nano /opt/server-monitor/config.yaml
```

Поле:

```yaml
ru_update_file: /var/lib/ru-nft-last-update
```

## 32. Проверка после перезагрузки

Перезагрузите сервер:

```bash
sudo reboot
```

Что произошло:

Сервер перезагрузился.

Ожидаемый результат:

SSH-соединение оборвется.

Подождите 1-2 минуты и подключитесь снова:

```bash
ssh USERNAME@SERVER_IP
```

Проверьте сервис:

```bash
sudo systemctl status server-monitor
```

Ожидаемый результат:

```text
Active: active (running)
```

Откройте:

```text
http://SERVER_IP:8080
```

Ожидаемый результат:

Dashboard открывается.

Важно:

После перезагрузки старая история исчезнет. Это правильно, потому что данные хранятся только в памяти.

## 33. Полное удаление системы

Остановите сервис:

```bash
sudo systemctl stop server-monitor
```

Что произошло:

Сервис остановлен.

Отключите автозапуск:

```bash
sudo systemctl disable server-monitor
```

Что произошло:

Сервис удален из автозагрузки.

Удалите unit-файл:

```bash
sudo rm /etc/systemd/system/server-monitor.service
```

Что произошло:

Файл systemd-сервиса удален.

Перечитайте systemd:

```bash
sudo systemctl daemon-reload
```

Что произошло:

systemd забыл удаленный service-файл.

Удалите приложение:

```bash
sudo rm -rf /opt/server-monitor
```

Что произошло:

Удалены файлы проекта, конфиг и виртуальное окружение.

Ожидаемый результат:

Система мониторинга полностью удалена.

Важно:

Отдельные файлы исторических метрик удалять не нужно, потому что приложение не создает базу данных и не пишет историю на диск.

## 34. Итоговый результат

После успешного развертывания:

- сервис `server-monitor` запущен через systemd;
- веб-интерфейс доступен по адресу `http://SERVER_IP:8080`;
- открывается dashboard `Gateway Telemetry` в брендинге `Strat-tools`;
- встроенная справка доступна по кнопке `Help`;
- графики CPU, RAM, температуры и сети отображаются;
- интерфейсы `eth0`, `eth0.3`, `ppp0` отображаются отдельно;
- состояние VPN и default route видно на dashboard;
- история хранится только в памяти процесса;
- после перезапуска сервиса история очищается;
- файлы SQLite, PostgreSQL, InfluxDB или Prometheus не создаются.
