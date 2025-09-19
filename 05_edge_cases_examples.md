# Supplement Ingredient Evidence Collector — Edge Cases (Продовження)

**Document type:** Extension to Prompt & JSON Schema
**Version:** v1.2 (2025‑09‑19)
**Owner:** Project "Supplement Ingredient Evidence Collector"

---

## 8) Типові крайові випадки (продовження)

* **Суперечні RCT (рандомізовані контрольовані дослідження)** → `result_status = "contradictory"`.

  * Мінімум 2 окремі `citations` з різними висновками щодо ефективності чи дози.
  * Обов'язково вказати джерела з різних журналів/авторів.
  * У `search_trace.notes` пояснити характер суперечностей (наприклад: «одне дослідження показало зниження артеріального тиску, інше – відсутність ефекту»).

**Приклад JSON:**

```json
{
  "ingredient_name_uk": "Екстракт зеленого чаю",
  "ingredient_name_lat": "Camellia sinensis",
  "result_status": "contradictory",
  "daily_dose": null,
  "citations": [
    {
      "type": "daily_dose",
      "title": "RCT on green tea extract and blood pressure",
      "journal_or_publisher": "Am J Clin Nutr",
      "year": 2018,
      "url": "https://...",
      "doi": "10.1093/ajcn/nqy123",
      "exact_quote": "Green tea extract significantly reduced systolic blood pressure...",
      "page_or_section": "p. 4",
      "source_priority": 2,
      "needs_human_review": false
    },
    {
      "type": "daily_dose",
      "title": "RCT: no effect of green tea extract on blood pressure",
      "journal_or_publisher": "Nutrients",
      "year": 2020,
      "url": "https://...",
      "doi": "10.3390/nu12041111",
      "exact_quote": "No significant differences were found between treatment and placebo groups...",
      "page_or_section": "Table 2",
      "source_priority": 2,
      "needs_human_review": false
    }
  ],
  "search_trace": [
    { "engine": "pubmed", "query": "green tea extract blood pressure RCT", "results_checked": 20, "notes": "contradictory results across two RCTs" }
  ],
  "provenance": { "colab_cell": "Cell EdgeCase", "model": "GPT-5", "retrieved_at": "2025-09-19T12:30:00Z" }
}
```

---

* **Дані про сполуки без кількісних значень** → заповнюється тільки `name`, `iupac/cas` (якщо є), `concentration = null`.

**Приклад JSON:**

```json
{
  "ingredient_name_uk": "Кора верби",
  "ingredient_name_lat": "Salix alba",
  "active_compounds": [
    { "name": "саліцин", "iupac": null, "cas": "138-52-3", "concentration": null }
  ],
  "result_status": "found",
  "citations": [
    {
      "type": "active_compounds",
      "title": "Willow bark constituents",
      "journal_or_publisher": "Phytochemistry",
      "year": 2015,
      "url": "https://...",
      "doi": "10.1016/j.phytochem.2015.03.001",
      "exact_quote": "Willow bark contains salicin among other phenolic glycosides...",
      "page_or_section": "p. 112",
      "source_priority": 2,
      "needs_human_review": false
    }
  ],
  "provenance": { "colab_cell": "Cell EdgeCase", "model": "GPT-5", "retrieved_at": "2025-09-19T12:35:00Z" }
}
```

---

* **Діапазон доз** → використовувати `min_value`/`max_value` замість одного `value`.

**Приклад JSON:**

```json
{
  "ingredient_name_uk": "Магній",
  "ingredient_name_lat": "Magnesium",
  "daily_dose": {
    "recommended": { "min_value": 300, "max_value": 400, "unit": "мг/день" },
    "upper_limit": null,
    "evidence_type": "guideline"
  },
  "result_status": "found",
  "citations": [
    {
      "type": "daily_dose",
      "title": "EFSA Scientific Opinion on Magnesium",
      "journal_or_publisher": "EFSA",
      "year": 2017,
      "url": "https://...",
      "doi": null,
      "exact_quote": "The recommended daily intake of magnesium is 300–400 mg per day...",
      "page_or_section": "p. 15",
      "source_priority": 1,
      "needs_human_review": false
    }
  ],
  "provenance": { "colab_cell": "Cell EdgeCase", "model": "GPT-5", "retrieved_at": "2025-09-19T12:40:00Z" }
}
```

