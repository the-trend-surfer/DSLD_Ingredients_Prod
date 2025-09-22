# Налаштування Google Sheets API

## 1. Створення Service Account

1. Йти на https://console.cloud.google.com/
2. Створити новий проект або використати існуючий
3. Увімкнути Google Sheets API:
   - APIs & Services → Library
   - Шукати "Google Sheets API"
   - Натиснути Enable

4. Створити Service Account:
   - APIs & Services → Credentials
   - Create Credentials → Service Account
   - Назвати: "DLSD-Sheets-Writer"
   - Ролі: Editor

5. Створити JSON ключ:
   - Натиснути на створений Service Account
   - Keys → Add Key → Create New Key → JSON
   - Завантажити файл

## 2. Встановлення файлу

1. Перемістити завантажений JSON файл у корінь проекту:
   ```
   D:\CODING\DLSD\service_account.json
   ```

2. Додати email з service account до Google Sheets:
   - Відкрити таблицю: https://docs.google.com/spreadsheets/d/1kOrSOPgn7IDdA170YJDRBQw4Wt2-Y8uX0PdvCfxY4qA
   - Share → додати email з service_account.json
   - Дати права Editor

## 3. Структура service_account.json

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "dlsd-sheets-writer@your-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

## 4. Встановлення залежностей

```bash
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

## 5. Тестування

Після налаштування запустити:
```bash
python test_sheets_integration.py
```

## 6. Результат

Система створить новий аркуш "Results_Table" з заголовками:
- A: Назва українською [Оригінальна назва]
- B: Джерело отримання біологічно активної речовини
- C: Активні сполуки
- D: Добова норма
- E: Джерела та цитати
- F: Метадані

Кожен оброблений інгредієнт буде автоматично записаний в новий рядок таблиці.