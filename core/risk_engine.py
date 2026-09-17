from dataclasses import dataclass
from typing import Optional, Dict


RISK_LEVELS = (
    "LOW",
    "MODERATE",
    "HIGH",
    "VERY HIGH",
    "INSUFFICIENT DATA",
)


@dataclass
class RiskInput:
    rainfall_intensity: Optional[str] = None
    rainfall_duration_hours: Optional[float] = None
    drainage: Optional[str] = None
    terrain: Optional[str] = None
    previous_flooding: Optional[str] = None
    water_accumulation: Optional[str] = None


@dataclass
class RiskResult:
    level: str
    score: Optional[int]
    factors: Dict[str, int]
    explanation: str
    uncertainty: str


def assess_risk(data: RiskInput) -> RiskResult:
    """
    Deterministic community flood-risk assessment.

    This is a relative risk-assessment prototype.
    It is NOT an official flood-warning or hydrological prediction system.
    """

    required = [
        data.rainfall_intensity,
        data.rainfall_duration_hours,
        data.drainage,
        data.terrain,
        data.previous_flooding,
        data.water_accumulation,
    ]

    if any(value is None or value == "" for value in required):
        return RiskResult(
            level="INSUFFICIENT DATA",
            score=None,
            factors={},
            explanation=(
                "There is not enough information to provide a reliable "
                "relative flood-risk assessment."
            ),
            uncertainty=(
                "Additional rainfall, duration, drainage, terrain, "
                "previous-flooding, and water-accumulation information is needed."
            ),
        )

    factors: Dict[str, int] = {}

    # Rainfall intensity
    intensity = str(data.rainfall_intensity).lower()

    if intensity in {"very heavy", "extreme"}:
        factors["rainfall_intensity"] = 3
    elif intensity == "heavy":
        factors["rainfall_intensity"] = 2
    elif intensity == "moderate":
        factors["rainfall_intensity"] = 1
    else:
        factors["rainfall_intensity"] = 0

    # Rainfall duration
    duration = float(data.rainfall_duration_hours)

    if duration >= 8:
        factors["rainfall_duration"] = 3
    elif duration >= 4:
        factors["rainfall_duration"] = 2
    elif duration >= 2:
        factors["rainfall_duration"] = 1
    else:
        factors["rainfall_duration"] = 0

    # Drainage
    drainage = str(data.drainage).lower()

    if drainage in {"very poor", "poor"}:
        factors["drainage"] = 2
    elif drainage == "moderate":
        factors["drainage"] = 1
    else:
        factors["drainage"] = 0

    # Terrain
    terrain = str(data.terrain).lower()

    if terrain in {"low-lying", "very low", "low"}:
        factors["terrain"] = 2
    elif terrain == "moderate":
        factors["terrain"] = 1
    else:
        factors["terrain"] = 0

    # Previous flooding
    previous = str(data.previous_flooding).lower()

    if previous in {"frequent", "yes", "severe"}:
        factors["previous_flooding"] = 2
    elif previous in {"occasional", "sometimes"}:
        factors["previous_flooding"] = 1
    else:
        factors["previous_flooding"] = 0

    # Existing water accumulation
    accumulation = str(data.water_accumulation).lower()

    if accumulation in {"significant", "severe", "high"}:
        factors["water_accumulation"] = 3
    elif accumulation in {"moderate", "some"}:
        factors["water_accumulation"] = 1
    else:
        factors["water_accumulation"] = 0

    score = sum(factors.values())

    # Deterministic classification.
    if score >= 12:
        level = "VERY HIGH"
    elif score >= 8:
        level = "HIGH"
    elif score >= 4:
        level = "MODERATE"
    else:
        level = "LOW"

    important_factors = [
        name.replace("_", " ")
        for name, value in factors.items()
        if value >= 2
    ]

    if important_factors:
        explanation = (
            f"The relative risk is classified as {level}. "
            f"Important contributing factors include "
            f"{', '.join(important_factors)}."
        )
    else:
        explanation = (
            f"The relative risk is classified as {level} based on "
            "the supplied environmental and community-level factors."
        )

    uncertainty = (
        "This is a relative AI-assisted assessment based on user-reported "
        "inputs. It does not replace official warnings, forecasts, or "
        "instructions from authorized disaster-management agencies."
    )

    return RiskResult(
        level=level,
        score=score,
        factors=factors,
        explanation=explanation,
        uncertainty=uncertainty,
    )