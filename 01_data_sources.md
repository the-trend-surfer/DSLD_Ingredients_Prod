# Supplement Ingredient Evidence Collector — Data Sources

**Version:** v1.0 (2025‑09‑19)
**Owner:** Project "Supplement Ingredient Evidence Collector"

---

## Input File (Google Sheets)

* **INGREDIENTS\_SHEET\_ID** = `1kOrSOPgn7IDdA170YJDRBQw4Wt2-Y8uX0PdvCfxY4qA`
* **INGREDIENTS\_SHEET\_NAME** = `Ingredients_Main`
* **INGREDIENTS\_RANGE** = `C2:C` → основні імена інгредієнтів (українською або латинською, іноді абревіатури)
* **SYNONYMS\_EN\_LAT\_RANGE** = `E2:E` → англійські/латинські синоніми (через кому)
* **SYNONYMS\_UK\_RANGE** = *не використовується*

---

## Використання у пошуку

1. **Базовий пошук** завжди запускається по значенню з `INGREDIENTS_RANGE`.
2. **Додатково** обов'язково запускається пошук за синонімами з `SYNONYMS_EN_LAT_RANGE`.

   * Якщо в основному полі лише абревіатура → результати будуть збагачені пошуком по повних формах у синонімах.
   * Усі результати фіксуються в `search_trace` з позначкою `query_type = ingredient | synonym`.
3. Після збору результатів:

   * В JSON заповнюється поле `synonyms[]` з даними з обох колонок (C + E).
   * У `provenance` фіксується, чи був використаний синонім для успішного пошуку.

---

## Colab Config (Cell @title Config)

```python
SHEET_ID_ING = "1kOrSOPgn7IDdA170YJDRBQw4Wt2-Y8uX0PdvCfxY4qA"
SHEET_NAME_ING = "Ingredients_Main"
RANGE_INGREDIENTS = "C2:C"
RANGE_SYNONYMS_EN_LAT = "E2:E"
```

---

## Правило якості

* **Завжди** перевіряти і **ім'я**, і **синоніми**.
* Якщо результати знайдені лише за синонімом → це явно зазначається у `search_trace.notes` (наприклад: *"main name only acronym, results retrieved via synonym: full term"*).
* Якщо і ім'я, і синоніми не дали результату → `result_status = not_found`.