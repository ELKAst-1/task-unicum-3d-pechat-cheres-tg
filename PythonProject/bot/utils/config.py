import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN")

ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'sementrepp')

# Google Integration (опционально)             не надо
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID')
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY')

# Включена ли синхронизация с Google Таблицей  не надо
USE_GOOGLE_SHEETS = bool(GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON)

# Статусы и их цвета для Google Таблицы (RGB в диапазоне 0–1)
STATUS_COLORS = {
    "В очереди": {"red": 1.0, "green": 1.0, "blue": 0.8},     # Светло-жёлтый
    "В работе": {"red": 1.0, "green": 0.92, "blue": 0.0},    # Жёлтый
    "Готово": {"red": 0.85, "green": 1.0, "blue": 0.85},     # Светло-зелёный
    "Архив": {"red": 0.93, "green": 0.93, "blue": 0.93},     # Светло-серый
}

# Заголовки таблицы (должны совпадать с логикой отправки)
SHEET_HEADERS = [
    "ID заявки",
    "Имя",
    "Фамилия",
    "Группа",
    "Цель печати",
    "Файл (имя)",
    "Статус",
    "Комментарий",
    "Дата создания",
    "Последнее обновление"
]

# Путь к листу (можно изменить, если у вас не 'Sheet1')
SHEET_NAME = os.getenv('GOOGLE_SHEET_NAME', 'Заявки')

# Глобальные списки (могут загружаться из БД или оставаться пустыми для динамики)
GROUPS = []
PRINT_PURPOSES = []