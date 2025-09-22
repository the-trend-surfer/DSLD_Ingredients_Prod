"""
Stage 2: Judge Process
Рангування та фільтрація джерел за L1-L4 політикою
"""
import json
import jsonschema
from typing import Dict, List, Any
from urllib.parse import urlparse

from modules.multi_ai_client import multi_ai_client
from processes.source_policy import source_policy
from processes.schemas import JUDGE_OUTPUT_SCHEMA

class SourceJudge:
    """Judge agent for ranking and filtering sources by L1-L4 policy"""

    def __init__(self):
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        return """Ти — Judge. Оціни кандидатів за доменом і метаданими. Присвой source_priority: 1..4. Seed — лише для нормалізації, не як evidence. Deny — відхилити. Поверни JSON з масивами accepted[] і rejected[]."""

    def judge_candidates(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Judge and rank candidates by L1-L4 policy

        Args:
            candidates: List of candidate sources from Searcher

        Returns:
            Judged results matching JUDGE_OUTPUT_SCHEMA
        """
        try:
            print(f"[JUDGE] Judging {len(candidates)} candidates...")

            accepted = []
            rejected = []

            # Process each candidate
            for candidate in candidates:
                url = candidate.get("url", "")
                title = candidate.get("title", "")

                if not url:
                    rejected.append({
                        "url": url or "missing",
                        "reason": "missing URL"
                    })
                    continue

                # Classify URL using source policy
                classification = source_policy.classify_url(url)
                decision = classification["decision"]
                priority = classification["source_priority"]
                reason = classification["reason"]

                if decision == "accept" and priority:
                    # Add to accepted with metadata
                    accepted_item = {
                        "title": title,
                        "url": url,
                        "source_priority": priority,
                        "doi": classification.get("doi"),
                        "pmid": classification.get("pmid")
                    }
                    accepted.append(accepted_item)
                    print(f"[OK] L{priority}: {self._truncate_url(url)}")

                elif decision == "seed":
                    # Legacy seed handling (should not happen since Wikipedia is now L1)
                    rejected.append({
                        "url": url,
                        "reason": f"legacy seed classification: {reason}"
                    })
                    print(f"[WARNING] Legacy SEED: {self._truncate_url(url)}")

                else:
                    # Add to rejected with reason
                    rejected.append({
                        "url": url,
                        "reason": reason
                    })
                    print(f"[REJECTED] Rejected: {self._truncate_url(url)} - {reason}")

            # Sort accepted by priority (L1 first)
            accepted.sort(key=lambda x: x["source_priority"])

            # Remove duplicates (same DOI/PMID)
            accepted = self._deduplicate_by_doi_pmid(accepted)

            result = {
                "accepted": accepted,
                "rejected": rejected
            }

            # Validate against schema
            jsonschema.validate(result, JUDGE_OUTPUT_SCHEMA)

            print(f"[SUMMARY] Judge results: {len(accepted)} accepted, {len(rejected)} rejected")
            self._print_summary(accepted)

            return result

        except Exception as e:
            print(f"[ERROR] Judge failed: {e}")
            return self._create_fallback_result()

    def _deduplicate_by_doi_pmid(self, accepted: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates based on DOI/PMID"""
        seen_identifiers = set()
        unique_accepted = []

        for item in accepted:
            # Create identifier based on DOI or PMID
            doi = item.get("doi")
            pmid = item.get("pmid")

            identifier = None
            if doi:
                identifier = f"doi:{doi}"
            elif pmid:
                identifier = f"pmid:{pmid}"
            else:
                # Use URL as fallback identifier
                identifier = f"url:{item['url']}"

            if identifier not in seen_identifiers:
                seen_identifiers.add(identifier)
                unique_accepted.append(item)
            else:
                print(f"🔄 Skipping duplicate: {identifier}")

        return unique_accepted

    def _truncate_url(self, url: str, max_length: int = 50) -> str:
        """Truncate URL for display"""
        if len(url) <= max_length:
            return url
        return url[:max_length] + "..."

    def _print_summary(self, accepted: List[Dict[str, Any]]) -> None:
        """Print summary of accepted sources by priority"""
        if not accepted:
            print("[WARNING] No L1-L4 sources found")
            return

        by_priority = {}
        for item in accepted:
            priority = item["source_priority"]
            if priority not in by_priority:
                by_priority[priority] = 0
            by_priority[priority] += 1

        print("[SUMMARY] Accepted sources by priority:")
        for priority in sorted(by_priority.keys()):
            count = by_priority[priority]
            print(f"  L{priority}: {count} sources")

    def judge_with_ai_assistance(self, candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Alternative method using AI to assist with judging
        (for complex cases where automated rules aren't sufficient)
        """
        try:
            # Prepare context for AI
            context = f"INPUT_CANDIDATES: {json.dumps(candidates, indent=2)}\n\n"
            context += """RULES:
- accept: тільки L1/L2/L3, L4 — якщо нема інших. seed → НЕ у accepted. deny → у rejected.
- deduplicate за DOI/PMID (або нормалізований заголовок).
- додай "reason" у rejected.

L1: pubmed.ncbi.nlm.nih.gov, efsa.europa.eu, fda.gov, ods.od.nih.gov, wikipedia.org
L2: nature.com, science.org, wiley.com, sciencedirect.com, springer.com
L3: cochranelibrary.com, bmj.com, frontiersin.org
L4: researchgate.net, wikidata.org, university domains
DENY: blog.*, medium.com, substack.com

OUTPUT:
{
  "accepted": [{"title":"...","url":"...","source_priority":1,"doi":null,"pmid":"..."}],
  "rejected": [{"url":"...","reason":"deny: blog domain"}]
}"""

            # Get AI response
            response = multi_ai_client.fetch_evidence_with_best_model(
                "judge_candidates", None, None
            )

            # Extract JSON from response
            result = self._extract_json_from_response(response)

            # Validate and return
            jsonschema.validate(result, JUDGE_OUTPUT_SCHEMA)
            return result

        except Exception as e:
            print(f"[ERROR] AI-assisted judging failed: {e}")
            return self.judge_candidates(candidates)  # Fallback to rule-based

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from AI response"""
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1

            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")

        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse JSON from response: {e}")

    def _create_fallback_result(self) -> Dict[str, Any]:
        """Create fallback result when judging fails"""
        return {
            "accepted": [],
            "rejected": []
        }

    def get_priority_stats(self, accepted: List[Dict[str, Any]]) -> Dict[int, int]:
        """Get statistics about source priorities"""
        stats = {1: 0, 2: 0, 3: 0, 4: 0}

        for item in accepted:
            priority = item.get("source_priority", 4)
            if priority in stats:
                stats[priority] += 1

        return stats

    def has_high_quality_sources(self, accepted: List[Dict[str, Any]]) -> bool:
        """Check if we have L1 or L2 sources"""
        return any(item.get("source_priority", 4) <= 2 for item in accepted)

# Global instance
judge = SourceJudge()