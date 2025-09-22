# 🎯 DLSD PROJECT MANAGER - Керівництво користувача

## 🚀 Швидкий старт

### Найпростіший спосіб - Launcher
```bash
python launcher.py
```

Виберіть один з готових шаблонів:
- 🧪 **Test run** - 5 інгредієнтів для тестування
- 📝 **Small batch** - 50 інгредієнтів
- 📚 **Medium batch** - 200 інгредієнтів
- 🏭 **Large batch** - 500 інгредієнтів

## 🎛️ Основні команди

### 1. Інтерактивний режим
```bash
python project_manager.py --interactive
```

### 2. Прямий запуск з параметрами
```bash
# Обробити рядки 1-100
python project_manager.py --start 1 --end 100

# З конкретною AI моделлю
python project_manager.py --start 1 --end 50 --model claude
```

### 3. Продовження існуючого проєкту
```bash
python project_manager.py --resume
```

### 4. Dashboard only
```bash
# Web dashboard (рекомендується)
python project_manager.py --dashboard-only --dashboard web

# Console dashboard
python project_manager.py --dashboard-only --dashboard console
```

## 🔗 Паралельна обробка (кілька комп'ютерів)

### Налаштування діапазонів
```bash
python launcher.py --parallel
```

Система автоматично розподілить інгредієнти між комп'ютерами:

**Приклад для 3 комп'ютерів:**
- 💻 Комп'ютер 1: `python project_manager.py --start 1 --end 2000`
- 💻 Комп'ютер 2: `python project_manager.py --start 2001 --end 4000`
- 💻 Комп'ютер 3: `python project_manager.py --start 4001 --end 6500`

## 📊 Real-time Dashboard

Dashboard автоматично запускається під час обробки і показує:

```
🎯 DLSD PROJECT MANAGER - REAL-TIME DASHBOARD
======================================================================
📊 Project: DLSD_20250921_173045
🤖 AI Model: openai
📅 Started: 2025-09-21 17:30:45
----------------------------------------------------------------------
📈 Progress: [████████████████████░░░░░░░░░░░░░░░░░░░░] 50.2%
----------------------------------------------------------------------
📋 Range: rows 1-100
🔢 Total items: 100
✅ Processed: 50
🎯 Successful: 47 (94.0%)
❌ Errors: 3 (6.0%)
⏭️  Skipped: 0
----------------------------------------------------------------------
⏱️  Elapsed: 1:25:30
⚡ Avg time/item: 0:01:42
⏰ Estimated remaining: 1:25:00
🎯 ETA: 2025-09-21 19:20:15
----------------------------------------------------------------------
🟢 Recent successes:
   ✅ Vitamin C
   ✅ Magnesium
   ✅ Omega-3
🔴 Recent failures:
   ❌ Unknown compound: No valid sources found
----------------------------------------------------------------------
💡 Press Ctrl+C to stop processing
📝 State auto-saved at: 2025-09-21T18:55:30.123456
```

## 🔄 Resume функціональність

### Автоматичне збереження стану
Система автоматично зберігає стан у `project_state.json`:
- ✅ Поточний прогрес
- ✅ Успішні та невдалі інгредієнти
- ✅ Налаштування проєкту
- ✅ Статистика часу

### Відновлення після переривання
```bash
# Якщо процес був перерваний, просто запустіть:
python project_manager.py --resume

# Або через інтерактивний режим:
python project_manager.py --interactive
# Виберіть "Resume existing project"
```

## 📁 Структура файлів

```
D:\CODING\DLSD\
├── project_manager.py      # Основна система управління
├── launcher.py             # Швидкий запуск
├── project_state.json      # Стан поточного проєкту
├── output/
│   ├── PROJECT_RESULTS_DLSD_20250921_173045.json
│   └── PRODUCTION_RESULTS_20250921_173714.json
└── PROJECT_MANAGER_GUIDE.md
```

## 🛠️ Контроль помилок

### Типи помилок
- **Processing errors** - помилки обробки конкретного інгредієнта
- **API errors** - помилки зв'язку з зовнішніми сервісами
- **Network errors** - проблеми з мережею

### Автоматичний retry
- ✅ Автоматичне збереження стану після кожного інгредієнта
- ✅ Можливість продовження з місця зупинки
- ✅ Детальний лог помилок

### Стратегія обробки помилок
1. **Помилка обробки інгредієнта** → записується в failed_ingredients, продовжується обробка
2. **Системна помилка** → збереження стану, можливість resume
3. **Ctrl+C переривання** → збереження стану, показ статистики

## 📊 Моніторинг прогресу

### Параметри відстеження
- **Progress percentage** - відсоток виконання
- **Success rate** - відсоток успішних обробок
- **Error rate** - відсоток помилок
- **Average time per ingredient** - середній час обробки
- **ETA** - очікуваний час завершення

### Статистика в реальному часі
- 🔄 Оновлення кожні 5 секунд
- 📊 Progress bar з візуальним відображенням
- 📈 Trend analysis для оцінки швидкості
- ⏰ Точні прогнози часу завершення

## 🎯 Оптимізація продуктивності

### Рекомендації по розміру batch
- **Тестування**: 5-10 інгредієнтів
- **Розробка**: 50-100 інгредієнтів
- **Виробництво**: 200-500 інгредієнтів
- **Масштабування**: розподіл між кількома комп'ютерами

### Вибір AI моделі
- **OpenAI** (рекомендується) - найкраща стабільність та якість
- **Claude** - альтернатива для розробки
- **Gemini** - експериментальна підтримка

## 🚨 Troubleshooting

### Часті проблеми

**1. "No existing project found"**
```bash
# Створіть новий проєкт
python launcher.py
# Або
python project_manager.py --start 1 --end 10
```

**2. "Failed to read ingredients"**
```bash
# Перевірте Google Sheets доступ
# Переконайтесь що є інтернет з'єднання
```

**3. "Dashboard not updating"**
```bash
# Перезапустіть з --dashboard
python project_manager.py --dashboard
```

**4. Процес "завис"**
```bash
# Ctrl+C для зупинки
# Потім resume для продовження
python project_manager.py --resume
```

### Діагностика
```bash
# Перевірка стану проєкту
python -c "import json; print(json.load(open('project_state.json')))"

# Перевірка останніх результатів
ls -la output/
```

## 🎉 Успішне завершення

Після завершення обробки:
- ✅ Фінальна статистика виводиться в консоль
- ✅ Результати зберігаються в `output/PROJECT_RESULTS_*.json`
- ✅ Дані записуються в Google Sheets
- ✅ `project_state.json` залишається для історії

## 📞 Підтримка

У разі проблем:
1. Перевірте `project_state.json` на наявність помилок
2. Запустіть dashboard для діагностики: `python project_manager.py --dashboard`
3. Використайте test run для перевірки: `python launcher.py` → вибрати "1"