"""
Stage 1: Searcher Process
Генерація пошукових запитів та збір кандидатів L1-L4 з використанням синонімів
"""
import json
import requests
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode, quote
import jsonschema
import random

from modules.multi_ai_client import multi_ai_client
from modules.ncbi_client import ncbi_client
from processes.source_policy import source_policy
from processes.schemas import SEARCHER_OUTPUT_SCHEMA
from config import Config

class ScientificSearcher:
    """Searcher agent for generating search queries and collecting L1-L4 candidates"""

    def __init__(self):
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        return """Generate search terms for scientific databases.

TASK: Create 8-14 search terms for PubMed, EFSA, FDA searches.

RULES:
- Use all provided names and synonyms
- Include scientific terms
- Focus on supplements and nutrition
- Return simple list format

OUTPUT: Return only the search terms, one per line."""

    def search_ingredient(self, normalized_data: Dict[str, Any], synonyms: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate search queries and collect candidates using ALL available names

        Args:
            normalized_data: Output from Normalizer
            synonyms: Additional synonyms to use in search

        Returns:
            Search results matching SEARCHER_OUTPUT_SCHEMA
        """
        try:
            ingredient = normalized_data["ingredient"]
            ingredient_class = normalized_data["class"]
            lat_name = normalized_data.get("taxon", {}).get("lat", "")

            print(f"[SEARCH] Searching for: {ingredient}")

            # Collect ALL available names
            all_names = [ingredient]
            if synonyms:
                all_names.extend(synonyms)
            if lat_name and lat_name != "Невідомо":
                all_names.append(lat_name)

            print(f"[INFO] Using names: {', '.join(all_names[:3])}...")

            # Generate search terms using all names
            search_terms = self._generate_search_terms(all_names, ingredient_class)

            # Collect candidates from multiple sources
            candidates = []

            # 1. Real PubMed search through NCBI API
            candidates.extend(self._search_real_pubmed(all_names, search_terms))

            # 2. L2 journal searches
            candidates.extend(self._generate_journal_candidates(all_names))

            # 3. L1 regulatory sources
            candidates.extend(self._generate_regulatory_candidates(all_names))

            # 4. L1 Wikipedia sources
            candidates.extend(self._generate_wikipedia_candidates(all_names))

            # Limit and deduplicate
            unique_candidates = self._deduplicate_candidates(candidates)
            final_candidates = unique_candidates[:20]

            result = {
                "search_terms": search_terms,
                "candidates": final_candidates
            }

            # Validate against schema
            jsonschema.validate(result, SEARCHER_OUTPUT_SCHEMA)

            print(f"[INFO] Generated {len(search_terms)} search terms, {len(final_candidates)} candidates")
            return result

        except Exception as e:
            print(f"[ERROR] Search failed for {ingredient}: {e}")
            return self._create_fallback_result(ingredient)

    def _generate_search_terms(self, all_names: List[str], ingredient_class: str) -> List[str]:
        """Generate search terms using OR format for all available names"""
        search_terms = []

        # Фільтруємо порожні назви
        valid_names = [name.strip() for name in all_names if name and name.strip()]

        if not valid_names:
            return []

        # Створюємо OR частину для всіх назв
        if len(valid_names) == 1:
            names_or_part = f'"{valid_names[0]}"'
        else:
            quoted_names = [f'"{name}"' for name in valid_names]
            names_or_part = f'({" OR ".join(quoted_names)})'

        # Base terms з OR форматом
        search_terms.extend([
            f'{names_or_part} AND supplement',
            f'{names_or_part} AND dosage',
            f'{names_or_part} AND effects',
            f'{names_or_part} AND "active compounds"'
        ])

        # Class-specific terms
        if ingredient_class == "vitamin":
            search_terms.extend([
                f'{names_or_part} AND RDA',
                f'{names_or_part} AND deficiency'
            ])
        elif ingredient_class == "plant":
            search_terms.extend([
                f'{names_or_part} AND extract',
                f'{names_or_part} AND phytochemistry'
            ])

        # Regulatory sources з OR форматом
        search_terms.extend([
            f'site:efsa.europa.eu {names_or_part}',
            f'site:fda.gov {names_or_part}',
            f'site:ods.od.nih.gov {names_or_part}'
        ])

        # Wikipedia sources (L1-L2 level)
        search_terms.extend([
            f'site:en.wikipedia.org {names_or_part}',
            f'site:uk.wikipedia.org {names_or_part}',
            f'site:ru.wikipedia.org {names_or_part}'
        ])

        # Додаємо додаткові терми якщо менше 8
        while len(search_terms) < 8:
            search_terms.extend([
                f'{names_or_part} AND safety',
                f'{names_or_part} AND research',
                f'{names_or_part} AND clinical',
                f'{names_or_part} AND benefits'
            ])

        # Limit to schema requirements (8-14)
        return search_terms[:14]

    def _search_real_pubmed(self, all_names: List[str], search_terms: List[str]) -> List[Dict[str, Any]]:
        """Search real PubMed articles through NCBI API"""
        candidates = []

        try:
            # Фільтруємо порожні назви
            valid_names = [name.strip() for name in all_names if name and name.strip()]

            if not valid_names:
                return candidates

            # Створюємо OR частину для PubMed запитів
            if len(valid_names) == 1:
                names_or_part = f'"{valid_names[0]}"'
            else:
                quoted_names = [f'"{name}"' for name in valid_names]
                names_or_part = f'({" OR ".join(quoted_names)})'

            # Створюємо специфічні запити для PubMed з OR форматом
            pubmed_queries = [
                f'{names_or_part}[Title/Abstract] AND (supplement OR nutrition OR dietary)',
                f'{names_or_part}[Title] AND dosage',
                f'{names_or_part} AND (active compound OR bioactive)',
                f'{names_or_part} AND (clinical OR study OR effect)',
                f'{names_or_part} AND (biological source OR derived from OR extracted from)'
            ]

            # Відфільтровуємо дублікати та обмежуємо
            pubmed_queries = list(set(pubmed_queries[:8]))  # Максимум 8 запитів

            print(f"[SEARCH] Running {len(pubmed_queries)} NCBI queries...")

            # Виконуємо пошук через NCBI API
            articles = ncbi_client.search_multiple_queries(pubmed_queries, max_per_query=3)

            # Конвертуємо в формат candidates
            for article in articles:
                candidates.append({
                    "title": article.get("title", "")[:100],  # Обрізаємо довгі заголовки
                    "url": article.get("url", ""),
                    "domain": "pubmed.ncbi.nlm.nih.gov",
                    "year": article.get("year"),
                    "doi": article.get("doi"),
                    "pmid": article.get("pmid"),
                    "why": f"NCBI search result",
                    "abstract": article.get("abstract", ""),
                    "full_text": article.get("full_text", "")
                })

            print(f"[SEARCH] Found {len(candidates)} real PubMed articles")
            return candidates

        except Exception as e:
            print(f"[ERROR] Real PubMed search failed: {e}")
            # Fallback до порожнього списку
            return []

    def _generate_journal_candidates(self, all_names: List[str]) -> List[Dict[str, Any]]:
        """Generate L2 journal search candidates"""
        candidates = []

        journals = [
            ("nature.com", "Nature"),
            ("science.org", "Science"),
            ("sciencedirect.com", "ScienceDirect")
        ]

        for name in all_names[:2]:
            for domain, journal in journals:
                candidates.append({
                    "title": f"{name} research - {journal}",
                    "url": f"https://{domain}/search?q={quote(name)}",
                    "domain": domain,
                    "year": None,
                    "doi": None,
                    "pmid": None,
                    "why": f"{journal} search for {name}"
                })

        return candidates

    def _generate_wikipedia_candidates(self, all_names: List[str]) -> List[Dict[str, Any]]:
        """Generate Wikipedia L1 source candidates"""
        candidates = []

        wikipedia_domains = [
            ("en.wikipedia.org", "Wikipedia EN"),
            ("uk.wikipedia.org", "Wikipedia UA"),
            ("ru.wikipedia.org", "Wikipedia RU")
        ]

        for name in all_names[:2]:  # First 2 names for Wikipedia
            for domain, source in wikipedia_domains:
                candidates.append({
                    "title": f"{name} - {source}",
                    "url": f"https://{domain}/wiki/{quote(name.replace(' ', '_'))}",
                    "domain": domain,
                    "year": None,
                    "doi": None,
                    "pmid": None,
                    "why": f"{source} article for {name}"
                })

        return candidates

    def _generate_regulatory_candidates(self, all_names: List[str]) -> List[Dict[str, Any]]:
        """Generate L1 regulatory source candidates"""
        candidates = []

        regulatory = [
            ("efsa.europa.eu", "EFSA"),
            ("fda.gov", "FDA"),
            ("ods.od.nih.gov", "NIH ODS")
        ]

        for name in all_names[:1]:  # Only main name for regulatory
            for domain, org in regulatory:
                candidates.append({
                    "title": f"{name} - {org} information",
                    "url": f"https://{domain}/search?q={quote(name)}",
                    "domain": domain,
                    "year": None,
                    "doi": None,
                    "pmid": None,
                    "why": f"{org} regulatory information for {name}"
                })

        return candidates

    def _deduplicate_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate candidates"""
        seen_urls = set()
        unique_candidates = []

        for candidate in candidates:
            url = candidate["url"]
            if url not in seen_urls:
                seen_urls.add(url)
                unique_candidates.append(candidate)

        return unique_candidates

    def _create_fallback_result(self, ingredient: str) -> Dict[str, Any]:
        """Create fallback result when search fails"""
        return {
            "search_terms": [
                f'"{ingredient}" supplement',
                f'site:pubmed.ncbi.nlm.nih.gov "{ingredient}"',
                f'site:efsa.europa.eu "{ingredient}"'
            ],
            "candidates": []
        }

# Global instance
searcher = ScientificSearcher()