---

* **Дані тільки з низькоякісних джерел (рівень 3–4)** → допускаються, але `needs_human_review = true`.

**Приклад JSON:**

```json
{
  "ingredient_name_uk": "Ехінацея",
  "ingredient_name_lat": "Echinacea purpurea",
  "result_status": "partial",
  "citations": [
    {
      "type": "daily_dose",
      "title": "Manufacturer label: Echinacea supplement",
      "journal_or_publisher": "Product Label",
      "year": 2022,
      "url": "https://...",
      "doi": null,
      "exact_quote": "Suggested use: 500 mg per day...",
      "page_or_section": "label",
      "source_priority": 4,
      "needs_human_review": true
    }
  ],
  "provenance": { "colab_cell": "Cell EdgeCase", "model": "GPT-5", "retrieved_at": "2025-09-19T12:45:00Z" }
}
```

---

* **Невідповідність таксономії** → `result_status = "ambiguous"`.

**Приклад JSON:**

```json
{
  "ingredient_name_uk": "Женьшень",
  "ingredient_name_lat": "Panax spp.",
  "result_status": "ambiguous",
  "citations": [
    {
      "type": "origin",
      "title": "Taxonomy of Panax ginseng",
      "journal_or_publisher": "J Ethnopharmacol",
      "year": 2016,
      "url": "https://...",
      "doi": "10.1016/j.jep.2016.05.001",
      "exact_quote": "Panax ginseng is often confused with Panax quinquefolius...",
      "page_or_section": "p. 220",
      "source_priority": 2,
      "needs_human_review": false
    },
    {
      "type": "origin",
      "title": "Conflicting classification of Panax species",
      "journal_or_publisher": "Planta Med",
      "year": 2019,
      "url": "https://...",
      "doi": "10.1055/a-1234-5678",
      "exact_quote": "Some authors classify Panax ginseng and Panax quinquefolius differently...",
      "page_or_section": "p. 50",
      "source_priority": 2,
      "needs_human_review": false
    }
  ],
  "search_trace": [
    { "engine": "pubmed", "query": "Panax ginseng taxonomy", "results_checked": 10, "notes": "conflicting taxonomy between sources" }
  ],
  "provenance": { "colab_cell": "Cell EdgeCase", "model": "GPT-5", "retrieved_at": "2025-09-19T12:50:00Z" }
}
```

---

* **Мертві або закриті посилання** → `url = null`, залишати DOI.

**Приклад JSON:**

```json
{
  "ingredient_name_uk": "Куркумін",
  "ingredient_name_lat": "Curcuma longa",
  "result_status": "found",
  "citations": [
    {
      "type": "active_compounds",
      "title": "Curcumin composition study",
      "journal_or_publisher": "Food Chem",
      "year": 2014,
      "url": null,
      "doi": "10.1016/j.foodchem.2014.05.002",
      "exact_quote": "Curcuma longa rhizome contains curcumin as the major polyphenol...",
      "page_or_section": "p. 70",
      "source_priority": 2,
      "needs_human_review": true
    }
  ],
  "search_trace": [
    { "engine": "science_direct", "query": "Curcumin composition", "results_checked": 5, "notes": "URL inaccessible, used DOI" }
  ],
  "provenance": { "colab_cell": "Cell EdgeCase", "model": "GPT-5", "retrieved_at": "2025-09-19T12:55:00Z" }
}
```

---

## 9) Приклади JSON для крайових випадків

### 9.1 Суперечні RCT → `result_status = "contradictory"`

