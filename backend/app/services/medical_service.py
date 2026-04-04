"""
app/services/medical_service.py — External medical data (Wikipedia, FDA)
"""
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("arogyaai.medical")


class MedicalService:
    """Wikipedia + FDA drug data for AI context enrichment."""

    async def get_wikipedia_summary(self, query: str) -> Optional[str]:
        """Fetch a brief Wikipedia medical summary to ground AI responses."""
        try:
            # Sanitize query
            safe_query = query.replace(" ", "_").replace("/", "")[:80]
            url = f"{settings.WIKI_API}/{safe_query}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(
                    url,
                    headers={"User-Agent": "ArogyaAI/2.2 (health app; India)"}
                )
                if r.status_code == 200:
                    data = r.json()
                    summary = data.get("extract", "")
                    # Only return if it looks like medical content
                    if summary and len(summary) > 50:
                        return summary[:600]
        except Exception as e:
            logger.debug("[Medical] Wikipedia fetch failed: %s", e)
        return None

    async def search_drug_fda(self, drug_name: str) -> Optional[dict]:
        """Search FDA drug database for basic drug info."""
        try:
            url = f"{settings.OPENFDA_BASE}/label.json"
            params = {"search": f"openfda.brand_name:{drug_name}", "limit": 1}
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    results = data.get("results", [])
                    if results:
                        item = results[0]
                        return {
                            "brand_name": item.get("openfda", {}).get("brand_name", [drug_name])[0],
                            "generic_name": item.get("openfda", {}).get("generic_name", []),
                            "purpose": item.get("purpose", [""])[0][:300] if item.get("purpose") else None,
                            "warnings": item.get("warnings", [""])[0][:300] if item.get("warnings") else None,
                            "dosage": item.get("dosage_and_administration", [""])[0][:300] if item.get("dosage_and_administration") else None,
                        }
        except Exception as e:
            logger.debug("[Medical] FDA search failed: %s", e)
        return None

    async def get_adverse_events(self, drug_name: str) -> Optional[dict]:
        """Get top adverse events reported for a drug from FDA."""
        try:
            url = f"{settings.OPENFDA_BASE}/event.json"
            params = {
                "search": f"patient.drug.medicinalproduct:{drug_name}",
                "count": "patient.reaction.reactionmeddrapt.exact",
                "limit": 5,
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(url, params=params)
                if r.status_code == 200:
                    data = r.json()
                    results = data.get("results", [])
                    return {
                        "top_reactions": [item["term"] for item in results[:5]],
                        "source": "FDA Adverse Event Reporting System (FAERS)",
                    }
        except Exception as e:
            logger.debug("[Medical] FDA adverse events failed: %s", e)
        return None


# Singleton
medical_service = MedicalService()
