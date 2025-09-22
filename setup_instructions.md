# Setup Instructions для локального запуску

## 1. Google Sheets API Setup

### Крок 1: Створення Google Cloud Project
1. Відкрийте [Google Cloud Console](https://console.cloud.google.com/)
2. Створіть новий проєкт або виберіть існуючий
3. Увімкніть Google Sheets API та Google Drive API

### Крок 2: Створення Service Account
1. Перейдіть до "IAM & Admin" → "Service Accounts"
2. Натисніть "Create Service Account"
3. Введіть назву (наприклад, "dlsd-sheets-access")
4. Натисніть "Create and Continue"
5. Надайте роль "Editor" або "Viewer" (залежно від потреб)

### Крок 3: Генерація JSON ключа
1. Знайдіть створений service account
2. Натисніть на нього → вкладка "Keys"
3. "Add Key" → "Create New Key" → "JSON"
4. Збережіть файл як `credentials.json` у корені проєкту

### Крок 4: Надання доступу до Google Sheet
1. Відкрийте ваш Google Sheet: `1kOrSOPgn7IDdA170YJDRBQw4Wt2-Y8uX0PdvCfxY4qA`
2. Натисніть "Share"
3. Додайте email service account (знаходиться у `credentials.json` → `client_email`)
4. Надайте права "Editor"

## 2. Environment Setup

### Створіть `.env` файл:
```bash
cp .env.example .env
```

### Заповніть `.env`:
```
OPENAI_API_KEY=sk-your-openai-key-here
NCBI_EMAIL=your-email@example.com
```

## 3. Installation

```bash
# Встановіть залежності
pip install -r requirements.txt

# Перевірте конфігурацію
python -c "from config import validate_config; validate_config()"

# Тест Google Sheets підключення
python -c "from auth import setup_google_sheets; setup_google_sheets()"
```

## 4. Структура файлів

```
DLSD/
├── credentials.json          # Google Service Account (НЕ КОМІТЬ!)
├── .env                     # API ключі (НЕ КОМІТЬ!)
├── requirements.txt         # Python залежності
├── config.py               # Конфігурація
├── auth.py                 # Автентифікація
├── main.py                 # Головний скрипт
├── modules/                # Модулі коду
│   ├── search.py          # Пошук даних
│   ├── openai_client.py   # OpenAI інтеграція
│   └── processors.py      # Обробка даних
└── output/                # Результати
```

## 5. Security

Додайте до `.gitignore`:
```
credentials.json
.env
output/
backup/
*.log
```