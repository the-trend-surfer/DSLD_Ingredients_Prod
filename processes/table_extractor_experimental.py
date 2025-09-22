"""
EXPERIMENTAL Table Extractor - Gemini Google Search як пріоритет #1
"""
import json
import requests
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import time

from modules.multi_ai_client import multi_ai_client
from modules.ncbi_client import ncbi_client
from modules.gemini_google_search import gemini_google_searcher
from config import Config
from processes.ai_prompts import TablePrompts
from processes.table_schema import TABLE_OUTPUT_SCHEMA
from processes.source_policy import source_policy

class ExperimentalTableExtractor:
    """EXPERIMENTAL Extractor з Gemini Google Search як пріоритетом"""

    def __init__(self):
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        return """Ти експерт з харчових добавок. Витягуй точні дані для таблиці з 5 стовпчиків:

1. Назва українською [Оригінальна назва]
2. Джерело сировини (частина рослини/організму)
3. Активні сполуки (тільки підтверджені)
4. Добова норма (конкретне значення або порожнє поле)
5. Джерела та цитати

Повертай тільки JSON згідно схеми."""

    def extract_for_table_experimental(self, normalized_data: Dict[str, Any], accepted_sources: List[Dict[str, Any]], synonyms: Optional[List[str]] = None, existing_links: Optional[List[str]] = None, ai_model: Optional[str] = None) -> Dict[str, Any]:
        """
        ЕКСПЕРИМЕНТАЛЬНА ВЕРСІЯ з ПРАВИЛЬНОЮ ПРІОРИТИЗАЦІЄЮ:
        1. PubMed/NCBI (L1)
        2. Прямі L1 джерела
        3. L2 джерела
        4. Gemini Google Search з L1-L4 фільтрацією
        5. Інші джерела
        """
        try:
            # Витягуємо назву інгредієнта з будь-якого формату
            if isinstance(normalized_data, dict):
                ingredient = normalized_data.get("ingredient") or normalized_data.get("name") or str(normalized_data)
            else:
                ingredient = str(normalized_data)

            print(f"[EXPERIMENTAL] Extracting table data for {ingredient}...")

            # Ініціалізуємо результат (порожній на початку)
            final_result = self._create_empty_table_result(ingredient)
            sources_tried = []

            # 🔗 ЕТАП 1: EXISTING LINKS (спеціалізовані джерела)
            if existing_links:
                print(f"[STAGE-1] Processing {len(existing_links)} existing links...")
                documents = []
                for link in existing_links:
                    doc = self._download_single_document(link)
                    if doc and self._is_relevant_content(doc.get('text', ''), ingredient):
                        documents.append(doc)

                if documents:
                    print(f"[EXISTING-DATA] Found {len(documents)} relevant existing documents")
                    existing_table = self._extract_with_table_ai(ingredient, documents, ai_model)
                    if existing_table:
                        final_result = self._merge_table_results(final_result, existing_table, "Existing Links")
                        sources_tried.append("Existing Links")

            # 📚 ЕТАП 2: PUBMED/NCBI ПЕРШИЙ! (L1 - найвища якість)
            print(f"[STAGE-2] Searching PubMed/NCBI (L1 priority)...")
            all_names = [ingredient]
            if synonyms:
                all_names.extend(synonyms[:2])

            ncbi_articles = self._get_ncbi_articles(all_names)
            if ncbi_articles:
                print(f"[PUBMED-L1] Found {len(ncbi_articles)} PubMed articles")
                ncbi_table = self._extract_with_table_ai(ingredient, ncbi_articles[:3], ai_model)
                if ncbi_table:
                    final_result = self._merge_table_results(final_result, ncbi_table, "PubMed L1")
                    sources_tried.append("PubMed L1")

            # 🏛️ ЕТАП 3: ПРЯМІ L1 ДЖЕРЕЛА (NIH, EFSA, FDA)
            print(f"[STAGE-3] Checking direct L1 sources...")
            l1_direct_results = self._check_direct_l1_sources(ingredient, synonyms, ai_model)
            if l1_direct_results:
                final_result = self._merge_table_results(final_result, l1_direct_results, "Direct L1")
                sources_tried.append("Direct L1")

            # 🔬 ЕТАП 4: L2 ДЖЕРЕЛА (Nature, ScienceDirect)
            print(f"[STAGE-4] Checking L2 academic sources...")
            l2_results = self._check_l2_sources(ingredient, synonyms, ai_model)
            if l2_results:
                final_result = self._merge_table_results(final_result, l2_results, "L2 Academic")
                sources_tried.append("L2 Academic")

            # 🔍 ЕТАП 5: ПЕРЕВІРКА НЕОБХІДНОСТІ GEMINI
            completion_stats = self._calculate_completion_stats(final_result)
            print(f"[COMPLETION-CHECK] Current completion: {completion_stats['percentage']:.1f}%")

            # Якщо дані неповні, використовуємо ЦІЛЬОВИЙ Gemini пошук з site: операторами
            if completion_stats['percentage'] < 30:  # Якщо менше 30% заповнено
                print(f"[STAGE-5] Data incomplete ({completion_stats['percentage']:.1f}%), using TARGETED Gemini search...")

                try:
                    # PHASE 1: Цільовий пошук по L1-L4 сайтах з site: операторами
                    missing_fields = self._check_missing_critical_fields(final_result)
                    print(f"[TARGETED] Missing critical fields: {missing_fields}")

                    google_result = self._targeted_gemini_search_with_sites(ingredient, synonyms, missing_fields)

                    if google_result and google_result.get('search_method') != 'gemini_google_search_failed':
                        # Перевіряємо чи знайшли критичні поля
                        filtered_google_data = self._filter_google_results_by_l1_l4(google_result, ingredient)

                        if filtered_google_data:
                            final_result = self._merge_table_results(final_result, filtered_google_data, "Gemini Targeted")
                            sources_tried.append("Gemini Targeted")
                            print(f"[GEMINI-SUPPLEMENT] Added targeted Gemini data")
                        else:
                            print(f"[GEMINI-FILTERED] No L1-L4 sources found in Gemini results")
                    else:
                        print(f"[GEMINI-FAILED] Google Search failed or returned no results")

                except Exception as e:
                    print(f"[GEMINI-ERROR] Google Search error: {e}")
            else:
                print(f"[GEMINI-SKIP] Data complete enough ({completion_stats['percentage']:.1f}% >= 30%), skipping Gemini")

            # 🔍 ЕТАП 6: ПЕРЕВІРКА ПРОПУЩЕНИХ КОЛОНОК
            missing_fields = self._check_missing_fields(final_result)
            if missing_fields:
                print(f"[STAGE-6] Missing fields: {missing_fields}, trying additional sources...")
                additional_result = self._fill_missing_fields(ingredient, missing_fields, synonyms, ai_model)
                if additional_result:
                    final_result = self._merge_table_results(final_result, additional_result, "Additional Sources")
                    sources_tried.append("Additional Sources")

            # 📊 ФІНАЛЬНА СТАТИСТИКА
            final_completion_stats = self._calculate_completion_stats(final_result)
            print(f"[FINAL-STATS] {final_completion_stats['percentage']:.1f}% complete - Sources used: {', '.join(sources_tried) if sources_tried else 'None'}")

            return final_result

        except Exception as e:
            print(f"[ERROR] Experimental extraction failed for {ingredient}: {e}")
            return self._create_empty_table_result(ingredient)

    def _merge_table_results(self, current_result: Dict[str, Any], new_result: Dict[str, Any], source_name: str) -> Dict[str, Any]:
        """Об'єднує два результати таблиці, заповнюючи пропущені поля"""
        try:
            merged = current_result.copy()

            # 1. Назва українською [Оригінальна назва]
            if not merged.get('nazva_ukr_orig') and new_result.get('nazva_ukr_orig'):
                merged['nazva_ukr_orig'] = new_result['nazva_ukr_orig']
                print(f"[MERGE] Added name from {source_name}")

            # 2. Джерело сировини
            if not merged.get('dzherelo_syrovyny') and new_result.get('dzherelo_syrovyny'):
                merged['dzherelo_syrovyny'] = new_result['dzherelo_syrovyny']
                print(f"[MERGE] Added source material from {source_name}")

            # 3. Активні сполуки (об'єднуємо, видаляємо дублікати)
            current_compounds = merged.get('aktyvni_spoluky', [])
            new_compounds = new_result.get('aktyvni_spoluky', [])

            if new_compounds:
                # Об'єднуємо та видаляємо дублікати (порівнюємо нижнім регістром)
                combined_compounds = current_compounds.copy()
                current_lower = [c.lower() for c in current_compounds]

                for compound in new_compounds:
                    if compound.lower() not in current_lower:
                        combined_compounds.append(compound)
                        current_lower.append(compound.lower())

                if len(combined_compounds) > len(current_compounds):
                    merged['aktyvni_spoluky'] = combined_compounds[:10]  # Максимум 10 сполук
                    print(f"[MERGE] Added {len(combined_compounds) - len(current_compounds)} compounds from {source_name}")

            # 4. Добова норма (приоритет непорожнім значенням)
            if not merged.get('dobova_norma') and new_result.get('dobova_norma'):
                merged['dobova_norma'] = new_result['dobova_norma']
                print(f"[MERGE] Added dosage from {source_name}")

            # 5. Джерела та цитати (об'єднуємо)
            current_citations = merged.get('dzherela_tsytaty', [])
            new_citations = new_result.get('dzherela_tsytaty', [])

            if new_citations:
                # Об'єднуємо цитати, перевіряючи дублікати за URL
                combined_citations = current_citations.copy()
                current_urls = [c.get('url', '') for c in current_citations]

                for citation in new_citations:
                    if citation.get('url', '') not in current_urls:
                        combined_citations.append(citation)
                        current_urls.append(citation.get('url', ''))

                if len(combined_citations) > len(current_citations):
                    merged['dzherela_tsytaty'] = combined_citations[:5]  # Максимум 5 цитат
                    print(f"[MERGE] Added {len(combined_citations) - len(current_citations)} citations from {source_name}")

            return merged

        except Exception as e:
            print(f"[MERGE-ERROR] Failed to merge results from {source_name}: {e}")
            return current_result

    def _check_missing_fields(self, result: Dict[str, Any]) -> List[str]:
        """Перевіряє які поля відсутні або порожні"""
        missing = []

        if not result.get('nazva_ukr_orig'):
            missing.append('name')

        if not result.get('dzherelo_syrovyny'):
            missing.append('source_material')

        if not result.get('aktyvni_spoluky') or len(result.get('aktyvni_spoluky', [])) == 0:
            missing.append('compounds')

        if not result.get('dobova_norma'):
            missing.append('dosage')

        if not result.get('dzherela_tsytaty') or len(result.get('dzherela_tsytaty', [])) == 0:
            missing.append('citations')

        return missing

    def _calculate_completion_stats(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Обчислює статистику заповненості полів"""
        total_fields = 5
        filled_fields = 0

        if result.get('nazva_ukr_orig'):
            filled_fields += 1

        if result.get('dzherelo_syrovyny'):
            filled_fields += 1

        if result.get('aktyvni_spoluky') and len(result.get('aktyvni_spoluky', [])) > 0:
            filled_fields += 1

        if result.get('dobova_norma'):
            filled_fields += 1

        if result.get('dzherela_tsytaty') and len(result.get('dzherela_tsytaty', [])) > 0:
            filled_fields += 1

        percentage = (filled_fields / total_fields) * 100

        return {
            'filled_fields': filled_fields,
            'total_fields': total_fields,
            'percentage': percentage,
            'missing_fields': self._check_missing_fields(result)
        }

    def _fill_missing_fields(self, ingredient: str, missing_fields: List[str], synonyms: Optional[List[str]], ai_model: Optional[str]) -> Dict[str, Any]:
        """Намагається заповнити пропущені поля з додаткових джерел"""
        try:
            print(f"[ADDITIONAL] Trying to fill missing: {', '.join(missing_fields)}")

            # Для пропущених полів можемо спробувати:
            # 1. Wikipedia (часто має базову інформацію)
            # 2. Спеціалізовані запити NCBI
            # 3. Загальні енциклопедичні джерела

            additional_sources = []

            # Wikipedia як універсальне джерело
            if 'name' in missing_fields or 'source_material' in missing_fields:
                wiki_urls = [
                    f"https://en.wikipedia.org/wiki/{ingredient.replace(' ', '_')}",
                    f"https://uk.wikipedia.org/wiki/{ingredient.replace(' ', '_')}"
                ]

                for url in wiki_urls:
                    doc = self._download_single_document(url)
                    if doc and self._is_relevant_content(doc.get('text', ''), ingredient):
                        additional_sources.append(doc)
                        break  # Беремо тільки одну Wikipedia статтю

            # Спеціалізовані NCBI запити для сполук і дозування
            if 'compounds' in missing_fields or 'dosage' in missing_fields:
                specialized_queries = [
                    f'"{ingredient}" AND (chemical composition OR active compounds)',
                    f'"{ingredient}" AND (dosage OR dose OR recommended amount)'
                ]

                for query in specialized_queries:
                    try:
                        pubmed_ids = ncbi_client.search_pubmed(query, max_results=2)
                        if pubmed_ids:
                            for pmid in pubmed_ids:
                                article_data = ncbi_client.fetch_article_details(pmid)
                                if article_data:
                                    additional_sources.append({
                                        'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                                        'text': article_data.get('abstract', ''),
                                        'title': article_data.get('title', '')
                                    })
                                    break  # Беремо тільки одну статтю на запит
                    except Exception as e:
                        print(f"[ADDITIONAL-NCBI] Specialized query failed: {e}")
                        continue

            # Обробляємо додаткові джерела
            if additional_sources:
                print(f"[ADDITIONAL] Found {len(additional_sources)} additional sources")
                return self._extract_with_table_ai(ingredient, additional_sources[:2], ai_model)

            return None

        except Exception as e:
            print(f"[ADDITIONAL-ERROR] Failed to fill missing fields: {e}")
            return None

    def _convert_google_result_to_table_ukrainian(self, google_result: Dict[str, Any], ingredient: str) -> Dict[str, Any]:
        """Конвертує результат Google Search в формат таблиці з українською мовою через AI"""
        try:
            # Використовуємо AI для правильного перекладу та форматування
            raw_response = google_result.get('raw_response', '')
            google_sources = google_result.get('google_sources', [])

            if not raw_response:
                return self._create_empty_table_result(ingredient)

            # Підготовка контенту з джерел для кращих цитат
            sources_content = ""
            valid_sources = []

            print(f"[DEBUG] Processing {len(google_sources)} Google sources for citations")

            # Gemini не повертає content у google_sources, використовуємо raw_response
            if raw_response and len(raw_response) > 100:
                print(f"[DEBUG] Using Gemini raw_response as content source: {len(raw_response)} chars")
                sources_content = f"\nГлавное содержание от Gemini Google Search:\n{raw_response[:1000]}\n"

                # Створюємо джерела з конвертованих URLs
                for i, source in enumerate(google_sources[:3]):
                    url = source.get('url', '')
                    title = source.get('title', '')

                    # Конвертуємо VertexAI URL в читабельний з конкретною сторінкою
                    converted_url = self._convert_vertexai_to_real_url(url, title, ingredient)

                    valid_sources.append({
                        'url': converted_url,
                        'content': f"Content from Gemini analysis: {title}",
                        'title': title
                    })
                    print(f"[DEBUG] Added Google source: {title} -> {converted_url}")
            else:
                print(f"[DEBUG] No useful raw_response from Gemini: {len(raw_response)} chars")

            print(f"[DEBUG] Found {len(valid_sources)} Google sources")

            # Створюємо український промпт для обробки Google результатів
            ukrainian_prompt = f"""Обробі дані про інгредієнт {ingredient} з Google Search результатів. ОБОВ'ЯЗКОВО українською мовою.

ВИХІДНІ ДАНІ З GOOGLE:
{raw_response[:1000]}

ДОДАТКОВИЙ КОНТЕНТ З ДЖЕРЕЛ:
{sources_content[:1000]}

⚠️ КРИТИЧНО ВАЖЛИВО ДЛЯ ЦИТАТ:
❌ ЗАБОРОНЕНО використовувати назви доменів як цитати: "ahcc.net", "wikipedia.org", "pubmed.ncbi.nlm.nih.gov"
❌ ЗАБОРОНЕНО використовувати назви сайтів, URL або домени в якості цитат
❌ ЗАБОРОНЕНО додавати інформацію про вітамін D, мінерали або інші речовини НЕ пов'язані з {ingredient}
✅ ОБОВ'ЯЗКОВО витягуй конкретні РЕЧЕННЯ з контенту джерел вище
✅ Використовуй тільки фактичну інформацію про {ingredient}
✅ Цитати мають бути реальними реченнями з тексту, наприклад: "AHCC shows immunomodulatory effects in clinical studies"
✅ Якщо немає хорошого контенту - краще залишити цитати порожніми

ЗАВДАННЯ - створи таблицю з 5 стовпчиків у ТОЧНОМУ форматі:

1. Назва українською [Оригінальна назва] - приклади: "β-ситостерин (β-Sitosterol)", "Лецитин (фосфатиділхолін) (Lecithin)"

2. Джерело сировини - ТОЧНИЙ формат як у прикладах:
   ✅ "Соя, морква, інжир, коріандр, дягель лікарський корені, плоди (Angelica archangelica)"
   ✅ "Олії рослинні (соєва, оливкова, зародків пшениці), Мака перуанська коренеплоди (Lepidium meyenii)"
   ✅ "Субпродукти тваринного походження (продукт гідролізу хрящової тканини птиці, тварин, морських організмів)"
   ✅ "Молоко, риба, м'ясо (або отриманий шляхом біотехнологічного синтезу)"

3. Активні сполуки - українською з англійською в дужках: "Гіалуронова кислота (Hyaluronic acid)"

4. Добова норма - тільки цифри та одиниці з тексту

5. Джерела та цитати - точні цитати з тексту

ОБОВ'ЯЗКОВІ ПРАВИЛА ФОРМАТУ:
✅ Українські назви їжі: соя, морква, помідори, яблука (НЕ "соєві боби")
✅ Частини рослин: корені, листя, квітки, плоди, насіння
✅ Латинські назви в дужках: (Angelica archangelica), (Lepidium meyenii)
✅ Обробка: олії рослинні, продукт гідролізу, біотехнологічний синтез
✅ Для синтетичних: "або отриманий шляхом біотехнологічного синтезу"
✅ Розділення комами між джерелами

JSON формат:
{{
  "nazva_ukr_orig": "Українська назва [Original Name]",
  "dzherelo_syrovyny": "український організм; українська частина",
  "aktyvni_spoluky": ["українські назви сполук"],
  "dobova_norma": "дозування" або "",
  "dzherela_tsytaty": [...]
}}

Відповідай ТІЛЬКИ JSON."""

            # Викликаємо AI для правильної обробки
            response = self._call_ai_direct(ukrainian_prompt, "openai")  # Використовуємо OpenAI для поширених українських назв

            if response and '{' in response:
                data = self._extract_json_from_response(response)
                if data and self._validate_table_data(data):
                    print(f"[OK] AI generated Ukrainian data for {ingredient}")

                    # ПОВНІСТЮ ІГНОРУЄМО AI цитати - використовуємо ТІЛЬКИ Gemini raw_response!
                    print(f"[CITATIONS] Ignoring AI citations, using ONLY Gemini raw_response")
                    improved_citations = []

                    # Витягуємо реальні цитати з Gemini response
                    real_quotes = self._extract_real_quotes_from_response(raw_response, 0)
                    print(f"[CITATIONS] Extracted {len(real_quotes)} real quotes from Gemini")

                    for i, real_quote in enumerate(real_quotes[:3]):
                        if len(real_quote) > 30:
                            # Знаходимо відповідне джерело з реальним URL
                            source_url = ""
                            source_title = ""
                            if i < len(valid_sources):
                                source = valid_sources[i]
                                original_url = source.get('url', '')
                                source_title = source.get('title', '')
                                # Декодуємо реальний URL
                                real_url = self._convert_vertexai_to_real_url(original_url, source_title, ingredient)
                                source_url = real_url if real_url else original_url
                            else:
                                source_url = "https://scholar.google.com"  # L1 джерело для додаткових цитат

                            improved_citations.append({
                                'url': source_url,
                                'quote': real_quote,
                                'type': 'Google Search - Gemini real content'
                            })
                            print(f"[OK] Citation {i+1}: {real_quote[:50]}... | URL: {source_url[:40]}...")

                    # Якщо мало цитат з Gemini - додаємо з реального контенту джерел
                    if len(improved_citations) < 2 and valid_sources:
                        print(f"[CITATIONS] Adding backup citations from source content")
                        for source in valid_sources[:3-len(improved_citations)]:
                            content_text = source.get('content', '').strip()
                            if len(content_text) > 50 and not content_text.endswith('.com'):
                                # Беремо першу змістовну частину контенту як цитату
                                quote_text = content_text[:150] + "..." if len(content_text) > 150 else content_text
                                real_url = self._convert_vertexai_to_real_url(source.get('url', ''), source.get('title', ''), ingredient)

                                improved_citations.append({
                                    'url': real_url if real_url else source.get('url', ''),
                                    'quote': quote_text,
                                    'type': 'Google Search - source content extract'
                                })
                                print(f"[OK] Backup citation: {quote_text[:50]}...")

                    data['dzherela_tsytaty'] = improved_citations
                    print(f"[FINAL] Total real citations: {len(improved_citations)}")

                    return data
                else:
                    print(f"[ERROR] AI response validation failed for {ingredient}")
            else:
                print(f"[ERROR] No valid JSON in AI response for {ingredient}")

            return self._create_empty_table_result(ingredient)

        except Exception as e:
            print(f"[ERROR] Ukrainian Google result conversion failed: {e}")
            return self._create_empty_table_result(ingredient)

    def _convert_google_result_to_table(self, google_result: Dict[str, Any], ingredient: str) -> Dict[str, Any]:
        """Конвертує результат Google Search в формат таблиці"""
        try:
            # Витягуємо дані з Google результату
            source_material = google_result.get('source_material', {})
            active_compounds = google_result.get('active_compounds', [])
            dosage_info = google_result.get('dosage_info', {})
            google_sources = google_result.get('google_sources', [])

            # Формуємо назву (тільки з реальними даними)
            scientific_name = source_material.get('scientific_name', '')
            if scientific_name and scientific_name not in ['scientific name', 'various', 'unknown']:
                nazva = f"{ingredient} [{scientific_name}]"
            else:
                nazva = ingredient  # Без шаблонного тексту

            # Формуємо джерело сировини (тільки якщо є конкретні дані)
            organism = source_material.get('organism', '')
            part_used = source_material.get('part_used', '')
            kingdom = source_material.get('kingdom', '')

            dzherelo_parts = []
            # Додаємо тільки змістовні дані
            if organism and organism not in ['organism', 'extract', 'various']:
                dzherelo_parts.append(organism)
            if part_used and part_used not in ['part', 'root', 'extract', 'various']:
                dzherelo_parts.append(part_used)

            # Якщо немає конкретних даних, залишаємо порожнім
            dzherelo_syrovyny = '; '.join(dzherelo_parts) if dzherelo_parts else ""

            # Формуємо активні сполуки (тільки реальні дані з джерел)
            aktyvni_spoluky = []
            for compound in active_compounds[:5]:  # Максимум 5 сполук
                compound_name = compound.get('name', '')
                concentration = compound.get('concentration', '')
                if compound_name:
                    if concentration and concentration != 'not specified':
                        aktyvni_spoluky.append(f"{compound_name} ({concentration})")
                    else:
                        aktyvni_spoluky.append(compound_name)

            # Формуємо дозування
            daily_dose = dosage_info.get('daily_dose', '')
            clinical_dose = dosage_info.get('clinical_dose', '')
            dobova_norma = daily_dose or clinical_dose or ""

            # Формуємо цитати з Google джерел
            dzherela_tsytaty = []
            for source in google_sources[:3]:  # Максимум 3 джерела
                url = source.get('url')
                if url:
                    # Перевіряємо пріоритет джерела (але не відкидаємо)
                    url_classification = source_policy.classify_url(url)
                    priority_level = url_classification.get('source_priority', 5)  # 5 = найнижчий пріоритет

                    # Витягуємо релевантну цитату з контенту, а не title
                    quote = ""
                    if source.get('content'):
                        # Шукаємо релевантні фрагменти про інгредієнт
                        content = source['content'][:500].lower()
                        ingredient_lower = ingredient.lower()

                        # Знаходимо речення з назвою інгредієнта
                        sentences = content.split('.')
                        for sentence in sentences:
                            if ingredient_lower in sentence or any(syn.lower() in sentence for syn in (active_compounds or [])[:3]):
                                quote = sentence.strip()[:100] + "..." if len(sentence) > 100 else sentence.strip()
                                break

                    # Fallback до title якщо немає контенту
                    if not quote and source.get('title'):
                        quote = source['title'][:50] + "..." if len(source['title']) > 50 else source['title']

                    if quote:
                        dzherela_tsytaty.append({
                            "url": url,
                            "quote": quote,
                            "type": f"L{priority_level} джерело"
                        })

            # Якщо немає цитат з Google джерел, залишаємо порожнім
            if not dzherela_tsytaty:
                dzherela_tsytaty = []

            return {
                "nazva_ukr_orig": nazva,
                "dzherelo_syrovyny": dzherelo_syrovyny,
                "aktyvni_spoluky": aktyvni_spoluky,
                "dobova_norma": dobova_norma,
                "dzherela_tsytaty": dzherela_tsytaty
            }

        except Exception as e:
            print(f"[ERROR] Google result conversion failed: {e}")
            return self._create_empty_table_result(ingredient)

    def _download_single_document(self, url: str) -> Optional[Dict[str, Any]]:
        """Завантажує один документ"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            text_content = self._extract_text_from_html(response.text)
            if text_content and len(text_content) > 100:
                return {
                    "url": url,
                    "text": text_content[:3000]
                }
            return None
        except Exception as e:
            print(f"[ERROR] Failed to download {url}: {e}")
            return None

    def _extract_text_from_html(self, html_content: str) -> str:
        """Витягує чистий текст з HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            return text
        except Exception as e:
            print(f"[ERROR] HTML parsing error: {e}")
            return ""

    def _is_relevant_content(self, text: str, ingredient: str) -> bool:
        """Перевіряє чи контент релевантний до інгредієнта"""
        if not text or len(text) < 200:
            return False
        text_lower = text.lower()
        ingredient_lower = ingredient.lower()
        return ingredient_lower in text_lower

    def _get_ncbi_articles(self, all_names: List[str]) -> List[Dict[str, Any]]:
        """Отримує статті з NCBI"""
        try:
            queries = []
            for name in all_names[:2]:
                if len(name) > 2:
                    queries.extend([
                        f'"{name}"[Title/Abstract] AND (supplement OR nutrition OR dietary)',
                        f'"{name}" AND (active compound OR bioactive OR phytochemical)'
                    ])

            queries = list(set(queries[:4]))
            print(f"[NCBI] Running {len(queries)} queries...")

            articles = ncbi_client.search_multiple_queries(queries, max_per_query=2)

            documents = []
            for article in articles:
                documents.append({
                    "url": article.get("url", ""),
                    "text": article.get("abstract", "") + " " + article.get("full_text", ""),
                    "title": article.get("title", ""),
                    "pmid": article.get("pmid", "")
                })

            print(f"[NCBI] Found {len(documents)} articles with content")
            return documents

        except Exception as e:
            print(f"[ERROR] NCBI search failed: {e}")
            return []

    def _extract_with_table_ai(self, ingredient: str, documents: List[Dict[str, Any]], ai_model: Optional[str] = None) -> Dict[str, Any]:
        """Витягує дані через AI для таблиці"""
        try:
            if not documents:
                return self._create_empty_table_result(ingredient)

            print(f"[INFO] Processing {len(documents)} documents for {ingredient}")

            for i, doc in enumerate(documents[:2], 1):
                url = doc.get('url', '')
                text = doc.get('text', '')
                title = doc.get('title', '')

                full_text = f"{title}\n\n{text}" if title else text

                if len(full_text) < 50:
                    continue

                print(f"[INFO] Document {i}: {len(full_text)} chars")

                prompt = TablePrompts.get_table_extraction_prompt(ingredient, full_text, url)
                response = self._call_ai_direct(prompt, ai_model)

                if response and '{' in response:
                    data = self._extract_json_from_response(response)
                    if data and self._validate_table_data(data):
                        print(f"[OK] Valid data extracted from document {i}")
                        return data

            return self._create_empty_table_result(ingredient)

        except Exception as e:
            print(f"[ERROR] Table AI extraction failed: {e}")
            return self._create_empty_table_result(ingredient)

    def _call_ai_direct(self, prompt: str, ai_model: Optional[str] = None) -> str:
        """Викликає AI моделі"""
        try:
            if ai_model and ai_model in multi_ai_client.available_models:
                if ai_model == 'claude':
                    return multi_ai_client._call_claude(prompt)
                elif ai_model == 'openai':
                    return multi_ai_client._call_openai(prompt)
                elif ai_model == 'gemini':
                    return multi_ai_client._call_gemini(prompt)

            # Fallback
            for model_type in ['claude', 'openai', 'gemini']:
                if model_type in multi_ai_client.available_models:
                    try:
                        if model_type == 'claude':
                            return multi_ai_client._call_claude(prompt)
                        elif model_type == 'openai':
                            return multi_ai_client._call_openai(prompt)
                        elif model_type == 'gemini':
                            return multi_ai_client._call_gemini(prompt)
                    except:
                        continue
            return ""
        except Exception as e:
            print(f"[ERROR] AI call failed: {e}")
            return ""

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Витягує JSON з відповіді AI"""
        try:
            if '```json' in response:
                start_marker = '```json'
                end_marker = '```'
                start_idx = response.find(start_marker) + len(start_marker)
                end_idx = response.find(end_marker, start_idx)
                if start_idx != -1 and end_idx != -1:
                    json_str = response[start_idx:end_idx].strip()
                    return json.loads(json_str)

            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1

            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {}

        except (json.JSONDecodeError, ValueError) as e:
            print(f"[ERROR] JSON parsing error: {e}")
            return {}

    def _validate_table_data(self, data: Dict[str, Any]) -> bool:
        """Валідує дані таблиці"""
        try:
            required_fields = ["nazva_ukr_orig", "dzherelo_syrovyny", "aktyvni_spoluky", "dobova_norma", "dzherela_tsytaty"]
            for field in required_fields:
                if field not in data:
                    return False
            if not isinstance(data["aktyvni_spoluky"], list):
                return False
            if not isinstance(data["dzherela_tsytaty"], list):
                return False
            return True
        except:
            return False

    def _extract_real_quotes_from_response(self, raw_response: str, existing_count: int) -> List[str]:
        """Витягує реальні цитати з Gemini raw_response"""
        quotes = []

        if not raw_response:
            return quotes

        # Розділяємо текст на речення
        sentences = []
        for delimiter in ['. ', '! ', '? ', '; ']:
            parts = raw_response.split(delimiter)
            for part in parts:
                clean_part = part.strip()
                if len(clean_part) > 40 and len(clean_part) < 200:
                    # Фільтруємо якісні речення
                    if any(keyword in clean_part.lower() for keyword in
                          ['studies', 'research', 'shown', 'found', 'demonstrated', 'clinical', 'trial', 'effect', 'dose', 'dosage', 'mg', 'supplement']):
                        sentences.append(clean_part)

        # Беремо найкращі речення як цитати
        needed_quotes = 3 - existing_count
        for sentence in sentences[:needed_quotes]:
            if len(sentence) > 30:
                # Очищуємо речення від зайвих символів
                clean_sentence = sentence.strip('.,;:!?').strip()
                if clean_sentence and not clean_sentence.lower().startswith('source'):
                    quotes.append(clean_sentence)

        # Якщо не знайдено хороших речень, беремо загальні фрази
        if not quotes and needed_quotes > 0:
            general_parts = raw_response.split('\n')
            for part in general_parts:
                clean_part = part.strip()
                if 30 < len(clean_part) < 150 and not clean_part.lower().startswith(('search', 'source', 'find')):
                    quotes.append(clean_part)
                    if len(quotes) >= needed_quotes:
                        break

        return quotes[:needed_quotes]

    def _check_missing_critical_fields(self, result: Dict[str, Any]) -> List[str]:
        """Перевіряє які критичні поля відсутні"""
        missing = []

        if not result.get('dzherelo_syrovyny') or result.get('dzherelo_syrovyny') == '':
            missing.append('source_material')

        if not result.get('aktyvni_spoluky') or len(result.get('aktyvni_spoluky', [])) == 0:
            missing.append('active_compounds')

        if not result.get('dobova_norma') or result.get('dobova_norma') == '':
            missing.append('dosage')

        return missing

    def _targeted_gemini_search_with_sites(self, ingredient: str, synonyms: List[str], missing_fields: List[str]) -> Dict[str, Any]:
        """Цільовий Gemini пошук з site: операторами для L1-L4 джерел"""
        try:
            # Формуємо site: оператори для L1-L4 джерел
            l1_sites = [
                "site:pubmed.ncbi.nlm.nih.gov", "site:ncbi.nlm.nih.gov", "site:nih.gov",
                "site:efsa.europa.eu", "site:fda.gov",
                "site:scholar.google.com", "site:en.wikipedia.org"
            ]

            l2_sites = [
                "site:nature.com", "site:science.org", "site:sciencedirect.com"
            ]

            l3_sites = [
                "site:examine.com", "site:consumerlab.com"
            ]

            # Спочатку шукаємо на L1-L4 сайтах
            priority_sites = " OR ".join(l1_sites + l2_sites + l3_sites)
            search_terms = [ingredient] + (synonyms[:2] if synonyms else [])
            ingredient_query = " OR ".join([f'"{term}"' for term in search_terms])

            targeted_query = f'({priority_sites}) AND ({ingredient_query})'

            print(f"[TARGETED-SEARCH] Phase 1 - L1-L4 sites for: {ingredient}")
            print(f"[TARGETED-QUERY] {targeted_query[:100]}...")

            # Формуємо спеціалізований промпт
            missing_info = ""
            if 'source_material' in missing_fields:
                missing_info += "- Biological source/organism (what plant, animal, bacteria it comes from)\n"
            if 'active_compounds' in missing_fields:
                missing_info += "- Active compounds/chemicals with concentrations\n"
            if 'dosage' in missing_fields:
                missing_info += "- Daily dosage recommendations from clinical studies\n"

            targeted_prompt = f"""Search for scientific data about dietary supplement: {ingredient}

SEARCH QUERY: {targeted_query}

Find these missing data points:
{missing_info}

Focus on peer-reviewed sources, clinical studies, and official health agencies.
Return structured information with exact citations and URLs."""

            result = gemini_google_searcher.search_comprehensive_ingredient_data(
                ingredient, synonyms, custom_prompt=targeted_prompt
            )

            if result and result.get('search_method') != 'gemini_google_search_failed':
                print(f"[TARGETED-SUCCESS] Found data from L1-L4 targeted search")
                return result

            # PHASE 2: Якщо не знайшли на L1-L4, загальний пошук
            print(f"[TARGETED-FALLBACK] Phase 2 - General search for missing fields")

            general_prompt = f"""Search for scientific data about dietary supplement: {ingredient}

SEARCH TERMS: "{ingredient}" OR "{' OR '.join(search_terms[:3])}"

Find these missing data points:
{missing_info}

Include any reliable sources with scientific backing."""

            return gemini_google_searcher.search_comprehensive_ingredient_data(
                ingredient, synonyms, custom_prompt=general_prompt
            )

        except Exception as e:
            print(f"[ERROR] Targeted Gemini search failed: {e}")
            return {}

    def _create_empty_table_result(self, ingredient: str) -> Dict[str, Any]:
        """Створює порожній результат таблиці"""
        return {
            "nazva_ukr_orig": "",  # Порожнє - pipeline сам створить назву
            "dzherelo_syrovyny": "",
            "aktyvni_spoluky": [],
            "dobova_norma": "",
            "dzherela_tsytaty": []
        }

    def _convert_vertexai_to_real_url(self, vertexai_url: str, title: str, ingredient: str = "") -> str:
        """ДЕКОДУЄ РЕАЛЬНИЙ URL з VertexAI redirect через HTTP requests"""
        if 'vertexaisearch.cloud.google.com' not in vertexai_url:
            return vertexai_url

        try:
            print(f"[URL-HTTP] Following redirect for: {vertexai_url[:80]}...")

            import requests
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry

            # Налаштування сесії з timeout та retry
            session = requests.Session()
            retry_strategy = Retry(
                total=2,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            # Виконуємо HTTP HEAD запит щоб слідувати за redirects
            response = session.head(
                vertexai_url,
                allow_redirects=True,
                timeout=8,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )

            final_url = response.url

            # Перевіряємо чи це справді інший URL
            if final_url != vertexai_url and not final_url.startswith('https://vertexaisearch.cloud.google.com'):
                print(f"[URL-SUCCESS] Real URL found: {final_url}")
                return final_url
            else:
                print(f"[URL-REDIRECT-FAILED] No real redirect found")
                return self._get_real_url_from_title(title)

        except Exception as e:
            print(f"[URL-HTTP-ERROR] Request failed: {e}")
            return self._get_real_url_from_title(title)

    def _get_real_url_from_title(self, title: str) -> str:
        """Отримує реальний URL на основі title як ОСТАННІЙ fallback"""
        if not title:
            print(f"[URL-FALLBACK] No title provided, returning empty")
            return ""

        title_lower = title.lower()
        print(f"[URL-FALLBACK] Trying title-based mapping for: {title}")

        # Використовуємо тільки РЕАЛЬНІ відомі URL
        real_mappings = {
            'ahcc.net': 'https://ahcc.net',
            'sourcenaturals.com': 'https://www.sourcenaturals.com',
            'qualityoflife.net': 'https://qualityoflife.net',
            'verywellhealth.com': 'https://www.verywellhealth.com',
            'examine.com': 'https://examine.com',
            'wikipedia.org': 'https://en.wikipedia.org',
            'nih.gov': 'https://www.nih.gov',
            'pubmed': 'https://pubmed.ncbi.nlm.nih.gov'
        }

        for domain, base_url in real_mappings.items():
            if domain in title_lower:
                print(f"[URL-FALLBACK] Found mapping: {title} -> {base_url}")
                return base_url

        # Якщо нічого не знайдено - повертаємо порожнє замість фейкового
        print(f"[URL-FALLBACK] No mapping found for title: {title}")
        return ""

    def _check_direct_l1_sources(self, ingredient: str, synonyms: Optional[List[str]], ai_model: Optional[str]) -> Optional[Dict[str, Any]]:
        """Перевіряє прямі L1 джерела (NIH, EFSA, FDA)"""
        try:
            print(f"[L1-DIRECT] Checking direct L1 sources for {ingredient}...")

            l1_urls = [
                f"https://ods.od.nih.gov/search?q={ingredient}",
                f"https://efsa.europa.eu/search?q={ingredient}",
                f"https://fda.gov/search?q={ingredient}"
            ]

            # Для простоти реалізації, поки що повертаємо None
            # В майбутньому тут можна додати реальний пошук по L1 сайтах
            print(f"[L1-DIRECT] Direct L1 search not implemented yet")
            return None

        except Exception as e:
            print(f"[L1-DIRECT-ERROR] Error checking L1 sources: {e}")
            return None

    def _check_l2_sources(self, ingredient: str, synonyms: Optional[List[str]], ai_model: Optional[str]) -> Optional[Dict[str, Any]]:
        """Перевіряє L2 джерела (Nature, ScienceDirect)"""
        try:
            print(f"[L2-ACADEMIC] Checking L2 academic sources for {ingredient}...")

            l2_urls = [
                f"https://nature.com/search?q={ingredient}",
                f"https://sciencedirect.com/search?q={ingredient}"
            ]

            # Для простоти реалізації, поки що повертаємо None
            # В майбутньому тут можна додати реальний пошук по L2 сайтах
            print(f"[L2-ACADEMIC] L2 academic search not implemented yet")
            return None

        except Exception as e:
            print(f"[L2-ACADEMIC-ERROR] Error checking L2 sources: {e}")
            return None

    def _filter_google_results_by_l1_l4(self, google_result: Dict[str, Any], ingredient: str) -> Optional[Dict[str, Any]]:
        """Фільтрує Gemini Google Search результати за L1-L4 джерелами"""
        try:
            print(f"[GEMINI-L1L4-FILTER] Filtering Gemini results by L1-L4 sources...")

            if not google_result or not google_result.get('sources'):
                print(f"[GEMINI-L1L4-FILTER] No sources to filter")
                return None

            # Отримуємо список L1-L4 доменів з source_policy
            l1_l4_domains = []
            try:
                # L1 domains
                l1_l4_domains.extend([
                    'nih.gov', 'ncbi.nlm.nih.gov', 'pubmed.ncbi.nlm.nih.gov',
                    'efsa.europa.eu', 'fda.gov', 'ods.od.nih.gov',
                    'scholar.google.com', 'wikipedia.org'
                ])
                # L2 domains
                l1_l4_domains.extend([
                    'nature.com', 'science.org', 'sciencedirect.com',
                    'examine.com', 'consumerlab.com'
                ])
                # L3 domains можна додати пізніше

            except Exception as e:
                print(f"[GEMINI-L1L4-FILTER] Error getting L1-L4 domains: {e}")
                return None

            # Фільтруємо sources за L1-L4 доменами
            filtered_sources = []
            original_sources = google_result.get('sources', [])

            for source in original_sources:
                source_url = source.get('url', '')
                source_title = source.get('title', '')

                # Перевіряємо чи URL містить L1-L4 домени
                is_l1_l4 = False
                for domain in l1_l4_domains:
                    if domain in source_url.lower():
                        is_l1_l4 = True
                        print(f"[GEMINI-L1L4-FILTER] Accepted L1-L4 source: {domain} in {source_url}")
                        break

                if is_l1_l4:
                    filtered_sources.append(source)
                else:
                    print(f"[GEMINI-L1L4-FILTER] Rejected non-L1L4 source: {source_url}")

            if not filtered_sources:
                print(f"[GEMINI-L1L4-FILTER] No L1-L4 sources found in Gemini results")
                return None

            # Створюємо відфільтрований результат
            filtered_result = google_result.copy()
            filtered_result['sources'] = filtered_sources

            print(f"[GEMINI-L1L4-FILTER] Filtered {len(original_sources)} -> {len(filtered_sources)} L1-L4 sources")

            # Конвертуємо відфільтрований результат в таблицю
            return self._convert_google_result_to_table_ukrainian(filtered_result, ingredient)

        except Exception as e:
            print(f"[GEMINI-L1L4-FILTER-ERROR] Error filtering Gemini results: {e}")
            return None

    def _calculate_completion_stats(self, table_result: Dict[str, Any]) -> Dict[str, Any]:
        """Розраховує статистику заповненості таблиці"""
        try:
            total_fields = 5
            completed_fields = 0

            # Перевіряємо кожне поле
            if table_result.get('nazva_ukr_orig') and not 'не знайдена' in table_result['nazva_ukr_orig']:
                completed_fields += 1

            if table_result.get('dzherelo_syrovyny'):
                completed_fields += 1

            if table_result.get('aktyvni_spoluky') and len(table_result['aktyvni_spoluky']) > 0:
                completed_fields += 1

            if table_result.get('dobova_norma'):
                completed_fields += 1

            if table_result.get('dzherela_tsytaty') and len(table_result['dzherela_tsytaty']) > 0:
                completed_fields += 1

            percentage = (completed_fields / total_fields) * 100

            return {
                'total_fields': total_fields,
                'completed_fields': completed_fields,
                'percentage': percentage,
                'missing_fields': total_fields - completed_fields
            }

        except Exception as e:
            print(f"[COMPLETION-STATS-ERROR] Error calculating completion: {e}")
            return {'total_fields': 5, 'completed_fields': 0, 'percentage': 0.0, 'missing_fields': 5}


# Global instance
experimental_table_extractor = ExperimentalTableExtractor()