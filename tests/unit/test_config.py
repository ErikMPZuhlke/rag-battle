"""Env-driven configuration defaults and env-var overrides."""
from app.core.config import Settings, settings


def test_default_budget_values_match_documented_limits():
    assert settings.max_llm_calls == 3
    assert settings.max_retrievals == 10
    assert settings.max_input_tokens == 4000


def test_no_answer_text_matches_participant_rules_wording():
    assert settings.no_answer_text == "The documentation does not specify this."


def test_settings_falls_back_to_default_when_env_unset(monkeypatch):
    monkeypatch.delenv("TOP_K", raising=False)
    assert Settings().top_k == 5


def test_settings_reads_override_from_environment(monkeypatch):
    monkeypatch.setenv("TOP_K", "99")
    assert Settings().top_k == 99
