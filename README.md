# DLSD Evidence Collector

Автоматизована система для збору науково підтверджених даних про інгредієнти харчових добавок.

## 🚀 Швидкий старт

### 1. Встановлення
```bash
pip install -r requirements.txt
```

### 2. Налаштування
```bash
# Налаштування конфігурації та тестування з'єднань
python main.py setup --email your-email@example.com
```

### 3. Тестування
```bash
# Тест на 5 інгредієнтах
python main.py test --count 5
```

### 4. Повна обробка
```bash
# Обробка всіх інгредієнтів
python main.py process
```

## 📋 Команди

### Setup
```bash
python main.py setup --email your@email.com
```
Налаштування та перевірка конфігурації

### Test
```bash
python main.py test --count 10
```
Тестування на обмеженій кількості інгредієнтів

### Process
```bash
python main.py process
```
Повна обробка всіх інгредієнтів з Google Sheets

### Export
```bash
python main.py export --format csv --output results.csv
python main.py export --format jsonl --output results.jsonl
```
Експорт результатів у різних форматах

## 🔧 Конфігурація

### Файли конфігурації:
- `.env` - API ключі та налаштування
- `credentials.json` - Google Service Account
- `config.py` - основні параметри

### Необхідні API ключі:
- **AI Models** (потрібен хоча б один):
  - OpenAI API (GPT-4o, GPT-4o-mini)
  - Claude API (Sonnet 4, Claude 3.5)
  - Gemini API (Gemini 2.5 Flash Lite, 1.5 Flash)
- **Google Sheets API** - для читання інгредієнтів
- **NCBI API** - для доступу до PubMed (опційно)
- **NCBI Email** - для доступу до PubMed

## 📁 Структура проєкту

```
DLSD/
├── main.py                 # CLI інтерфейс
├── config.py              # Конфігурація
├── auth.py                # Автентифікація
├── requirements.txt       # Залежності
├── modules/               # Основні модулі
│   ├── multi_ai_client.py # Multi-AI інтеграція
│   ├── search.py         # Пошук джерел
│   └── processors.py     # Batch обробка
├── output/               # Результати
└── setup_instructions.md # Детальні інструкції
```

## 🎯 Особливості

- **Multi-AI support** - OpenAI, Claude, Gemini з автоматичним fallback
- **Multi-source search** - PubMed, Google Scholar
- **Source priority** - рівні довіри 1-4
- **Intelligent model selection** - вибір найкращої моделі для кожного запиту
- **Batch processing** - обробка 6500+ інгредієнтів
- **Error handling** - retry логіка та збереження проміжних результатів
- **Multiple export formats** - CSV, JSON, JSONL

## 📊 Формат результатів

Кожен результат містить:
- Українську та латинську назви
- Джерело отримання
- Активні сполуки
- Наукові дослідження
- Рівень доказів (1-4)
- Джерела та посилання

## 🔒 Security

- API ключі зберігаються в `.env` (не комітяться)
- Google credentials в `credentials.json` (не комітяться)
- Додайте до `.gitignore`: `.env`, `credentials.json`, `output/`

## 🐛 Troubleshooting

### Google Sheets помилки:
1. Перевірте `credentials.json`
2. Переконайтеся, що service account має доступ до sheet
3. Перевірте Sheet ID в `config.py`

### OpenAI API помилки:
1. Перевірте `OPENAI_API_KEY` в `.env`
2. Перевірте баланс акаунту
3. Перевірте rate limits

### NCBI/PubMed помилки:
1. Встановіть правильний email в `NCBI_EMAIL`
2. Дотримуйтесь rate limiting (макс. 3 запити/сек)

## 📈 Моніторинг прогресу

Система автоматично:
- Зберігає проміжні результати кожні 10 інгредієнтів
- Логує помилки в окремі файли
- Показує прогрес у real-time
- Дозволяє відновлення після збоїв