"""
tests/test_health_engine.py — Health engine unit tests
"""
from app.services.health_engine import (
    HealthScoreEngine,
    DoctorUpsellEngine,
    detect_emergency,
    QueryUsageTracker,
)


# ── Emergency Detection ──────────────────────────────────────────
class TestEmergencyDetection:
    def test_english_chest_pain(self):
        assert detect_emergency("I have chest pain") is True

    def test_english_heart_attack(self):
        assert detect_emergency("I think I'm having a heart attack") is True

    def test_english_breathing(self):
        assert detect_emergency("I can't breathe") is True

    def test_hindi_emergency(self):
        assert detect_emergency("सीने में दर्द हो रहा है") is True

    def test_gujarati_emergency(self):
        assert detect_emergency("છાતીમાં દુખાવો") is True

    def test_normal_cold(self):
        assert detect_emergency("I have a cold and mild headache") is False

    def test_normal_fever(self):
        assert detect_emergency("I have fever for 2 days") is False

    def test_empty_message(self):
        assert detect_emergency("") is False

    def test_case_insensitive(self):
        assert detect_emergency("CHEST PAIN") is True


# ── Health Score Engine ──────────────────────────────────────────
class TestHealthScoreEngine:
    def test_emergency_always_15(self):
        score = HealthScoreEngine.compute("serious", True, emergency=True)
        assert score == 15

    def test_serious_low_score(self):
        score = HealthScoreEngine.compute("serious", True, emergency=False)
        assert score <= 65

    def test_mild_high_score(self):
        score = HealthScoreEngine.compute("mild", False, emergency=False)
        assert score >= 85

    def test_moderate_medium_score(self):
        score = HealthScoreEngine.compute("moderate", False, emergency=False)
        assert 50 <= score <= 90

    def test_deterministic(self):
        """Score must NOT use randomness — same inputs always same output."""
        score1 = HealthScoreEngine.compute("mild", False, False)
        score2 = HealthScoreEngine.compute("mild", False, False)
        assert score1 == score2, "Health scores must be deterministic!"
        score3 = HealthScoreEngine.compute("serious", True, False)
        score4 = HealthScoreEngine.compute("serious", True, False)
        assert score3 == score4

    def test_score_always_in_range(self):
        for severity in ["mild", "moderate", "serious"]:
            for needs_doc in [True, False]:
                score = HealthScoreEngine.compute(severity, needs_doc, False)
                assert 0 <= score <= 100, f"Score out of range: {score}"

    def test_status_label_excellent(self):
        assert HealthScoreEngine.get_status_label(90) == "Excellent"

    def test_status_label_poor(self):
        assert HealthScoreEngine.get_status_label(30) == "Poor"

    def test_status_color_green(self):
        assert HealthScoreEngine.get_status_color(90) == "#22c55e"


# ── Doctor Upsell Engine ──────────────────────────────────────────
class TestDoctorUpsellEngine:
    def test_mild_returns_none(self):
        result = DoctorUpsellEngine.generate("mild", "general", needs_doctor=False)
        assert result is None

    def test_serious_returns_upsell(self):
        result = DoctorUpsellEngine.generate("serious", "heart", needs_doctor=True)
        assert result is not None
        assert result["show"] is True
        assert result["specialty"] == "Cardiologist"
        assert result["price_inr"] > 0

    def test_moderate_returns_upsell(self):
        result = DoctorUpsellEngine.generate("moderate", "skin", needs_doctor=False)
        assert result is not None
        assert result["specialty"] == "Dermatologist"

    def test_needs_doctor_triggers_upsell(self):
        result = DoctorUpsellEngine.generate("mild", "general", needs_doctor=True)
        assert result is not None

    def test_unknown_body_system_defaults_to_gp(self):
        result = DoctorUpsellEngine.generate("serious", "unknown_body_part", needs_doctor=True)
        assert result is not None
        assert result["specialty"] == "General Physician"


# ── Query Usage Tracker ───────────────────────────────────────────
class TestQueryUsageTracker:
    def test_localhost_unlimited(self):
        tracker = QueryUsageTracker(free_limit=3)
        assert tracker.get_remaining("127.0.0.1", is_premium=False) == 999

    def test_premium_unlimited(self):
        tracker = QueryUsageTracker(free_limit=3)
        assert tracker.get_remaining("1.2.3.4", is_premium=True) == 999

    def test_free_user_gets_limited(self):
        tracker = QueryUsageTracker(free_limit=3)
        assert tracker.get_remaining("5.5.5.5") == 3

    def test_consume_decrements(self):
        tracker = QueryUsageTracker(free_limit=3)
        tracker.consume("6.6.6.6")
        assert tracker.get_remaining("6.6.6.6") == 2

    def test_consume_blocks_at_limit(self):
        tracker = QueryUsageTracker(free_limit=2)
        tracker.consume("7.7.7.7")
        tracker.consume("7.7.7.7")
        result = tracker.consume("7.7.7.7")
        assert result is False

    def test_reset_clears_all(self):
        tracker = QueryUsageTracker(free_limit=3)
        tracker.consume("8.8.8.8")
        tracker.reset()
        assert tracker.get_remaining("8.8.8.8") == 3
