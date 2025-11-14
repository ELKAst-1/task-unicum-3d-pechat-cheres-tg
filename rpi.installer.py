#!/usr/bin/env python3
import os
import sys
import subprocess
import getpass

def run(cmd, shell=True, check=True):
    return subprocess.run(cmd, shell=shell, check=check, text=True)

def main():
    if os.geteuid() == 0:
        print("❌ Не запускайте от root. Используйте обычного пользователя (например, pi).")
        sys.exit(1)

    user = getpass.getuser()
    project_dir = os.path.expanduser("~/3d-print-bot")
    python_project_dir = os.path.join(project_dir, "PythonProject")

    print("🔧 Шаг 1: Обновление системы...")
    run("sudo apt update && sudo apt upgrade -y")

    print("🔧 Шаг 2: Установка Python, Git и venv...")
    run("sudo apt install -y python3 python3-pip python3-venv git")

    print("🔧 Шаг 3: Клонирование репозитория...")
    if not os.path.exists(project_dir):
        run(f"git clone https://github.com/ELKAst-1/-.git {project_dir}")
    else:
        print(f"✅ Папка {project_dir} уже существует — пропускаем клонирование.")

    # Проверяем, есть ли PythonProject внутри
    if not os.path.exists(python_project_dir):
        print("⚠️  Папка PythonProject не найдена. Убедитесь, что структура репозитория верна.")
        print("   Ожидается: https://github.com/ELKAst-1/-/tree/main/PythonProject")
        sys.exit(1)

    venv_dir = os.path.join(python_project_dir, "venv")
    print("🔧 Шаг 4: Создание виртуального окружения...")
    if not os.path.exists(venv_dir):
        run(f"python3 -m venv {venv_dir}")
    run(f"{venv_dir}/bin/pip install --upgrade pip")

    print("🔧 Шаг 5: Установка зависимостей...")
    requirements = [
        "python-telegram-bot==20.7",
        "APScheduler",
        "pandas",
        "openpyxl"
    ]
    req_file = os.path.join(python_project_dir, "requirements.txt")
    with open(req_file, "w") as f:
        f.write("\n".join(requirements))
    run(f"{venv_dir}/bin/pip install -r {req_file}")

    print("🔧 Шаг 6: Создание run.sh...")
    run_script = os.path.join(python_project_dir, "run.sh")
    with open(run_script, "w") as f:
        f.write(f"""#!/bin/bash
cd {python_project_dir}
source venv/bin/activate
exec python3 main.py
""")
    run(f"chmod +x {run_script}")

    # .env в корне PythonProject
    env_path = os.path.join(python_project_dir, ".env")
    if not os.path.exists(env_path):
        print("📝 Создание шаблона .env")
        with open(env_path, "w") as f:
            f.write("# TELEGRAM_BOT_TOKEN=ваш_токен_бота\n")
            f.write("# ADMIN_CHAT_IDS=123456789\n")
    else:
        print("✅ Файл .env уже существует.")

    print("🔧 Шаг 7: Настройка systemd...")
    service_content = f"""[Unit]
Description=3D Print Telegram Bot
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={python_project_dir}
EnvironmentFile={env_path}
ExecStart={run_script}
Restart=always
RestartSec=90
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    with open("/tmp/3d-print-bot.service", "w") as f:
        f.write(service_content)
    run("sudo mv /tmp/3d-print-bot.service /etc/systemd/system/")
    run("sudo systemctl daemon-reload")
    run("sudo systemctl enable 3d-print-bot.service")
    run("sudo systemctl start 3d-print-bot.service")

    print("\n✅ Установка завершена!")
    print(f"\n📝 Отредактируйте .env:")
    print(f"   nano {env_path}")
    print("\n📄 Команды:")
    print("   sudo systemctl status 3d-print-bot")
    print("   sudo journalctl -u 3d-print-bot -f")

if __name__ == "__main__":
    main()