```json
{
  "ingredient_name_uk": "Екстракт часнику",
  "ingredient_name_lat": "Allium sativum",
  "synonyms": ["часниковий екстракт", "garlic extract"],
  "source_material": {"kingdom": "Рослини", "part_or_origin": "цибулини", "description": null},
  "active_compounds": [{"name": "аліцин", "iupac": null, "cas": "539-86-6", "concentration": null}],
  "daily_dose": {"recommended": null, "upper_limit": null, "evidence_type": "RCT"},
  "result_status": "contradictory",
  "sources": [
    {"title": "RCT A on garlic and blood pressure", "journal_or_publisher": "Journal A", "year": 2019, "url": "https://example.org/rcta", "doi": null, "source_priority": 2, "needs_human_review": false},
    {"title": "RCT B on garlic and blood pressure", "journal_or_publisher": "Journal B", "year": 2021, "url": "https://example.org/rctb", "doi": null, "source_priority": 2, "needs_human_review": false}
  ],
  "citations": [
    {"type": "other", "title": "RCT A on garlic and blood pressure", "journal_or_publisher": "Journal A", "year": 2019, "url": "https://example.org/rcta", "doi": null, "exact_quote": "Significant reduction in systolic BP versus placebo.", "page_or_section": "Results", "source_priority": 2, "needs_human_review": false},
    {"type": "other", "title": "RCT B on garlic and blood pressure", "journal_or_publisher": "Journal B", "year": 2021, "url": "https://example.org/rctb", "doi": null, "exact_quote": "No difference in BP compared with placebo.", "page_or_section": "Conclusion", "source_priority": 2, "needs_human_review": false}
  ],
  "search_trace": [{"engine": "pubmed", "query": "Allium sativum randomized blood pressure", "results_checked": 20, "notes": "знайдено 2 RCT з протилежними висновками"}],
  "provenance": {"colab_cell": "Cell 1 — Evidence Fetch", "model": "GPT‑5 Thinking", "model_version": "2025-09", "parser_version": "1.0.0", "run_id": "edge_case_1", "retrieved_at": "2025-09-19T11:50:00Z"}
}
```

### 9.2 Сполуки без кількісних значень → `concentration = null`

```json
{
  "ingredient_name_uk": "Кора верби",
  "ingredient_name_lat": "Salix alba",
  "synonyms": ["біла верба", "willow bark"],
  "source_material": {"kingdom": "Рослини", "part_or_origin": "кора", "description": null},
  "active_compounds": [
    {"name": "саліцин", "iupac": null, "cas": "138-52-3", "concentration": null},
    {"name": "таніни", "iupac": null, "cas": null, "concentration": null}
  ],
  "daily_dose": null,
  "result_status": "partial",
  "sources": [{"title": "Review on Salix alba phytochemistry", "journal_or_publisher": "Journal C", "year": 2017, "url": "https://example.org/salix-review", "doi": null, "source_priority": 3, "needs_human_review": true}],
  "citations": [{"type": "active_compounds", "title": "Review on Salix alba phytochemistry", "journal_or_publisher": "Journal C", "year": 2017, "url": "https://example.org/salix-review", "doi": null, "exact_quote": "Willow bark contains salicin and tannins.", "page_or_section": "Phytochemicals", "source_priority": 3, "needs_human_review": true}],
  "search_trace": [{"engine": "google_scholar", "query": "Salix alba phytochemistry salicin", "results_checked": 12, "notes": "кількісних даних не наведено"}],
  "provenance": {"colab_cell": "Cell 1 — Evidence Fetch", "model": "GPT‑5 Thinking", "model_version": "2025-09", "parser_version": "1.0.0", "run_id": "edge_case_2", "retrieved_at": "2025-09-19T11:51:00Z"}
}
```

### 9.3 Діапазон доз → `min_value`/`max_value`

