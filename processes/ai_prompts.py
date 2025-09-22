"""
AI Prompts for Table Extraction
"""

class TablePrompts:
    """Collection of AI prompts for table extraction"""

    @staticmethod
    def get_table_extraction_prompt(ingredient: str, content: str, url: str = "") -> str:
        """
        Get prompt for extracting table data from document content

        Args:
            ingredient: Ingredient name
            content: Document text content
            url: Source URL (optional)

        Returns:
            Formatted prompt for AI extraction
        """

        prompt = f"""Витягни дані про інгредієнт "{ingredient}" з наданого тексту у JSON форматі.

ВАЖЛИВО: Повертай ТІЛЬКИ валідний JSON без додаткових пояснень.

Формат відповіді:
{{
  "nazva_ukr_orig": "Українська назва (English name)",
  "dzherelo_syrovyny": "Частина рослини/організму",
  "aktyvni_spoluky": ["сполука1", "сполука2"],
  "dobova_norma": "Дозування з одиницями",
  "dzherela_tsytaty": [
    {{"quote": "точна цитата з тексту", "url": "URL джерела"}}
  ]
}}

Правила:
1. nazva_ukr_orig - ЗАВЖДИ перекладай назву українською у форматі "Українська (English)":
   - "AHCC" → "АХЦЦ (AHCC)"
   - "Vitamin C" → "Вітамін С (Vitamin C)"
   - "CoQ10" → "Коензим Q10 (CoQ10)"
   - НІКОЛИ НЕ пиши "[назва не знайдена]"
2. dzherelo_syrovyny - конкретна частина організму (листя, корінь, плоди)
3. aktyvni_spoluky - тільки підтверджені активні речовини
4. dobova_norma - конкретні цифри з одиницями (мг, г, IU)
5. dzherela_tsytaty - точні фрази з тексту (не більше 100 символів), URL має бути реальним посиланням на джерело

ДЖЕРЕЛО: {url}

Текст для аналізу:
{content[:2000]}

JSON відповідь:"""

        return prompt

    @staticmethod
    def get_source_extraction_prompt(ingredient: str, content: str) -> str:
        """Get prompt for extracting source material information"""

        return f"""Витягни інформацію про джерело сировини для "{ingredient}" з тексту.

Поверни ТІЛЬКИ джерело у форматі: "Організм, частина (Наукова назва)"

Приклади:
- "Гриби шіїтаке, міцелій (Lentinula edodes)"
- "Соя, насіння (Glycine max)"
- "Риба, печінка (Marine sources)"

Текст: {content[:500]}

Джерело сировини:"""

    @staticmethod
    def get_compounds_extraction_prompt(ingredient: str, content: str) -> str:
        """Get prompt for extracting active compounds"""

        return f"""Витягни активні сполуки для "{ingredient}" з тексту.

Поверни ТІЛЬКИ сполуки у форматі: "українська назва (English name), українська назва 2 (English name 2)"

Приклади:
- "β-ситостерин (β-Sitosterol), токофероли (Tocopherols)"
- "аскорбінова кислота (Ascorbic acid)"

Текст: {content[:500]}

Активні сполуки:"""

    @staticmethod
    def get_dosage_extraction_prompt(ingredient: str, content: str) -> str:
        """Get prompt for extracting dosage information"""

        return f"""Витягни дозування для "{ingredient}" з тексту.

Поверни ТІЛЬКИ цифри та одиниці.

Приклади:
- "500 mg"
- "1-3 g"
- "200-400 mg"

Текст: {content[:500]}

Дозування:"""