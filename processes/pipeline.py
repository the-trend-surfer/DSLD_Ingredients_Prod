#!/usr/bin/env python3
"""
🔄 MAIN PIPELINE - DLSD Evidence Collector
Відновлений STAGES-BASED пайплайн який працював:
- Stage 0: Normalizer (normalizer.py)
- Stage 1: Searcher (searcher.py)
- Stage 2: Judge (judge.py)
- Stage 4: Table Extractor (table_extractor_experimental.py)
- Адаптований для A-G стовпчиків згідно з CLAUDE.md
"""
import sys
import os
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# Fix Windows encoding issues
if sys.platform == "win32":
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    except AttributeError:
        pass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processes.normalizer import normalizer
from processes.searcher import searcher
from processes.judge import judge
from processes.table_extractor_experimental import ExperimentalTableExtractor
from modules.sheets_writer import sheets_writer
from config import Config

class EvidencePipeline:
    """Відновлений stages-based пайплайн з A-G форматом виводу"""

    def __init__(self):
        self.pipeline_stats = {
            'total_processed': 0,
            'normalizer_success': 0,
            'searcher_success': 0,
            'judge_success': 0,
            'extraction_success': 0,
            'sheets_written': 0
        }

        # Ініціалізуємо table extractor
        self.table_extractor = ExperimentalTableExtractor()

    def initialize_sheets(self) -> bool:
        """Ініціалізує Google Sheets для запису результатів"""
        try:
            # Sheets Writer вже ініціалізований при імпорті
            return sheets_writer.service is not None
        except Exception as e:
            print(f"[ERROR] Failed to initialize sheets: {e}")
            return False

    def process_ingredient(self, ingredient: str, synonyms: Optional[List[str]] = None,
                          existing_links: Optional[List[str]] = None, ai_model: str = None) -> Dict[str, Any]:
        """
        ВІДНОВЛЕНИЙ STAGES-BASED ПАЙПЛАЙН який працював раніше

        Args:
            ingredient: Назва інгредієнта
            synonyms: Список синонімів
            existing_links: Існуючі посилання зі стовпчика G
            ai_model: Конкретна AI модель для використання

        Returns:
            Структуровані дані для Google Sheets A-G стовпчиків
        """
        start_time = time.time()
        print(f"[STAGES-PIPELINE] Processing: {ingredient}")

        try:
            # STAGE 0: NORMALIZER - переклад українською та нормалізація
            print(f"[STAGE 0] Normalizing {ingredient}...")
            normalized_data = normalizer.normalize(ingredient, synonyms)
            if normalized_data:
                self.pipeline_stats['normalizer_success'] += 1
                print(f"[STAGE 0 OK] Normalized: {normalized_data.get('taxon', {}).get('uk', ingredient)}")
            else:
                print(f"[STAGE 0 FALLBACK] Using original ingredient name")
                normalized_data = {"ingredient": ingredient, "class": "unknown", "taxon": {"uk": ingredient, "lat": ingredient}}

            # STAGE 1: SEARCHER - генерація пошукових запитів та збір кандидатів L1-L4
            print(f"[STAGE 1] Searching for candidates...")
            search_result = searcher.search_ingredient(normalized_data, synonyms)
            if search_result and search_result.get('candidates'):
                self.pipeline_stats['searcher_success'] += 1
                candidates = search_result['candidates']
                print(f"[STAGE 1 OK] Found {len(candidates)} candidate sources")
            else:
                print(f"[STAGE 1 WARNING] No candidates found")
                candidates = []

            # STAGE 2: JUDGE - рангування джерел за L1-L4 політикою
            print(f"[STAGE 2] Judging {len(candidates)} candidates...")
            judge_result = judge.judge_candidates(candidates)
            if judge_result and judge_result.get('accepted'):
                self.pipeline_stats['judge_success'] += 1
                accepted_sources = judge_result['accepted']
                print(f"[STAGE 2 OK] {len(accepted_sources)} sources accepted")
            else:
                print(f"[STAGE 2 WARNING] No sources accepted")
                accepted_sources = []

            # STAGE 4: TABLE EXTRACTOR - витягування даних у табличний формат
            print(f"[STAGE 4] Extracting table data from {len(accepted_sources)} sources...")
            table_result = self.table_extractor.extract_for_table_with_separate_bcd_cycles(
                normalized_data,
                accepted_sources,
                synonyms=synonyms,
                existing_links=existing_links,
                ai_model=ai_model
            )

            if table_result:
                self.pipeline_stats['extraction_success'] += 1
                print(f"[STAGE 4 OK] Table data extracted successfully")
            else:
                print(f"[STAGE 4 WARNING] Table extraction failed")
                table_result = {}

            # АДАПТАЦІЯ ДО A-G ФОРМАТУ - конвертуємо результат table_extractor у A-G стовпчики
            print(f"[DEBUG] Table extractor returned: {list(table_result.keys()) if table_result else 'None'}")
            if table_result:
                for key, value in table_result.items():
                    print(f"[DEBUG] {key}: {value}")
            result = self._convert_table_result_to_ag_format(ingredient, normalized_data, table_result)

            # ЗАПИС В GOOGLE SHEETS
            print(f"[SHEETS] Writing to Google Sheets...")
            try:
                table_data = {
                    'ingredient': ingredient,
                    'A_nazva_ukrainska': result['A_nazva_ukrainska'],
                    'B_dzherelo_otrymannya': result['B_dzherelo_otrymannya'],
                    'C_aktyvni_spoluky': result['C_aktyvni_spoluky'],
                    'D_dozuvannya': result['D_dozuvannya'],
                    'E_riven_dokaziv': result['E_riven_dokaziv'],
                    'F_tsytaty': result['F_tsytaty'],
                    'G_dzherela': result['G_dzherela']
                }

                sheets_written = sheets_writer.write_table_result(table_data)
                if sheets_written:
                    self.pipeline_stats['sheets_written'] += 1
                    print(f"[SHEETS OK] Written to Google Sheets")
                else:
                    print(f"[SHEETS WARNING] Failed to write to Google Sheets")
            except Exception as e:
                print(f"[SHEETS ERROR] {e}")

            # СТАТИСТИКА
            processing_time = round(time.time() - start_time, 1)
            self.pipeline_stats['total_processed'] += 1

            has_ukrainian = bool(result['A_nazva_ukrainska'])
            has_source = bool(result['B_dzherelo_otrymannya'])
            has_compounds = bool(result['C_aktyvni_spoluky'])
            has_dosage = bool(result['D_dozuvannya'])
            has_citations = bool(result['F_tsytaty'])

            print(f"[STATS] Time: {processing_time}s | UA: {'✓' if has_ukrainian else '✗'} | Source: {'✓' if has_source else '✗'} | Compounds: {'✓' if has_compounds else '✗'} | Dose: {'✓' if has_dosage else '✗'} | Citations: {'✓' if has_citations else '✗'} | Level: {result['E_riven_dokaziv']}")

            return result

        except Exception as e:
            print(f"[STAGES-PIPELINE ERROR] Failed for {ingredient}: {e}")
            # Повертаємо базовий результат з помилкою
            return self._create_fallback_ag_result(ingredient, str(e))

    def _convert_table_result_to_ag_format(self, ingredient: str, normalized_data: Dict[str, Any], table_result: Dict[str, Any]) -> Dict[str, Any]:
        """Конвертує результат table_extractor у A-G формат"""

        # Пріоритет назв: 1) table_result з AI, 2) normalized_data, 3) fallback
        a_nazva = ""

        # 1. Спочатку перевіряємо назву з table_result (AI переклад)
        if table_result.get('nazva_ukr_orig') and table_result['nazva_ukr_orig'].strip():
            a_nazva = table_result['nazva_ukr_orig']

        # 2. Якщо немає - використовуємо normalized_data
        elif normalized_data.get('taxon', {}).get('uk'):
            uk_name = normalized_data['taxon']['uk']
            if uk_name != ingredient and '(' not in uk_name:
                a_nazva = f"{uk_name} ({ingredient})"

        # 3. Fallback - створюємо базовий переклад для відомих абревіатур
        if not a_nazva:
            # Простий переклад для популярних інгредієнтів
            translations = {
                "AHCC": "АХЦЦ (AHCC)",
                "CoQ10": "Коензим Q10 (CoQ10)",
                "ATP": "АТФ (ATP)",
                "DNA": "ДНК (DNA)",
                "RNA": "РНК (RNA)",
                "EPA": "ЕПК (EPA)",
                "DHA": "ДГК (DHA)"
            }
            a_nazva = translations.get(ingredient, f"{ingredient} ({ingredient})")

        result = {
            'A_nazva_ukrainska': a_nazva,  # З normalized_data або table_result
            'B_dzherelo_otrymannya': table_result.get('dzherelo_syrovyny', ''),  # Джерело сировини
            'C_aktyvni_spoluky': self._format_compounds(table_result.get('aktyvni_spoluky', [])),  # Активні сполуки
            'D_dozuvannya': table_result.get('dobova_norma', ''),  # Дозування
            'E_riven_dokaziv': self._determine_evidence_level(table_result),  # Рівень доказів
            'F_tsytaty': self._format_citations(table_result.get('dzherela_tsytaty', [])),  # Цитати з URL
            'G_dzherela': ''  # Порожній, оскільки URL тепер в стовпчику F
        }

        return result

    def _format_compounds(self, compounds: List[str]) -> str:
        """Форматує активні сполуки у строку"""
        if not compounds:
            return ''

        # Якщо вже є строка, повертаємо як є
        if isinstance(compounds, str):
            return compounds

        # Конвертуємо список у строку
        return ', '.join(compounds[:5])  # Максимум 5 сполук

    def _format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Форматує цитати з URL у строку для стовпчика F"""
        if not citations:
            return ''

        # Якщо вже є строка, повертаємо як є
        if isinstance(citations, str):
            return citations

        formatted = []
        for citation in citations[:3]:  # Максимум 3 цитати
            if isinstance(citation, dict):
                quote = citation.get('quote', '')
                url = citation.get('url', '')

                if quote and len(quote) > 10:  # Мінімальна довжина цитати
                    # Формат: "цитата (URL)"
                    citation_text = quote[:100]  # Обрізаємо довгі цитати
                    if url:
                        citation_text += f" ({url})"
                    formatted.append(citation_text)
            elif isinstance(citation, str):
                formatted.append(citation[:100])

        return '; '.join(formatted)

    def _format_sources(self, sources: List[str]) -> str:
        """Форматує джерела у строку для стовпчика G"""
        if not sources:
            return ''

        # Якщо вже є строка, повертаємо як є
        if isinstance(sources, str):
            return sources

        # Фільтруємо валідні URL
        valid_urls = []
        for source in sources[:3]:  # Максимум 3 URL
            if isinstance(source, str) and ('http' in source or 'doi:' in source):
                valid_urls.append(source)

        return '; '.join(valid_urls)

    def _extract_urls_from_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Витягує URL з цитат для стовпчика G"""
        if not citations:
            return ''

        # Якщо вже є строка, повертаємо як є
        if isinstance(citations, str):
            return citations

        # Витягуємо URL з цитат
        urls = []
        for citation in citations[:3]:  # Максимум 3 URL
            if isinstance(citation, dict):
                url = citation.get('url', '')
                if url and 'http' in url:
                    urls.append(url)

        return '; '.join(urls)

    def _determine_evidence_level(self, table_result: Dict[str, Any]) -> str:
        """Визначає рівень доказів на основі джерел"""
        # Витягуємо URL з цитат для визначення рівня
        citations = table_result.get('dzherela_tsytaty', [])
        sources = []

        for citation in citations:
            if isinstance(citation, dict):
                url = citation.get('url', '')
                if url:
                    sources.append(url)

        # Якщо немає URL в цитатах, використовуємо sources
        if not sources:
            sources = table_result.get('sources', [])

        # Перевіряємо найкращі домени для L1-L4
        for source in sources:
            if isinstance(source, str):
                if any(domain in source.lower() for domain in ['pubmed', 'ncbi.nlm.nih.gov', 'efsa.europa.eu']):
                    return 'L1'
                elif any(domain in source.lower() for domain in ['nature.com', 'sciencedirect.com']):
                    return 'L2'
                elif any(domain in source.lower() for domain in ['examine.com', 'wiley.com']):
                    return 'L3'

        return 'L4'  # За замовчуванням

    def _create_fallback_ag_result(self, ingredient: str, error_msg: str) -> Dict[str, Any]:
        """Створює fallback результат у A-G форматі"""
        return {
            'A_nazva_ukrainska': f"{ingredient} ({ingredient})",
            'B_dzherelo_otrymannya': '',
            'C_aktyvni_spoluky': '',
            'D_dozuvannya': '',
            'E_riven_dokaziv': 'L4',
            'F_tsytaty': f'Помилка обробки: {error_msg[:100]}',
            'G_dzherela': ''
        }

    def get_pipeline_stats(self) -> Dict[str, int]:
        """Повертає статистику роботи пайплайна"""
        return self.pipeline_stats.copy()

# Глобальний екземпляр
pipeline = EvidencePipeline()