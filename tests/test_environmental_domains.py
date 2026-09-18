import pytest

from core.environmental_domains import assess_domain


@pytest.mark.parametrize(
    "domain",
    [
        "River & Erosion",
        "Heat Risk",
        "Air Pollution",
        "Water Security",
        "Agriculture & Environmental Stress",
        "Waste & Environmental Concerns",
    ],
)
def test_domain_assessment_returns_relative_result(domain):
    fields = {
        "River & Erosion": ["River proximity", "Observed erosion", "Bank condition", "Exposure context"],
        "Heat Risk": ["Heat exposure", "Duration", "Urban conditions", "Vulnerability context"],
        "Air Pollution": ["Air-quality condition", "Exposure duration", "Outdoor exposure", "Sensitive-group context"],
        "Water Security": ["Availability", "Reliability", "Contamination concern", "Drought / water stress"],
        "Agriculture & Environmental Stress": ["Rainfall / water stress", "Soil / land condition", "Crop exposure", "Drainage context"],
        "Waste & Environmental Concerns": ["Waste accumulation", "Drainage blockage", "Plastic exposure", "Environmental management"],
    }[domain]

    result = assess_domain(domain, {field: "High" for field in fields})

    assert result.level == "HIGH"
    assert result.score == result.maximum_score
    assert result.factors
    assert result.explanation
    assert result.uncertainty
    assert result.actions


def test_domain_assessment_requires_complete_inputs():
    result = assess_domain(
        "Heat Risk",
        {
            "Heat exposure": "High",
            "Duration": "Unknown",
            "Urban conditions": "Low",
            "Vulnerability context": "Low",
        },
    )

    assert result.level == "INSUFFICIENT DATA"
    assert result.score is None
    assert "Duration" in result.uncertainty
