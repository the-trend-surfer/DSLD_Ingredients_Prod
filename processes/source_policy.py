"""
Source Policy - L1-L4 domain classification and URL evaluation
"""
from typing import Dict, Any
from urllib.parse import urlparse

class SourcePolicy:
    """L1-L4 source classification policy"""

    def __init__(self):
        # L1: Найвища якість - офіційні регулятори та PubMed
        self.l1_domains = [
            'pubmed.ncbi.nlm.nih.gov',
            'ncbi.nlm.nih.gov',
            'nih.gov',
            'efsa.europa.eu',
            'fda.gov',
            'ods.od.nih.gov',
            'en.wikipedia.org',
            'uk.wikipedia.org',
            'ru.wikipedia.org'
        ]

        # L2: Високоякісні наукові журнали
        self.l2_domains = [
            'nature.com',
            'science.org',
            'sciencedirect.com',
            'springer.com',
            'wiley.com'
        ]

        # L3: Рецензовані журнали та спеціалізовані ресурси
        self.l3_domains = [
            'cochranelibrary.com',
            'bmj.com',
            'frontiersin.org',
            'examine.com'
        ]

        # L4: Університети та інші ресурси
        self.l4_domains = [
            'researchgate.net',
            'wikidata.org',
            'consumerlab.com'
        ]

        # DENY: Заборонені домени
        self.deny_domains = [
            'blog.',
            'medium.com',
            'substack.com',
            'wordpress.com',
            'blogspot.com'
        ]

    def get_source_priority(self, url: str) -> int:
        """
        Повертає пріоритет джерела (1-4) для URL

        Returns:
            1: L1 (найвища якість)
            2: L2 (високоякісні наукові)
            3: L3 (спеціалізовані ресурси)
            4: L4 (університети та інші)
            5: DENY (заборонено)
        """
        try:
            if not url:
                return 5

            # Parse domain
            parsed = urlparse(url.lower())
            domain = parsed.netloc.lower()

            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            # Check L1 domains (highest priority)
            for l1_domain in self.l1_domains:
                if l1_domain in domain:
                    return 1

            # Check L2 domains
            for l2_domain in self.l2_domains:
                if l2_domain in domain:
                    return 2

            # Check L3 domains
            for l3_domain in self.l3_domains:
                if l3_domain in domain:
                    return 3

            # Check L4 domains
            for l4_domain in self.l4_domains:
                if l4_domain in domain:
                    return 4

            # Check denied domains
            for deny_domain in self.deny_domains:
                if deny_domain in domain:
                    return 5

            # Default to L4 for unknown domains
            return 4

        except Exception as e:
            return 5

    def classify_url(self, url: str) -> Dict[str, Any]:
        """
        Класифікує URL за L1-L4 політикою

        Returns:
            {
                "decision": "accept" | "deny" | "seed",
                "source_priority": 1-4 | None,
                "reason": "explanation",
                "doi": extracted DOI or None,
                "pmid": extracted PMID or None
            }
        """
        try:
            if not url:
                return {
                    "decision": "deny",
                    "source_priority": None,
                    "reason": "empty URL"
                }

            # Parse domain
            parsed = urlparse(url.lower())
            domain = parsed.netloc

            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]

            # Check for DENY domains first
            for deny_pattern in self.deny_domains:
                if deny_pattern in domain:
                    return {
                        "decision": "deny",
                        "source_priority": None,
                        "reason": f"denied domain: {deny_pattern}"
                    }

            # Extract DOI and PMID
            doi = self._extract_doi(url)
            pmid = self._extract_pmid(url)

            # Check L1 domains
            for l1_domain in self.l1_domains:
                if domain.endswith(l1_domain) or l1_domain in domain:
                    return {
                        "decision": "accept",
                        "source_priority": 1,
                        "reason": f"L1 domain: {l1_domain}",
                        "doi": doi,
                        "pmid": pmid
                    }

            # Check L2 domains
            for l2_domain in self.l2_domains:
                if domain.endswith(l2_domain) or l2_domain in domain:
                    return {
                        "decision": "accept",
                        "source_priority": 2,
                        "reason": f"L2 domain: {l2_domain}",
                        "doi": doi,
                        "pmid": pmid
                    }

            # Check L3 domains
            for l3_domain in self.l3_domains:
                if domain.endswith(l3_domain) or l3_domain in domain:
                    return {
                        "decision": "accept",
                        "source_priority": 3,
                        "reason": f"L3 domain: {l3_domain}",
                        "doi": doi,
                        "pmid": pmid
                    }

            # Check L4 domains
            for l4_domain in self.l4_domains:
                if domain.endswith(l4_domain) or l4_domain in domain:
                    return {
                        "decision": "accept",
                        "source_priority": 4,
                        "reason": f"L4 domain: {l4_domain}",
                        "doi": doi,
                        "pmid": pmid
                    }

            # Check for university domains (.edu, .ac.uk, etc.)
            if domain.endswith('.edu') or '.ac.' in domain or domain.endswith('.edu.ua'):
                return {
                    "decision": "accept",
                    "source_priority": 4,
                    "reason": "university domain",
                    "doi": doi,
                    "pmid": pmid
                }

            # If has DOI or PMID, probably academic
            if doi or pmid:
                return {
                    "decision": "accept",
                    "source_priority": 3,
                    "reason": f"academic identifier: {'DOI' if doi else 'PMID'}",
                    "doi": doi,
                    "pmid": pmid
                }

            # Unknown domain - deny by default
            return {
                "decision": "deny",
                "source_priority": None,
                "reason": f"unknown domain: {domain}"
            }

        except Exception as e:
            return {
                "decision": "deny",
                "source_priority": None,
                "reason": f"URL parsing error: {e}"
            }

    def _extract_doi(self, url: str) -> str:
        """Extract DOI from URL"""
        try:
            if 'doi.org/' in url:
                # Extract from doi.org URLs
                parts = url.split('doi.org/')
                if len(parts) > 1:
                    return parts[1].split('?')[0].split('#')[0]

            if '/doi/' in url:
                # Extract from /doi/ paths
                parts = url.split('/doi/')
                if len(parts) > 1:
                    return parts[1].split('?')[0].split('#')[0]

            return None
        except:
            return None

    def _extract_pmid(self, url: str) -> str:
        """Extract PMID from URL"""
        try:
            if 'pubmed.ncbi.nlm.nih.gov' in url:
                # Extract PMID from PubMed URLs
                if '/pmid=' in url:
                    pmid = url.split('/pmid=')[1].split('&')[0].split('#')[0]
                elif '/pubmed/' in url:
                    pmid = url.split('/pubmed/')[1].split('?')[0].split('#')[0].split('/')[0]
                else:
                    return None

                # Validate PMID is numeric
                if pmid.isdigit():
                    return pmid

            return None
        except:
            return None

# Global instance
source_policy = SourcePolicy()