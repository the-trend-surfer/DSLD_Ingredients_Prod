"""
Gemini Google Search Integration
Фінальний етап пошуку з використанням Google Search через Gemini API
"""
import google.generativeai as genai
import json
import re
from typing import Dict, List, Any, Optional
from config import Config

class GeminiGoogleSearcher:
    """Gemini з Google Search для фінального пошуку інгредієнтів"""

    def __init__(self):
        self.model = None
        self.search_tool = None
        self.setup_gemini_search()

    def setup_gemini_search(self):
        """Налаштування Gemini з Google Search"""
        try:
            if not Config.GEMINI_API_KEY:
                print("[ERROR] Gemini API key not found")
                return

            genai.configure(api_key=Config.GEMINI_API_KEY)

            # Створюємо інструмент для пошуку в Google
            self.search_tool = genai.protos.Tool(
                google_search_retrieval=genai.protos.GoogleSearchRetrieval()
            )

            # Створюємо модель з пошуковим інструментом
            self.model = genai.GenerativeModel(
                model_name='gemini-1.5-pro-latest',
                tools=[self.search_tool]
            )

            print("[OK] Gemini Google Search initialized")

        except Exception as e:
            print(f"[ERROR] Gemini Google Search setup failed: {e}")
            self.model = None

    def search_column_specific_data(self, ingredient: str, synonyms: Optional[List[str]] = None, column_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Цільовий пошук даних про інгредієнт для конкретного стовпчика

        Args:
            ingredient: Назва інгредієнта
            synonyms: Список синонімів
            column_type: Тип стовпчика ('source_material', 'active_compounds', 'dosage', 'comprehensive')

        Returns:
            Структуровані дані для конкретного стовпчика
        """
        if not self.model:
            print("[ERROR] Gemini Google Search not available")
            return self._create_empty_result(ingredient)

        try:
            # Створюємо промпт для конкретного типу стовпчика
            prompt = self._create_column_specific_prompt(ingredient, synonyms, column_type)
            print(f"[GEMINI-{column_type.upper()}] Using {column_type} search prompt")

            print(f"[GEMINI-SEARCH] Searching Google for: {ingredient}")
            print(f"[PROMPT] {prompt[:100]}...")

            # Виконуємо пошук
            response = self.model.generate_content(prompt)

            if not response.text:
                print("[ERROR] Empty response from Gemini Google Search")
                return self._create_empty_result(ingredient)

            # Парсимо відповідь з урахуванням типу стовпчика
            result = self._parse_gemini_response(response, ingredient, column_type)

            # Додаємо джерела з grounding metadata або створюємо synthetic sources
            raw_sources = []
            if hasattr(response, 'grounding_metadata') and response.grounding_metadata:
                raw_sources = self._extract_grounding_sources(response.grounding_metadata)
                print(f"[SOURCES] Found {len(raw_sources)} raw Google sources")
            elif hasattr(response, 'candidates') and response.candidates:
                raw_sources = self._extract_sources_from_candidates(response.candidates)
                print(f"[SOURCES] Found {len(raw_sources)} sources from candidates")
            else:
                # Fallback: створюємо synthetic sources на основі тексту відповіді
                print("[WARNING] No grounding metadata found, creating synthetic sources from response")
                raw_sources = self._create_synthetic_sources(response.text, ingredient)

            # Застосовуємо L1-L4 фільтрацію та пріоритизацію
            if raw_sources:
                result['google_sources'] = self._filter_sources_by_priority(raw_sources)
                print(f"[L1-L4] Prioritized sources: L1={len([s for s in result['google_sources'] if s.get('priority_level')==1])}, L2={len([s for s in result['google_sources'] if s.get('priority_level')==2])}, L3={len([s for s in result['google_sources'] if s.get('priority_level')==3])}, L4={len([s for s in result['google_sources'] if s.get('priority_level')==4])}")
            else:
                result['google_sources'] = []

            return result

        except Exception as e:
            print(f"[ERROR] Gemini Google Search failed for {ingredient}: {e}")
            return self._create_empty_result(ingredient)

    def _create_column_specific_prompt(self, ingredient: str, synonyms: Optional[List[str]] = None, column_type: str = "comprehensive") -> str:
        """Створює спеціалізований промпт для конкретного типу стовпчика"""

        # Додаємо синоніми до пошуку
        search_terms = [ingredient]
        if synonyms:
            search_terms.extend(synonyms[:2])  # Максимум 2 синоніми

        terms_text = " OR ".join([f'"{term}"' for term in search_terms])

        # Базові інструкції для всіх типів пошуку
        base_instructions = f"""SEARCH TERMS: {terms_text}
Ingredient: {ingredient}

L1-L4 SOURCE PRIORITY:
- L1 (Priority): NIH.gov, NCBI.nlm.nih.gov, EFSA.europa.eu, FDA.gov
- L2 (High): Nature.com, ScienceDirect.com, Springer.com
- L3 (Medium): Examine.com, Wiley.com
- L4 (Low): Commercial sites

FOCUS: Use L1-L2 sources first, L3-L4 only if L1-L2 unavailable."""

        # Створюємо спеціалізований промпт залежно від типу стовпчика
        if column_type == "source_material":
            prompt = f"""{base_instructions}

SPECIFIC TASK: Find BIOLOGICAL SOURCE (raw material origin) for supplement ingredient.

SEARCH QUERY: ("{ingredient}" OR {' OR '.join([f'"{s}"' for s in synonyms[:2]]) if synonyms else '"' + ingredient + '"'}) biological source extraction

FORMAT REQUIREMENTS:
- Ukrainian food names: соя, морква, інжир, коріандр
- Plant parts: корені, листя, квітки, плоди, насіння
- Latin names: (Angelica archangelica), (Lepidium meyenii)
- Processing: олії рослинні, екстракт, продукт гідролізу
- Animal sources: субпродукти тваринного походження, молоко, риба
- Synthetic: "або отриманий шляхом біотехнологічного синтезу"

EXAMPLES:
- "Соя, морква, інжир, коріандр, дягель лікарський корені, плоди (Angelica archangelica)"
- "Олії рослинні (соєва, оливкова, зародків пшениці), Мака перуанська коренеплоди (Lepidium meyenii)"
"""
        elif column_type == "active_compounds":
            prompt = f"""{base_instructions}

SPECIFIC TASK: Find ACTIVE COMPOUNDS (chemical constituents) for supplement ingredient.

SEARCH QUERY: ("{ingredient}" OR {' OR '.join([f'"{s}"' for s in synonyms[:2]]) if synonyms else '"' + ingredient + '"'}) active compounds chemical

FORMAT REQUIREMENTS:
- Ukrainian chemical names with English in parentheses
- Examples: "β-ситостерин (β-Sitosterol)", "Лецитин (фосфатиділхолін) (Lecithin)"
- Include concentration if available: "15-20% β-глюканів"
- List 2-4 main compounds maximum
"""
        elif column_type == "dosage":
            prompt = f"""{base_instructions}

SPECIFIC TASK: Find DOSAGE recommendations for supplement ingredient.

SEARCH QUERY: ("{ingredient}" OR {' OR '.join([f'"{s}"' for s in synonyms[:2]]) if synonyms else '"' + ingredient + '"'}) dosage clinical recommendations

FORMAT REQUIREMENTS:
- ONLY numbers and units: "500 mg", "1-3 g", "10 μg"
- NO additional text, instructions, or context
- Focus on adult daily therapeutic doses
"""
        else:  # comprehensive
            prompt = f"""{base_instructions}

SPECIFIC TASK: Find comprehensive scientific data about dietary supplement ingredient.

SEARCH QUERY: {terms_text}

FORMAT REQUIREMENTS:
- All data types: biological source, active compounds, dosage
- Follow Ukrainian formatting standards
- Extract exact citations from L1-L2 sources
"""

        return prompt

    def _filter_sources_by_priority(self, sources: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Фільтрує та ранжує джерела за L1-L4 пріоритетом"""
        from config import Config

        # Створюємо список з пріоритетами
        prioritized_sources = []

        for source in sources:
            url = source.get('url', '').lower()
            priority = 5  # За замовчуванням найнижчий пріоритет

            # Визначаємо пріоритет на основі домену
            for level, domains in Config.SOURCE_LEVELS.items():
                for domain in domains:
                    if domain.lower() in url:
                        priority = level
                        break
                if priority < 5:
                    break

            source_with_priority = source.copy()
            source_with_priority['priority_level'] = priority
            prioritized_sources.append(source_with_priority)

        # Сортуємо за пріоритетом (L1=1 найвищий, L4=4 найнижчий)
        prioritized_sources.sort(key=lambda x: x['priority_level'])

        print(f"[L1-L4-FILTER] Filtered {len(sources)} sources, prioritized by level")
        return prioritized_sources

    def _parse_gemini_response(self, response, ingredient: str, column_type: str = "comprehensive") -> Dict[str, Any]:
        """Парсить відповідь Gemini та структурує дані"""

        text = response.text

        # Витягуємо структуровані дані з тексту
        result = {
            'ingredient': ingredient,
            'source_material': self._extract_source_material(text),
            'active_compounds': self._extract_active_compounds(text),
            'dosage_info': self._extract_dosage_info(text),
            'scientific_evidence': self._extract_scientific_evidence(text),
            'raw_response': text,
            'search_method': 'gemini_google_search'
        }

        return result

    def _extract_source_material(self, text: str) -> Dict[str, str]:
        """Витягує інформацію про джерело сировини"""
        source_info = {
            'organism': '',
            'scientific_name': '',
            'part_used': '',
            'kingdom': ''
        }

        # Пошук латинських назв
        latin_pattern = r'([A-Z][a-z]+ [a-z]+)'
        latin_matches = re.findall(latin_pattern, text)
        if latin_matches:
            source_info['scientific_name'] = latin_matches[0]

        # Пошук частин рослин
        parts_pattern = r'\b(root|leaf|leaves|bark|fruit|seed|flower|stem|rhizome|berry|extract)\b'
        parts_matches = re.findall(parts_pattern, text, re.IGNORECASE)
        if parts_matches:
            source_info['part_used'] = ', '.join(set(parts_matches[:3]))

        return source_info

    def _extract_active_compounds(self, text: str) -> List[Dict[str, str]]:
        """Витягує активні сполуки"""
        compounds = []

        # Пошук хімічних сполук
        compound_patterns = [
            r'\b([a-zA-Z-]+(?:in|ine|ol|ic acid|ate))\b',  # Хімічні суфікси
            r'\b([A-Z][a-z]+-?[0-9]*)\b',  # Витаміни, мінерали
            r'\b(\d+(?:\.\d+)?%\s+[a-zA-Z-]+)\b'  # Відсотки
        ]

        for pattern in compound_patterns:
            matches = re.findall(pattern, text)
            for match in matches[:5]:  # Максимум 5 сполук
                if len(match) > 3:  # Фільтруємо короткі збіги
                    compounds.append({
                        'name': match,
                        'concentration': 'not specified'
                    })

        return compounds

    def _extract_dosage_info(self, text: str) -> Dict[str, str]:
        """Витягує інформацію про дозування"""
        dosage_info = {
            'daily_dose': '',
            'clinical_dose': '',
            'units': '',
            'context': ''
        }

        # Пошук дозувань
        dosage_patterns = [
            r'\b(\d+(?:\.\d+)?)\s*(mg|g|mcg|μg|IU|CFU)(?:/day|/daily|\s+daily)?\b',
            r'\b(\d+-\d+)\s*(mg|g|mcg|μg|IU|CFU)\b',
            r'\bdaily dose.*?(\d+(?:\.\d+)?)\s*(mg|g|mcg|μg|IU|CFU)\b'
        ]

        for pattern in dosage_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                dose, unit = matches[0]
                dosage_info['daily_dose'] = f"{dose} {unit}"
                dosage_info['units'] = unit
                break

        return dosage_info

    def _extract_scientific_evidence(self, text: str) -> List[Dict[str, str]]:
        """Витягує наукові докази"""
        evidence = []

        # Пошук років досліджень
        year_pattern = r'\b(20[0-2][0-9])\b'
        years = re.findall(year_pattern, text)

        # Пошук типів досліджень
        study_patterns = [
            r'(clinical trial)',
            r'(randomized controlled trial)',
            r'(placebo-controlled)',
            r'(meta-analysis)',
            r'(systematic review)'
        ]

        for pattern in study_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                evidence.append({
                    'type': match,
                    'year': years[0] if years else 'not specified'
                })

        return evidence

    def _extract_grounding_sources(self, grounding_metadata) -> List[Dict[str, str]]:
        """Витягує джерела з grounding metadata з контентом"""
        sources = []

        if hasattr(grounding_metadata, 'grounding_chunks'):
            for chunk in grounding_metadata.grounding_chunks:
                if hasattr(chunk, 'web'):
                    # Витягуємо контент з усіх доступних джерел
                    content = ""

                    # Намагаємося витягти контент з різних атрибутів
                    if hasattr(chunk, 'content') and chunk.content:
                        content = str(chunk.content)
                    elif hasattr(chunk, 'text') and chunk.text:
                        content = str(chunk.text)
                    elif hasattr(chunk, 'snippet') and chunk.snippet:
                        content = str(chunk.snippet)
                    elif hasattr(chunk.web, 'snippet') and chunk.web.snippet:
                        content = str(chunk.web.snippet)

                    # Якщо все ще немає контенту, використовуємо title
                    if not content and hasattr(chunk.web, 'title'):
                        content = str(chunk.web.title)

                    # Перевіряємо чи URL є VertexAI redirect і намагаємося отримати оригінальний
                    original_url = self._extract_original_url(chunk.web.uri)

                    sources.append({
                        'title': chunk.web.title if hasattr(chunk.web, 'title') else 'No title',
                        'url': original_url,  # Використовуємо оригінальний URL
                        'redirect_url': chunk.web.uri,  # Зберігаємо redirect для debugging
                        'content': content.strip()[:500] if content else '',  # Обмежуємо довжину
                        'type': 'google_search_result'
                    })

        return sources

    def _extract_sources_from_candidates(self, candidates) -> List[Dict[str, str]]:
        """Витягує джерела з candidates (альтернативний метод)"""
        sources = []

        try:
            for candidate in candidates:
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    if hasattr(candidate.grounding_metadata, 'grounding_chunks'):
                        for chunk in candidate.grounding_metadata.grounding_chunks:
                            if hasattr(chunk, 'web'):
                                sources.append({
                                    'title': chunk.web.title,
                                    'url': chunk.web.uri,
                                    'type': 'google_search_result'
                                })

        except Exception as e:
            print(f"[WARNING] Error extracting sources from candidates: {e}")

        return sources

    def _extract_original_url(self, redirect_url: str) -> str:
        """Витягує оригінальний URL з VertexAI redirect посилання"""
        import urllib.parse
        import base64

        # Перевіряємо чи це VertexAI redirect
        if 'vertexaisearch.cloud.google.com/grounding-api-redirect' in redirect_url:
            try:
                # Намагаємося витягти домен з redirect URL
                # VertexAI іноді кодує оригінальні домени в redirect

                # Простий спосіб - витягти можливий домен з redirect path
                if '/grounding-api-redirect/' in redirect_url:
                    # Іноді домен закодований у самому redirect
                    # Використаємо більш простий підхід - повернемо стандартний URL формат

                    # Для популярних доменів створимо mapping
                    domain_hints = {
                        'ahcc': 'https://ahcc.net',
                        'wikipedia': 'https://en.wikipedia.org',
                        'pubmed': 'https://pubmed.ncbi.nlm.nih.gov',
                        'ncbi': 'https://ncbi.nlm.nih.gov',
                        'sourcenaturals': 'https://sourcenaturals.com'
                    }

                    # Перевіряємо наявність доменів у redirect URL
                    redirect_lower = redirect_url.lower()
                    for hint, full_url in domain_hints.items():
                        if hint in redirect_lower:
                            print(f"[URL-CONVERT] VertexAI redirect → {full_url}")
                            return full_url

                # Якщо не можемо декодувати, повертаємо оригінальний redirect
                print(f"[URL-WARNING] Could not decode VertexAI redirect, keeping original")
                return redirect_url

            except Exception as e:
                print(f"[URL-ERROR] Failed to extract original URL: {e}")
                return redirect_url
        else:
            # Якщо це не redirect, повертаємо як є
            return redirect_url

    def _create_empty_result(self, ingredient: str) -> Dict[str, Any]:
        """Створює порожній результат при невдачі"""
        return {
            'ingredient': ingredient,
            'source_material': {},
            'active_compounds': [],
            'dosage_info': {},
            'scientific_evidence': [],
            'google_sources': [],
            'raw_response': '',
            'search_method': 'gemini_google_search_failed'
        }

# Глобальний екземпляр
gemini_google_searcher = GeminiGoogleSearcher()