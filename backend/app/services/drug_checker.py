"""
backend/app/services/drug_checker.py — Drug Interaction & Medication Intelligence Service
"""
import logging
from typing import Optional
from app.services.ai_service import ai_service

logger = logging.getLogger("arogyaai.drug_checker")

# Common Indian medications for autocomplete
COMMON_MEDICATIONS = [
    "Paracetamol", "Aspirin", "Ibuprofen", "Metformin", "Atorvastatin",
    "Amlodipine", "Lisinopril", "Metoprolol", "Omeprazole", "Pantoprazole",
    "Cetirizine", "Levothyroxine", "Azithromycin", "Amoxicillin", "Ciprofloxacin",
    "Doxycycline", "Losartan", "Ramipril", "Glimepiride", "Insulin",
    "Warfarin", "Clopidogrel", "Atenolol", "Furosemide", "Spironolactone",
    "Hydroxychloroquine", "Prednisolone", "Dexamethasone", "Folic Acid",
    "Iron Sulfate", "Calcium Carbonate", "Vitamin D3", "B-Complex",
    "Ranitidine", "Domperidone", "Ondansetron", "Metronidazole",
    "Diclofenac", "Aceclofenac", "Naproxen", "Tramadol", "Alprazolam",
    "Clonazepam", "Escitalopram", "Sertraline", "Fluoxetine", "Amitriptyline",
    "Gabapentin", "Pregabalin", "Carbamazepine", "Phenytoin", "Valproate",
    "Montelukast", "Salbutamol", "Budesonide", "Fluticasone", "Theophylline",
    "Sildenafil", "Tadalafil", "Tamsulosin", "Finasteride",
    "Oral Contraceptives", "Progesterone", "Estradiol",
    "Allopurinol", "Colchicine", "Hydroxyzine", "Chlorpheniramine",
]


class DrugCheckerService:
    """Real-time drug interaction checker powered by clinical AI."""

    async def check_interactions(
        self,
        medications: list[str],
        user_profile: Optional[dict] = None,
    ) -> dict:
        """
        Check drug-drug and drug-food interactions for a list of medications.
        Returns structured interaction report.
        """
        if not ai_service.available:
            return {
                "error": "AI service not available",
                "analysis": "Drug interaction checking requires AI service configuration.",
                "meta": {},
            }

        if len(medications) < 2:
            return {
                "analysis": "Please provide at least 2 medications to check interactions.",
                "meta": {"total_interactions": 0, "critical": 0, "dangerous": 0, "caution": 0, "safe": 0},
            }

        try:
            result = await ai_service.check_drug_interactions(medications, user_profile)
            logger.info("[DrugChecker] Analyzed %d medications", len(medications))
            return result
        except Exception as e:
            logger.error("[DrugChecker] Error: %s", e)
            return {
                "error": str(e),
                "analysis": "Could not complete drug interaction analysis. Please consult your pharmacist.",
                "meta": {},
            }

    def get_medication_suggestions(self, query: str) -> list[str]:
        """Return autocomplete suggestions for medication names."""
        if not query or len(query) < 2:
            return []
        query_lower = query.lower()
        return [m for m in COMMON_MEDICATIONS if query_lower in m.lower()][:8]


drug_checker_service = DrugCheckerService()
