from __future__ import annotations

from api.services.plans import PlanLimits, remaining_jobs, resolve_plan


def test_free_plan_defaults():
    plan = resolve_plan("free")
    assert plan.key == "free"
    assert plan.label == "Trial"
    assert plan.jobs_per_month is not None
    assert plan.max_corridors is not None


def test_pilot_and_enterprise():
    assert resolve_plan("pilot").key == "pilot"
    assert resolve_plan("enterprise").jobs_per_month is None
    assert resolve_plan("unlimited").key == "enterprise"


def test_unknown_plan_is_trial():
    assert resolve_plan("gold").key == "free"
    assert resolve_plan(None).key == "free"


def test_remaining_jobs_none_when_unlimited():
    plan = PlanLimits("enterprise", "Enterprise", None, None, 50)
    assert remaining_jobs(999, plan) is None


def test_remaining_jobs_floors_at_zero():
    plan = PlanLimits("free", "Trial", 25, 15, 5)
    assert remaining_jobs(25, plan) == 0
    assert remaining_jobs(40, plan) == 0
    assert remaining_jobs(10, plan) == 15


def test_founder_email_matches_configured(monkeypatch):
    from api.config import settings
    from api.deps import is_founder_email

    monkeypatch.setattr(settings, "founding_admin_email", "you@terraiq.dev")
    monkeypatch.setattr(settings, "demo_request_email", None)
    assert is_founder_email("you@terraiq.dev")
    assert not is_founder_email("other@example.com")


class _Fleet:
    billing_plan = "free"


def test_debug_account_has_no_job_limit(monkeypatch):
    from api.config import settings
    from api.services.plans import plan_for_account

    monkeypatch.setattr(settings, "debug", True)
    plan = plan_for_account(_Fleet())
    assert plan.jobs_per_month is None
    assert plan.max_corridors is None
    assert plan.label == "Dev"


def test_quota_applies_when_not_debug(monkeypatch):
    from api.config import settings
    from api.services.plans import plan_for_account

    monkeypatch.setattr(settings, "debug", False)
    plan = plan_for_account(_Fleet())
    assert plan.jobs_per_month == settings.free_jobs_per_month


def test_founder_unlimited_without_debug(monkeypatch):
    from api.config import settings
    from api.services.plans import plan_for_account

    monkeypatch.setattr(settings, "debug", False)
    monkeypatch.setattr(settings, "founding_admin_email", "dev@local")
    monkeypatch.setattr(settings, "demo_request_email", None)
    plan = plan_for_account(_Fleet(), actor_email="dev@local")
    assert plan.jobs_per_month is None
    assert plan.label == "Founder"
