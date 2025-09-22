# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Supplement Ingredient Evidence Collector** - автоматизована система для збору науково підтверджених даних про інгредієнти харчових добавок з використанням Google Sheets, OpenAI API та валідації джерел.

## Key Project Files

### Reference Documentation
- `01_data_sources.md` - конфігурація джерел даних (Google Sheets)
- `02_project_constraints.md` - обмеження та правила проєкту
- `03_project_overview.md` - загальний огляд та цілі
- `04_system_prompt_json_schema.md` - системний промпт та JSON схема валідації
- `05_edge_cases_examples.md` - крайові випадки та приклади реалізації
- `DLSD_Evidence_Collector.ipynb` - референсний Colab notebook
- `progress.md` - відстеження прогресу розробки

### Production Code Structure
- `modules/` - API clients та утиліти
  - `sheets_reader.py` - читання Google Sheets
  - `sheets_writer.py` - запис результатів
  - `multi_ai_client.py` - OpenAI/Claude/Gemini clients
  - `ncbi_client.py` - NCBI E-utilities API
  - `gemini_google_search.py` - Google Search через Gemini
- `processes/` - бізнес-логіка
  - `pipeline.py` - основний pipeline обробки
  - `schemas.py` - JSON Schema валідація
  - `ai_prompts.py` - системні промпти
  - `source_policy.py` - L1-L4 політика джерел
  - `normalizer.py` - нормалізація даних
- `run_production.py` - простий production runner
- `project_manager.py` - інтерактивний менеджер з dashboard

## Development Commands

### Production Run
```bash
# Interactive mode with dashboard
python project_manager.py --interactive

# Direct run with range
python project_manager.py --start 1 --end 100 --model openai

# Resume existing project
python project_manager.py --resume

# Simple production run
python run_production.py --test  # First 10 ingredients
python run_production.py --limit 100  # First 100 ingredients
python run_production.py  # All 6500+ ingredients
```

### Git Operations
```bash
git add .
git commit -m "description"
git push origin master
```

### Project Structure
- **Input:** Google Sheet ID `1kOrSOPgn7IDdA170YJDRBQw4Wt2-Y8uX0PdvCfxY4qA`
- **Ranges:** C2:C (інгредієнти), E2:E (синоніми англ/лат)
- **Output:** Results_Main sheet, JSONL/CSV files, output/ directory

## CRITICAL: Структура Google Sheets Results_Main

### 📊 Стовпчики таблиці:

| Стовпчик | Назва поля | Формат/Джерело | Приклад |
|----------|------------|----------------|---------|
| **A** | **Назва українською** | AI переклад: `Українська (English)` | `Вітамін С (Vitamin C)` |
| **B** | **Джерело отримання** | Витягуємо з PubMed/статей | `Соя, насіння (Glycine max)` |
| **C** | **Активні сполуки** | Витягуємо з PubMed/статей | `β-ситостерин (β-Sitosterol)` |
| **D** | **Дозування** | Витягуємо з PubMed/статей | `500 mg`, `1-3 g` |
| **E** | **Рівень доказів** | Автоматично L1-L4 | `L1`, `L2` |
| **F** | **Цитати** | Точні цитати з статей | `improves immune function` |
| **G** | **Джерела** | URL PubMed/наукових джерел | `https://pubmed.ncbi.nlm.nih.gov/123` |

### 🔥 КРИТИЧНІ ПРАВИЛА:

**Стовпчик A - Назва:**
- ✅ **ТІЛЬКИ** AI переклад у форматі `Українська (English)`
- ❌ **НЕ шукати** назви в Google/пошуковиках
- ❌ **НЕМАЄ** окремого стовпчика для латинської назви
- ✅ Приклади: `Гінкго білоба (Ginkgo Biloba)`, `АХЦЦ (AHCC)`

**Стовпчики B-G - Дані:**
- ✅ Витягуємо **ТІЛЬКИ** з PubMed/NCBI/наукових статей
- ✅ AI аналізує знайдені статті та витягує інформацію
- ❌ **НЕ шукаємо** у випадкових сайтах
- ✅ Цитати = точні фрази з тексту статей, НЕ URL

