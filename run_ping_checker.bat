@echo off
chcp 65001 >nul
echo ===============================================
echo Exchange Server Ping Checker
echo ===============================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python с https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Устанавливаем зависимости если нужно
echo Проверка зависимостей...
pip install -q requests

echo.
echo Запуск проверки...
echo.

python main.py

echo.
echo ===============================================
echo Нажмите любую клавишу для выхода...
pause >nul