```json
{
  "ingredient_name_uk": "Магній (цитрат)",
  "ingredient_name_lat": "Magnesium citrate",
  "synonyms": ["магній цитрат"],
  "source_material": {"kingdom": "Мінерали", "part_or_origin": null, "description": null},
  "active_compounds": [],
  "daily_dose": {
    "recommended": {"value": null, "min_value": 200, "max_value": 400, "unit": "мг/день"},
    "upper_limit": {"value": 350, "min_value": null, "max_value": null, "unit": "мг/день"},
    "evidence_type": "guideline"
  },
  "result_status": "found",
  "sources": [{"title": "Guideline on magnesium intake", "journal_or_publisher": "Agency D", "year": 2018, "url": "https://example.org/mg-guideline", "doi": null, "source_priority": 1, "needs_human_review": false}],
  "citations": [{"type": "daily_dose", "title": "Guideline on magnesium intake", "journal_or_publisher": "Agency D", "year": 2018, "url": "https://example.org/mg-guideline", "doi": null, "exact_quote": "Recommended 200–400 mg/day; tolerable upper intake 350 mg/day (supplemental).", "page_or_section": "Table 2", "source_priority": 1, "needs_human_review": false}],
  "search_trace": [{"engine": "pubmed", "query": "magnesium citrate recommended intake guideline", "results_checked": 8, "notes": null}],
  "provenance": {"colab_cell": "Cell 1 — Evidence Fetch", "model": "GPT‑5 Thinking", "model_version": "2025-09", "parser_version": "1.0.0", "run_id": "edge_case_3", "retrieved_at": "2025-09-19T11:52:00Z"}
}
```

### 9.4 Тільки низькоякісні джерела (рівень 3–4) → `needs_human_review = true`

```json
{
  "ingredient_name_uk": "Екстракт зеленого чаю",
  "ingredient_name_lat": "Camellia sinensis",
  "synonyms": ["зелений чай", "green tea extract"],
  "source_material": {"kingdom": "Рослини", "part_or_origin": "листя", "description": null},
  "active_compounds": [{"name": "епігалокатехін‑3‑галат (EGCG)", "iupac": null, "cas": "989-51-5", "concentration": null}],
  "daily_dose": {"recommended": null, "upper_limit": null, "evidence_type": "label_claim"},
  "result_status": "partial",
  "sources": [{"title": "Manufacturer catalog entry", "journal_or_publisher": "Brand X", "year": 2022, "url": "https://example.org/label-egcg", "doi": null, "source_priority": 4, "needs_human_review": true}],
  "citations": [{"type": "active_compounds", "title": "Manufacturer catalog entry", "journal_or_publisher": "Brand X", "year": 2022, "url": "https://example.org/label-egcg", "doi": null, "exact_quote": "Contains EGCG.", "page_or_section": "Specs", "source_priority": 4, "needs_human_review": true}],
  "search_trace": [{"engine": "web", "query": "green tea extract EGCG label", "results_checked": 5, "notes": "високоякісних джерел не знайдено"}],
  "provenance": {"colab_cell": "Cell 1 — Evidence Fetch", "model": "GPT‑5 Thinking", "model_version": "2025-09", "parser_version": "1.0.0", "run_id": "edge_case_4", "retrieved_at": "2025-09-19T11:53:00Z"}
}
```

### 9.5 Невідповідність таксономії → `result_status = "ambiguous"`

