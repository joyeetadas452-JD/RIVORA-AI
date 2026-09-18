"""Transparent prototype assessments for environmental risk domains.

These assessments are structured relative reviews, not validated forecasts.
Flood & Waterlogging remains owned by ``core.risk_engine``.
"""

from dataclasses import dataclass
from typing import Dict, Mapping, Sequence


@dataclass(frozen=True)
class DomainAssessment:
    domain: str
    level: str
    score: int | None
    maximum_score: int
    factors: Dict[str, int]
    explanation: str
    uncertainty: str
    actions: Sequence[str]


DOMAIN_PROFILES = {
    "River & Erosion": {
        "fields": ("River proximity", "Observed erosion", "Bank condition", "Exposure context"),
        "actions": ("Monitor official river and disaster-management information.", "Avoid entering unstable banks or fast-moving water.", "Report observed hazards to the appropriate local authority."),
    },
    "Heat Risk": {
        "fields": ("Heat exposure", "Duration", "Urban conditions", "Vulnerability context"),
        "actions": ("Use reliable public-health guidance during heat events.", "Reduce strenuous exposure where practical and maintain hydration.", "Check on people who may be more vulnerable to heat."),
    },
    "Air Pollution": {
        "fields": ("Air-quality condition", "Exposure duration", "Outdoor exposure", "Sensitive-group context"),
        "actions": ("Check authoritative air-quality and public-health guidance.", "Reduce unnecessary exposure when conditions are poor.", "Consider sensitive people when planning outdoor activity."),
    },
    "Water Security": {
        "fields": ("Availability", "Reliability", "Contamination concern", "Drought / water stress"),
        "actions": ("Use trusted public-health or water-authority guidance.", "Do not assume untreated water is safe when contamination is suspected.", "Record local service concerns for the responsible authority."),
    },
    "Agriculture & Environmental Stress": {
        "fields": ("Rainfall / water stress", "Soil / land condition", "Crop exposure", "Drainage context"),
        "actions": ("Use local agricultural extension guidance for decisions.", "Monitor drainage, soil and crop conditions over time.", "Avoid treating this prototype as a crop or yield forecast."),
    },
    "Waste & Environmental Concerns": {
        "fields": ("Waste accumulation", "Drainage blockage", "Plastic exposure", "Environmental management"),
        "actions": ("Report hazardous accumulation or blocked drainage to the responsible authority.", "Avoid direct contact with unknown waste or contaminated water.", "Use local waste-management guidance for safe handling."),
    },
}

SEVERITY_OPTIONS = ("Unknown", "Low", "Moderate", "High")


def _score(value: str) -> int | None:
    normalized = str(value).strip().lower()
    if normalized == "unknown" or normalized == "":
        return None
    return {"low": 0, "moderate": 1, "high": 2}.get(normalized, None)


def assess_domain(domain: str, values: Mapping[str, str]) -> DomainAssessment:
    """Assess a non-flood domain using transparent categorical prototype rules."""
    if domain not in DOMAIN_PROFILES:
        raise ValueError(f"Unsupported prototype domain: {domain}")

    profile = DOMAIN_PROFILES[domain]
    factors: Dict[str, int] = {}
    missing = []
    for field in profile["fields"]:
        value = values.get(field, "Unknown")
        score = _score(value)
        if score is None:
            missing.append(field)
        else:
            factors[field] = score

    maximum_score = len(profile["fields"]) * 2
    if missing:
        return DomainAssessment(
            domain=domain,
            level="INSUFFICIENT DATA",
            score=None,
            maximum_score=maximum_score,
            factors=factors,
            explanation="This structured prototype review needs all domain inputs before it can provide a relative assessment.",
            uncertainty="Missing inputs: " + ", ".join(missing) + ". This is not a validated environmental forecast.",
            actions=profile["actions"],
        )

    score = sum(factors.values())
    if score >= round(maximum_score * 0.75):
        level = "HIGH"
    elif score >= round(maximum_score * 0.4):
        level = "MODERATE"
    else:
        level = "LOW"

    important = [name for name, value in factors.items() if value >= 2]
    driver_text = ", ".join(important) if important else "the supplied domain inputs"
    return DomainAssessment(
        domain=domain,
        level=level,
        score=score,
        maximum_score=maximum_score,
        factors=factors,
        explanation=f"The prototype relative assessment is {level} based on {driver_text}.",
        uncertainty="This is a transparent prototype review using manual categorical inputs. It does not replace official warnings, forecasts, professional advice or local authority instructions.",
        actions=profile["actions"],
    )
