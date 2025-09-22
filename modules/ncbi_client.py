"""
NCBI E-utilities API Client для реальних PubMed пошуків
"""
import requests
import xml.etree.ElementTree as ET
import time
from typing import List, Dict, Any, Optional

class NCBIClient:
    """Клас для роботи з NCBI E-utilities API"""

    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.email = "research@dlsd.com"  # Рекомендується для NCBI API
        self.rate_limit = 0.34  # 3 запити в секунду максимум

    def search_pubmed(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Пошук статей в PubMed через NCBI API

        Args:
            query: Пошуковий запит
            max_results: Максимальна кількість результатів

        Returns:
            Список статей з метаданими
        """
        try:
            print(f"[NCBI] Searching PubMed for: {query[:50]}...")

            # 1. ESearch - пошук ID статей
            search_url = f"{self.base_url}/esearch.fcgi"
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "xml",
                "email": self.email,
                "sort": "relevance"
            }

            search_response = requests.get(search_url, params=search_params, timeout=10)
            search_response.raise_for_status()

            # Парсимо XML відповідь
            root = ET.fromstring(search_response.content)
            pmids = [id_elem.text for id_elem in root.findall(".//Id")]

            if not pmids:
                print(f"[NCBI] No results found for: {query}")
                return []

            print(f"[NCBI] Found {len(pmids)} PubMed IDs")

            # Rate limiting
            time.sleep(self.rate_limit)

            # 2. EFetch - отримання метаданих
            articles = self._fetch_article_details(pmids[:max_results])

            return articles

        except Exception as e:
            print(f"[ERROR] NCBI search failed: {e}")
            return []

    def _fetch_article_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Отримує детальні дані про статті"""
        try:
            if not pmids:
                return []

            # EFetch запит
            fetch_url = f"{self.base_url}/efetch.fcgi"
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "email": self.email
            }

            fetch_response = requests.get(fetch_url, params=fetch_params, timeout=15)
            fetch_response.raise_for_status()

            # Парсимо XML
            root = ET.fromstring(fetch_response.content)
            articles = []

            for article_elem in root.findall(".//PubmedArticle"):
                try:
                    article_data = self._parse_article_xml(article_elem)
                    if article_data:
                        articles.append(article_data)
                except Exception as e:
                    print(f"[WARNING] Failed to parse article: {e}")
                    continue

            print(f"[NCBI] Parsed {len(articles)} articles")
            return articles

        except Exception as e:
            print(f"[ERROR] Failed to fetch article details: {e}")
            return []

    def _parse_article_xml(self, article_elem) -> Optional[Dict[str, Any]]:
        """Парсить XML одної статті"""
        try:
            # PMID
            pmid_elem = article_elem.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""

            # Заголовок
            title_elem = article_elem.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else ""

            # Абстракт
            abstract_elems = article_elem.findall(".//AbstractText")
            abstract_parts = []
            for abs_elem in abstract_elems:
                if abs_elem.text:
                    abstract_parts.append(abs_elem.text)
            abstract = " ".join(abstract_parts)

            # DOI
            doi = ""
            for id_elem in article_elem.findall(".//ArticleId"):
                if id_elem.get("IdType") == "doi":
                    doi = id_elem.text
                    break

            # Дата публікації
            year = None
            year_elem = article_elem.find(".//PubDate/Year")
            if year_elem is not None and year_elem.text:
                try:
                    year = int(year_elem.text)
                except ValueError:
                    year = None

            # Журнал
            journal_elem = article_elem.find(".//Title")
            journal = journal_elem.text if journal_elem is not None else ""

            if not title and not abstract:
                return None

            return {
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "doi": doi,
                "year": year,
                "journal": journal,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "source_priority": 1,  # PubMed = L1
                "full_text": f"{title} {abstract}".strip()
            }

        except Exception as e:
            print(f"[ERROR] XML parsing error: {e}")
            return None

    def search_multiple_queries(self, queries: List[str], max_per_query: int = 5) -> List[Dict[str, Any]]:
        """
        Виконує пошук по кількох запитах

        Args:
            queries: Список пошукових запитів
            max_per_query: Максимум результатів на запит

        Returns:
            Об'єднаний список статей
        """
        all_articles = []
        seen_pmids = set()

        for i, query in enumerate(queries[:5], 1):  # Обмежуємо до 5 запитів
            print(f"[NCBI] Query {i}/{len(queries[:5])}: {query}")

            articles = self.search_pubmed(query, max_per_query)

            # Дедуплікація по PMID
            for article in articles:
                pmid = article.get("pmid", "")
                if pmid and pmid not in seen_pmids:
                    seen_pmids.add(pmid)
                    all_articles.append(article)

            # Rate limiting між запитами
            time.sleep(self.rate_limit * 2)

        print(f"[NCBI] Total unique articles: {len(all_articles)}")
        return all_articles

# Global instance
ncbi_client = NCBIClient()