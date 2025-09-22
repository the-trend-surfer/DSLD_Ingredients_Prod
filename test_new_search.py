#!/usr/bin/env python3
"""
Тестування нової архітектури пошуку з OR операторами та L1-L4 фільтрацією
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.gemini_google_search import gemini_google_searcher

def test_column_specific_search():
    """Тестує нові функції пошуку по стовпчикам"""

    # Тестові дані
    test_ingredient = "AHCC"
    test_synonyms = ["Active Hexose Correlated Compound", "shiitake extract"]

    print("=== ТЕСТУВАННЯ НОВОЇ АРХІТЕКТУРИ ПОШУКУ ===\n")

    # Тест 1: Пошук джерела отримання (стовпчик B)
    print("1. ТЕСТ: Biological Source (стовпчик B)")
    print(f"Інгредієнт: {test_ingredient}")
    print(f"Синоніми: {test_synonyms}")
    print("Пошуковий запит: (\"AHCC\" OR \"Active Hexose Correlated Compound\" OR \"shiitake extract\") biological source extraction\n")

    try:
        result_source = gemini_google_searcher.search_column_specific_data(
            ingredient=test_ingredient,
            synonyms=test_synonyms,
            column_type="source_material"
        )

        print(f"Результат: {result_source.get('source_material', {})}")
        sources = result_source.get('google_sources', [])
        print(f"Знайдено джерел: {len(sources)}")

        # Показуємо L1-L4 розподіл
        l1_count = len([s for s in sources if s.get('priority_level') == 1])
        l2_count = len([s for s in sources if s.get('priority_level') == 2])
        l3_count = len([s for s in sources if s.get('priority_level') == 3])
        l4_count = len([s for s in sources if s.get('priority_level') == 4])

        print(f"L1 джерела: {l1_count}, L2: {l2_count}, L3: {l3_count}, L4: {l4_count}")

        # Показуємо топ-3 джерела
        top_sources = sources[:3]
        for i, source in enumerate(top_sources, 1):
            print(f"  {i}. L{source.get('priority_level', '?')}: {source.get('title', 'No title')[:60]}...")

    except Exception as e:
        print(f"ПОМИЛКА в тесті biological source: {e}")

    print("\n" + "="*60 + "\n")

    # Тест 2: Пошук активних сполук (стовпчик C)
    print("2. ТЕСТ: Active Compounds (стовпчик C)")
    print("Пошуковий запит: (\"AHCC\" OR \"Active Hexose Correlated Compound\" OR \"shiitake extract\") active compounds chemical\n")

    try:
        result_compounds = gemini_google_searcher.search_column_specific_data(
            ingredient=test_ingredient,
            synonyms=test_synonyms,
            column_type="active_compounds"
        )

        print(f"Результат: {result_compounds.get('active_compounds', [])}")
        sources = result_compounds.get('google_sources', [])
        print(f"Знайдено джерел: {len(sources)}")

        # L1-L4 розподіл
        l1_count = len([s for s in sources if s.get('priority_level') == 1])
        l2_count = len([s for s in sources if s.get('priority_level') == 2])
        l3_count = len([s for s in sources if s.get('priority_level') == 3])
        l4_count = len([s for s in sources if s.get('priority_level') == 4])

        print(f"L1 джерела: {l1_count}, L2: {l2_count}, L3: {l3_count}, L4: {l4_count}")

    except Exception as e:
        print(f"ПОМИЛКА в тесті active compounds: {e}")

    print("\n" + "="*60 + "\n")

    # Тест 3: Пошук дозування (стовпчик D)
    print("3. ТЕСТ: Dosage (стовпчик D)")
    print("Пошуковий запит: (\"AHCC\" OR \"Active Hexose Correlated Compound\" OR \"shiitake extract\") dosage clinical recommendations\n")

    try:
        result_dosage = gemini_google_searcher.search_column_specific_data(
            ingredient=test_ingredient,
            synonyms=test_synonyms,
            column_type="dosage"
        )

        print(f"Результат: {result_dosage.get('dosage_info', {})}")
        sources = result_dosage.get('google_sources', [])
        print(f"Знайдено джерел: {len(sources)}")

        # L1-L4 розподіл
        l1_count = len([s for s in sources if s.get('priority_level') == 1])
        l2_count = len([s for s in sources if s.get('priority_level') == 2])
        l3_count = len([s for s in sources if s.get('priority_level') == 3])
        l4_count = len([s for s in sources if s.get('priority_level') == 4])

        print(f"L1 джерела: {l1_count}, L2: {l2_count}, L3: {l3_count}, L4: {l4_count}")

    except Exception as e:
        print(f"ПОМИЛКА в тесті dosage: {e}")

    print("\n=== ТЕСТУВАННЯ ЗАВЕРШЕНО ===")

if __name__ == "__main__":
    test_column_specific_search()