### 📋 Алгоритм обробки:
1. **Стовпчик A**: AI перекладає `English` → `Українська (English)`
2. **Стовпчики B-D**: Окремі Gemini пошуки з L1-L4 ранжуванням
3. **Стовпчики E-G**: Автоматично з найкращих джерел
4. **Валідація**: Перевіряємо цитати та джерела
5. **Запис**: У Google Sheets за форматом

## 🔍 Детальна механіка пошуку по стовпчиках

### **Стовпчик A - Назва українською**
```
AI переклад → "Українська назва (English original)"
❌ БЕЗ пошуку в Google/інтернеті!
✅ Тільки AI переклад
```

### **Стовпчик B - Джерело отримання**
```
1. Gemini пошук: ("IngrediENT" OR "synonym1" OR "synonym2") biological source extraction "derived from"
2. L1-L4 фільтрація результатів (NIH→Nature→Examine→Commercial)
3. AI аналіз джерел за пріоритетом L1→L2→L3→L4
4. Витягує: організм, частина рослини/тварини, спосіб отримання
```

### **Стовпчик C - Активні сполуки**
```
1. Gemini пошук: ("IngrediENT" OR "synonym1" OR "synonym2") active compounds chemical composition
2. L1-L4 фільтрація результатів
3. AI аналіз джерел за пріоритетом L1→L2→L3→L4
4. Витягує: хімічні назви, концентрації, біоактивні речовини
```

### **Стовпчик D - Дозування**
```
1. Gemini пошук: ("IngrediENT" OR "synonym1" OR "synonym2") dosage clinical recommendations "mg per day"
2. L1-L4 фільтрація результатів
3. AI аналіз джерел за пріоритетом L1→L2→L3→L4
4. Витягує: ТІЛЬКИ числа + одиниці (500 mg, 1-3 g)
```

### **Стовпчики E, F, G - Автоматичне заповнення**
```
E. Рівень доказів → L1/L2/L3/L4 на основі найкращого знайденого джерела
F. Цитати → точні фрази з тексту найкращих джерел (НЕ URL!)
G. Джерела → URL найкращих L1-L4 джерел
```

## 🏆 L1-L4 Ранжування джерел

### **Level 1 (L1) - Найвища довіра**
```
- nih.gov, ncbi.nlm.nih.gov, pubmed.ncbi.nlm.nih.gov
- efsa.europa.eu, fda.gov, who.int
- ods.od.nih.gov
```

### **Level 2 (L2) - Високоякісні наукові джерела**
```
- nature.com, science.org, sciencedirect.com
- springer.com, wiley.com, tandfonline.com
- jamanetwork.com, nejm.org
- wikipedia.org
```

### **Level 3 (L3) - Надійні наукові ресурси**
```
- examine.com, consumerlab.com, cochrane.org
- uptodate.com, medlineplus.gov, mayoclinic.org
```

### **Level 4 (L4) - Потребують перевірки**
```
- Виробники добавок, комерційні сайти
- Блоги, форуми, особисті сайти
```

## 🔄 Процес для одного інгредієнта:
**Кожен стовпчик = окремий цикл: Gemini Google Search → L1-L4 фільтрація → AI аналіз пріоритетних джерел**

## Production vs Reference Implementation

### Current Production (Python)
- **Модульна архітектура** - розділені modules/ та processes/
- **Multi-AI support** - OpenAI/Claude/Gemini з automatic fallback
- **NCBI integration** - реальні наукові джерела через E-utilities API
- **Interactive management** - project_manager.py з real-time dashboard
- **Resume capability** - збереження стану та продовження з зупинки
- **Batch processing** - ефективна обробка 6500+ інгредієнтів

### Reference Implementation (Colab)
- **DLSD_Evidence_Collector.ipynb** - оригінальна логіка в notebook форматі
- **Cells 0-6** - структурований workflow як референс
- **Документація** - детальні правила в `.md` файлах
- **JSON Schema** - сувора валідація структури даних

## Core Architecture

### Main Components
1. **Google Sheets API Integration** - читання інгредієнтів та синонімів
2. **Multi-AI API (OpenAI/Claude/Gemini)** - структурований збір даних
3. **NCBI E-utilities Integration** - надійні наукові джерела
4. **Citation Verification System** - перевірка точності цитат
5. **Multi-level Source Priority** - Level 1-4 довіри до джерел
6. **Production Pipeline** - масова обробка 6500+ інгредієнтів

