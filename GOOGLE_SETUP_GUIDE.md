# Покрокове налаштування Google Sheets API

## Крок 1: Створення Google Cloud проекту

1. **Відкрити Google Cloud Console:**
   - Перейти на: https://console.cloud.google.com/
   - Увійти з Google акаунтом

2. **Створити новий проект:**
   - Натиснути на випадаючий список проектів (зверху)
   - "New Project"
   - Назвати: `DLSD-Ingredients-Project`
   - Натиснути "Create"

## Крок 2: Увімкнення Google Sheets API

1. **В Cloud Console:**
   - Меню ☰ → "APIs & Services" → "Library"

2. **Знайти та увімкнути API:**
   - Шукати: `Google Sheets API`
   - Натиснути на результат
   - Натиснути "ENABLE"

## Крок 3: Створення Service Account

1. **Перейти до Credentials:**
   - Меню ☰ → "APIs & Services" → "Credentials"

2. **Створити Service Account:**
   - Натиснути "+ CREATE CREDENTIALS"
   - Вибрати "Service account"

3. **Налаштування Service Account:**
   - Service account name: `dlsd-sheets-writer`
   - Service account ID: `dlsd-sheets-writer` (автоматично)
   - Description: `Writer for DLSD ingredients table`
   - Натиснути "CREATE AND CONTINUE"

4. **Надати ролі:**
   - Role: `Editor`
   - Натиснути "CONTINUE"
   - Натиснути "DONE"

## Крок 4: Створення JSON ключа

1. **Знайти створений Service Account:**
   - В списку Service Accounts знайти `dlsd-sheets-writer`
   - Натиснути на email адресу

2. **Створити ключ:**
   - Перейти на вкладку "KEYS"
   - Натиснути "ADD KEY" → "Create new key"
   - Вибрати "JSON"
   - Натиснути "CREATE"

3. **Завантажити файл:**
   - Автоматично завантажиться JSON файл
   - Перемістити його в: `D:\CODING\DLSD\service_account.json`

## Крок 5: Налаштування доступу до таблиці

1. **Скопіювати email з JSON:**
   - Відкрити файл `service_account.json`
   - Знайти поле `"client_email"`
   - Скопіювати значення (наприклад: `dlsd-sheets-writer@your-project.iam.gserviceaccount.com`)

2. **Надати доступ до Google Sheets:**
   - Відкрити таблицю: https://docs.google.com/spreadsheets/d/1kOrSOPgn7IDdA170YJDRBQw4Wt2-Y8uX0PdvCfxY4qA
   - Натиснути "Share" (Поділитися)
   - Вставити скопійований email
   - Вибрати роль: "Editor"
   - ЗНЯТИ галочку "Notify people" (не відправляти повідомлення)
   - Натиснути "Share"

## Крок 6: Встановлення Python бібліотек

```bash
cd D:\CODING\DLSD
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

## Крок 7: Тестування налаштування

```bash
cd D:\CODING\DLSD
python test_sheets_integration.py
```

**Очікуваний результат:**
```
✅ Аркуш Results_Table створено/знайдено
🔗 URL: https://docs.google.com/spreadsheets/d/1kOrSOPgn7IDdA170YJDRBQw4Wt2-Y8uX0PdvCfxY4qA
✅ Тестові дані успішно записані
```

## Структура service_account.json

Файл повинен мати таку структуру:
```json
{
  "type": "service_account",
  "project_id": "dlsd-ingredients-project-12345",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "dlsd-sheets-writer@dlsd-ingredients-project-12345.iam.gserviceaccount.com",
  "client_id": "123456789...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

## Можливі помилки та рішення

### Помилка: "Service account file not found"
- Перевірити, що файл знаходиться в: `D:\CODING\DLSD\service_account.json`
- Перевірити права доступу до файлу

### Помилка: "403 Forbidden"
- Перевірити, що Service Account email додано до Google Sheets з правами Editor
- Перевірити, що Google Sheets API увімкнено в проекті

### Помилка: "401 Unauthorized"
- Перевірити правильність JSON ключа
- Спробувати створити новий ключ

## Після успішного налаштування

Система буде автоматично:
1. Створювати аркуш "Results_Table" при першому запуску
2. Записувати результати обробки кожного інгредієнта
3. Зберігати всі 5 стовпчиків таблиці + метадані

**Посилання на результати:**
https://docs.google.com/spreadsheets/d/1kOrSOPgn7IDdA170YJDRBQw4Wt2-Y8uX0PdvCfxY4qA/edit#gid=0