```json
{
  "ingredient_name_uk": "Ашваганда",
  "ingredient_name_lat": "Withania somnifera",
  "synonyms": ["індійський женьшень", "ashwagandha"],
  "source_material": {"kingdom": "Рослини", "part_or_origin": "корінь", "description": null},
  "active_compounds": [{"name": "вітаноліди", "iupac": null, "cas": null, "concentration": null}],
  "daily_dose": null,
  "result_status": "ambiguous",
  "sources": [
    {"title": "Taxonomy ref 1", "journal_or_publisher": "Database E", "year": 2020, "url": "https://example.org/tax1", "doi": null, "source_priority": 3, "needs_human_review": true},
    {"title": "Taxonomy ref 2 (alt name: Withania somnifera Dunal)", "journal_or_publisher": "Database F", "year": 2019, "url": "https://example.org/tax2", "doi": null, "source_priority": 3, "needs_human_review": true}
  ],
  "citations": [
    {"type": "other", "title": "Taxonomy ref 1", "journal_or_publisher": "Database E", "year": 2020, "url": "https://example.org/tax1", "doi": null, "exact_quote": "Withania somnifera is listed as ...", "page_or_section": "Entry", "source_priority": 3, "needs_human_review": true},
    {"type": "other", "title": "Taxonomy ref 2", "journal_or_publisher": "Database F", "year": 2019, "url": "https://example.org/tax2", "doi": null, "exact_quote": "Synonym: Withania somnifera (L.) Dunal.", "page_or_section": "Synonyms", "source_priority": 3, "needs_human_review": true}
  ],
  "search_trace": [{"engine": "web", "query": "Withania somnifera taxonomy synonym Dunal", "results_checked": 10, "notes": "різні формати латинської назви"}],
  "provenance": {"colab_cell": "Cell 1 — Evidence Fetch", "model": "GPT‑5 Thinking", "model_version": "2025-09", "parser_version": "1.0.0", "run_id": "edge_case_5", "retrieved_at": "2025-09-19T11:54:00Z"}
}
```

---

## 10) Наступні кроки

* Додати приклад `not_found` з повним `search_trace`.
* Згенерувати Colab‑функцію **@title Edge Case Tester** для автоматичної перевірки виставлення `result_status` і прапорців `needs_human_review`.

---

## 11) Colab — Build Query Terms

**@title Build Query Terms**

```python
# Читає діапазони з Google Sheets і формує query_terms
import gspread
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
import re

# Конфіг (з канви Data Sources)
SHEET_ID = "1kOrSOPgn7IDdA170YJDRBQw4Wt2-Y8uX0PdvCfxY4qA"
SHEET_NAME = "Ingredients_Main"
INGREDIENTS_RANGE = "C2:C"
SYNONYMS_EN_LAT_RANGE = "E2:E"

creds = Credentials.from_service_account_file("credentials.json", scopes=["https://www.googleapis.com/auth/spreadsheets"])
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

names = [c[0] for c in sheet.get(INGREDIENTS_RANGE) if c]
synonyms = [c[0] for c in sheet.get(SYNONYMS_EN_LAT_RANGE) if c]

# Об'єднання та нормалізація
raw_terms = []
for v in names + synonyms:
    for t in re.split(r",|;|\n", str(v)):
        t = t.strip()
        if t:
            raw_terms.append(t)

# Дедуплікація та фільтрація абревіатур
query_terms = []
seen = set()
for t in raw_terms:
    key = t.lower()
    if key not in seen:
        seen.add(key)
        if len(t) <= 5 and t.upper() == t:
            continue  # пропускаємо ізольовані абревіатури
        query_terms.append(t)

print("Query terms:", query_terms)
# TODO: логувати query_terms у search_trace
```

---

## 12) Colab — Search Runner (Level 1→4)

**@title Search Runner**

```python
# Псевдокод: виконує пошук по кожному query_term та збирає sources/citations

results = []
search_trace = []

for term in query_terms:
    for level in [1,2,3,4]:
        # виклик функції search_level(term, level)
        found_sources, found_citations = search_level(term, level)
        if found_sources:
            results.extend(found_sources)
            citations.extend(found_citations)
            search_trace.append({"term": term, "level": level, "notes": f"{len(found_sources)} sources"})
            break  # не переходимо на нижчий рівень, якщо дані знайдені

# Після циклу формуємо JSON: ingredient, sources, citations, search_trace
print({"sources": results, "citations": citations, "search_trace": search_trace})
```

**Призначення:**

* проходить по всіх `query_terms`
* викликає пошук рівень‑за‑рівнем (1→4)
* збирає `sources` і `citations`
* записує лог у `search_trace`