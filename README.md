# Exchange Server Ping & Geolocation Checker

## English

### Overview

This project checks:

- ICMP ping latency to exchange endpoints
- HTTP latency to exchange endpoints
- IP geolocation for resolved hosts
- summary recommendations based on detected server regions

The project is cross-platform:

- Windows
- Ubuntu / Linux

Main entry point:

- `main.py`

Configuration file:

- `settings.py`

Results folder:

- `results/`

### Project Structure

```text
.
├── main.py
├── settings.py
├── requirements.txt
└── results/
```

### Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python main.py
```

### Ubuntu Setup From Scratch

If you start from a clean Ubuntu machine, run:

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv iputils-ping
```

Clone the repository:

```bash
git clone https://github.com/Giane-t/Test-ping-for-perps.git
cd Test-ping-for-perps
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Run the checker:

```bash
python3 main.py
```

### Ubuntu One-Block Install And Run

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv iputils-ping
git clone https://github.com/Giane-t/Test-ping-for-perps.git
cd Test-ping-for-perps
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 main.py
```

### Output Files

All generated files are saved into `results/`:

- `ping_results_YYYYMMDD_HHMMSS.json`
- `ping_results_YYYYMMDD_HHMMSS.csv`
- `ping_summary_YYYYMMDD_HHMMSS.txt`

### Notes

- On Ubuntu, the `ping` command is provided by `iputils-ping`
- If ICMP is blocked by the remote host, HTTP latency may still work
- Exchange endpoints and timeouts are configured in `settings.py`

---

## Русский

### Описание

Проект проверяет:

- ICMP ping до серверов бирж
- HTTP-задержку до серверов
- геолокацию IP-адресов
- итоговые рекомендации по размещению серверов

Проект работает на:

- Windows
- Ubuntu / Linux

Основной файл запуска:

- `main.py`

Файл настроек:

- `settings.py`

Папка с результатами:

- `results/`

### Структура проекта

```text
.
├── main.py
├── settings.py
├── requirements.txt
└── results/
```

### Быстрый запуск

Установка зависимостей:

```bash
pip install -r requirements.txt
```

Запуск:

```bash
python main.py
```

### Установка На Ubuntu С Нуля

Если у вас чистая Ubuntu, выполните:

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv iputils-ping
```

Клонируйте репозиторий:

```bash
git clone https://github.com/Giane-t/Test-ping-for-perps.git
cd Test-ping-for-perps
```

Создайте и активируйте виртуальное окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Установите Python-зависимости:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Запустите проверку:

```bash
python3 main.py
```

### Ubuntu: Все Команды Одним Блоком

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv iputils-ping
git clone https://github.com/Giane-t/Test-ping-for-perps.git
cd Test-ping-for-perps
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 main.py
```

### Какие Файлы Получаются На Выходе

Все результаты сохраняются в `results/`:

- `ping_results_YYYYMMDD_HHMMSS.json`
- `ping_results_YYYYMMDD_HHMMSS.csv`
- `ping_summary_YYYYMMDD_HHMMSS.txt`

### Примечания

- На Ubuntu команда `ping` ставится пакетом `iputils-ping`
- Если ICMP заблокирован на стороне сервера, HTTP latency всё равно может работать
- Список бирж и таймауты настраиваются в `settings.py`
