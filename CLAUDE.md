# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Supplement Ingredient Evidence Collector** - автоматизована система для збору науково підтверджених даних про інгредієнти харчових добавок з використанням Google Sheets, OpenAI API та валідації джерел.

## Key Project Files

### Documentation
- `01_data_sources.md` - конфігурація джерел даних (Google Sheets)
- `02_project_constraints.md` - обмеження та правила проєкту
- `03_project_overview.md` - загальний огляд та цілі
- `04_system_prompt_json_schema.md` - системний промпт та JSON схема валідації
- `05_edge_cases_examples.md` - крайові випадки та приклади реалізації
- `progress.md` - відстеження прогресу розробки

## Development Commands

### Git Operations
```bash
git add .
git commit -m "description"
git push origin master
```

### Project Structure
- **Input:** Google Sheet ID `1kOrSOPgn7IDdA170YJDRBQw4Wt2-Y8uX0PdvCfxY4qA`
- **Ranges:** C2:C (інгредієнти), E2:E (синоніми англ/лат)
- **Output:** Results_Main sheet, JSONL/CSV files

## Core Architecture

### Main Components
1. **Google Sheets API Integration** - читання інгредієнтів та синонімів
2. **OpenAI API with JSON Schema** - структурований збір даних
3. **Citation Verification System** - перевірка точності цитат
4. **Multi-level Source Priority** - Level 1-4 довіри до джерел
5. **Batch Processing Pipeline** - обробка 6500+ інгредієнтів

### Colab Structure
Проєкт реалізується як Google Colab notebook з Cells 0-6:
- Cell 0: Config та автентифікація
- Cell 1: Google Sheets API setup
- Cell 2: OpenAI API integration
- Cell 3: Search and verification functions
- Cell 4: Batch processing
- Cell 5: Results export
- Cell 6: Quality assurance

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