### Hybrid Structure
**Документація (Reference):**
- `01_data_sources.md` - джерела даних та Google Sheets конфігурація
- `02_project_constraints.md` - обмеження та правила проєкту
- `03_project_overview.md` - загальний огляд та цілі
- `04_system_prompt_json_schema.md` - системний промпт та JSON схема
- `05_edge_cases_examples.md` - крайові випадки та приклади
- `DLSD_Evidence_Collector.ipynb` - референсний Colab notebook

**Production Code:**
- `modules/` - API clients та утиліти
  - `sheets_reader.py` - читання Google Sheets
  - `sheets_writer.py` - запис результатів
  - `multi_ai_client.py` - OpenAI/Claude/Gemini clients
  - `ncbi_client.py` - NCBI E-utilities API
  - `gemini_google_search.py` - Google Search через Gemini
- `processes/` - бізнес-логіка
  - `pipeline.py` - основний pipeline обробки
  - `schemas.py` - JSON Schema валідація
  - `ai_prompts.py` - системні промпти
  - `source_policy.py` - L1-L4 політика джерел
  - `normalizer.py` - нормалізація даних
- `run_production.py` - production runner
- `project_manager.py` - інтерактивний менеджер з dashboard

## 🔥 Critical Technical Solutions

### Gemini Google Search з grounding_metadata

**Проблема:** Gemini Google Search не використовував реальні URL з grounding_metadata, натомість намагався парсити текст відповіді.

**Рішення:** Реалізовано правильне отримання URL з `response.candidates[0].grounding_metadata.grounding_chunks`:

```python
# modules/gemini_google_search.py - GeminiGoogleSearcher
def search_for_column_b_source(self, ingredient: str, synonyms: Optional[List[str]] = None):
    response = self.model.generate_content(query_text)

    # ✅ Правильне отримання grounding metadata
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
            grounding_data = candidate.grounding_metadata

            if hasattr(grounding_data, 'grounding_chunks') and grounding_data.grounding_chunks:
                for chunk in grounding_data.grounding_chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        sources.append({
                            "url": chunk.web.uri,           # ✅ Реальний URL
                            "title": chunk.web.title,       # ✅ Реальний title
                            "content": response.text,
                            "type": "gemini_search"
                        })
```

**Результат:**
- ✅ 6-11 реальних джерел на кожен пошук (B/C/D стовпчики)
- ✅ Автентичні URL з nih.gov, frontiersin.org, oregonstate.edu
- ✅ Повна інтеграція з citation collection system
- ✅ Vertex AI redirect URLs (очікувана поведінка)

**Тестування:**
```bash
python test_gemini_grounding.py  # Демонструє роботу grounding_metadata
```

## Key Constraints

### Strict Requirements
- **No hallucinations** - тільки реальні дані з джерел
- **JSON Schema compliance** - сувора відповідність схемі
- **Citation verification** - exact match перевірка цитат
- **Source domain restrictions** - тільки дозволені домени
- **Progressive validation** - прогрес через `progress.md`

### Allowed Domains
- `*.nih.gov`, `*.ncbi.nlm.nih.gov`
- `efsa.europa.eu`
- `examine.com`, `consumerlab.com`
- `sciencedirect.com`, `nature.com`

## Source Priority Levels

1. **Level 1** - Систематичні огляди, офіційні регулятори (EFSA, FDA, NIH)
2. **Level 2** - RCT у рецензованих журналах
3. **Level 3** - Рецензовані журнали 2-3 квартилі
4. **Level 4** - Виробники, етикетки (needs_human_review=true)

## JSON Output Schema

Обов'язкові поля: `ingredient_name_uk`, `ingredient_name_lat`, `result_status`, `sources`, `citations`, `provenance`

Статуси: `found`, `partial`, `not_found`, `ambiguous`, `contradictory`

## Quality Assurance

- Всі зміни логуються в `progress.md`
- Citation exact match verification
- 1% manual verification вибірки
- Edge cases handling documented

## Development Workflow

1. Внести зміни в код
2. Оновити `progress.md` з деталями
3. Тестувати на малій вибірці (5-10 інгредієнтів)
4. Валідувати JSON output
5. Commit та push до GitHub