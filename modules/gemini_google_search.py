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

    def search_for_column_b_source(self, ingredient: str, synonyms: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Пошук для стовпчика B - Джерело отримання
        Query pattern: ("IngrediENT" OR "synonym1") biological source extraction "derived from"
        """
        if not self.model:
            return []

        try:
            # Формуємо імена для пошуку
            search_terms = [f'"{ingredient}"']
            if synonyms:
                search_terms.extend([f'"{syn}"' for syn in synonyms[:2]])

            # Спеціалізований запит для джерела сировини
            query_text = f"Find biological source and origin of {' OR '.join(search_terms)}. Focus on plant/animal/fungal source, scientific name, which part (leaves, root, fruit, etc.)"

            response = self.model.generate_content(query_text)

            # Використовуємо grounding_metadata для реальних URL
            sources = []

            # Отримуємо grounding metadata з першого кандидата
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    grounding_data = candidate.grounding_metadata

                    if hasattr(grounding_data, 'grounding_chunks') and grounding_data.grounding_chunks:
                        for chunk in grounding_data.grounding_chunks:
                            if hasattr(chunk, 'web') and chunk.web:
                                sources.append({
                                    "url": chunk.web.uri,
                                    "title": chunk.web.title,
                                    "content": response.text,
                                    "type": "gemini_search"
                                })

            if sources:
                print(f"[B1-OK] Gemini found {len(sources)} sources")
            else:
                print(f"[B1] No grounding metadata from Gemini")

            return sources

        except Exception as e:
            print(f"[ERROR] Column B search failed for {ingredient}: {e}")
            return []

    def search_for_column_c_compounds(self, ingredient: str, synonyms: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Пошук для стовпчика C - Активні сполуки
        Query pattern: ("IngrediENT" OR "synonym1") active compounds chemical composition
        """
        if not self.model:
            return []

        try:
            # Формуємо імена для пошуку
            search_terms = [f'"{ingredient}"']
            if synonyms:
                search_terms.extend([f'"{syn}"' for syn in synonyms[:2]])

            # Спеціалізований запит для активних сполук
            query_text = f"Find active compounds and chemical composition of {' OR '.join(search_terms)}. Focus on bioactive ingredients, chemical names, concentrations, molecular formulas"

            response = self.model.generate_content(query_text)

            # Використовуємо grounding_metadata для реальних URL
            sources = []

            # Отримуємо grounding metadata з першого кандидата
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    grounding_data = candidate.grounding_metadata

                    if hasattr(grounding_data, 'grounding_chunks') and grounding_data.grounding_chunks:
                        for chunk in grounding_data.grounding_chunks:
                            if hasattr(chunk, 'web') and chunk.web:
                                sources.append({
                                    "url": chunk.web.uri,
                                    "title": chunk.web.title,
                                    "content": response.text,
                                    "type": "gemini_search"
                                })

            if sources:
                print(f"[C1-OK] Gemini found {len(sources)} sources")
            else:
                print(f"[C1] No grounding metadata from Gemini")

            return sources

        except Exception as e:
            print(f"[ERROR] Column C search failed for {ingredient}: {e}")
            return []

    def search_for_column_d_dosage(self, ingredient: str, synonyms: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Пошук для стовпчика D - Дозування
        Query pattern: ("IngrediENT" OR "synonym1") dosage clinical recommendations "mg per day"
        """
        if not self.model:
            return []

        try:
            # Формуємо імена для пошуку
            search_terms = [f'"{ingredient}"']
            if synonyms:
                search_terms.extend([f'"{syn}"' for syn in synonyms[:2]])

            # Спеціалізований запит для дозування
            query_text = f"Find dosage and clinical recommendations for {' OR '.join(search_terms)}. Focus on recommended dose, mg per day, clinical studies, therapeutic dosage"

            response = self.model.generate_content(query_text)

            # Використовуємо grounding_metadata для реальних URL
            sources = []

            # Отримуємо grounding metadata з першого кандидата
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    grounding_data = candidate.grounding_metadata

                    if hasattr(grounding_data, 'grounding_chunks') and grounding_data.grounding_chunks:
                        for chunk in grounding_data.grounding_chunks:
                            if hasattr(chunk, 'web') and chunk.web:
                                sources.append({
                                    "url": chunk.web.uri,
                                    "title": chunk.web.title,
                                    "content": response.text,
                                    "type": "gemini_search"
                                })

            if sources:
                print(f"[D1-OK] Gemini found {len(sources)} sources")
            else:
                print(f"[D1] No grounding metadata from Gemini")

            return sources

        except Exception as e:
            print(f"[ERROR] Column D search failed for {ingredient}: {e}")
            return []

# Основна функція (legacy)
def gemini_google_search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """Legacy функція для сумісності"""
    searcher = GeminiGoogleSearcher()
    return searcher.search_for_column_b_source(query)