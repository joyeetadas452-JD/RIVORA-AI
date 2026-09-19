import pytest

from core.risk_engine import RiskInput, assess_risk


def test_low_risk():
    result = assess_risk(
        RiskInput(
            rainfall_intensity="light",
            rainfall_duration_hours=1,
            drainage="good",
            terrain="elevated",
            previous_flooding="no",
            water_accumulation="none",
        )
    )

    assert result.level == "LOW"
    assert result.explanation
    assert result.uncertainty


def test_moderate_risk():
    result = assess_risk(
        RiskInput(
            rainfall_intensity="heavy",
            rainfall_duration_hours=4,
            drainage="good",
            terrain="low",
            previous_flooding="no",
            water_accumulation="none",
        )
    )

    assert result.level == "MODERATE"
    assert result.explanation
    assert result.uncertainty


def test_high_risk():
    result = assess_risk(
        RiskInput(
            rainfall_intensity="heavy",
            rainfall_duration_hours=4,
            drainage="poor",
            terrain="low",
            previous_flooding="frequent",
            water_accumulation="moderate",
        )
    )

    assert result.level == "HIGH"
    assert result.explanation
    assert result.uncertainty


def test_very_high_risk():
    result = assess_risk(
        RiskInput(
            rainfall_intensity="very heavy",
            rainfall_duration_hours=8,
            drainage="poor",
            terrain="low",
            previous_flooding="frequent",
            water_accumulation="significant",
        )
    )

    assert result.level == "VERY HIGH"
    assert result.explanation
    assert result.uncertainty


def test_insufficient_data():
    result = assess_risk(
        RiskInput(
            rainfall_intensity=None,
            rainfall_duration_hours=None,
            drainage=None,
            terrain=None,
            previous_flooding=None,
            water_accumulation=None,
        )
    )

    assert result.level == "INSUFFICIENT DATA"
    assert result.uncertainty
