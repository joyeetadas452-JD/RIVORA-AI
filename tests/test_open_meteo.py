import json
from types import SimpleNamespace
from urllib.error import URLError

import pytest

from core.open_meteo import (
    LocationNotFoundError,
    OpenMeteoUnavailableError,
    RainfallDataMissingError,
    fetch_recent_rainfall,
    optional_weather_field,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_legacy_observation_without_optional_fields_does_not_crash():
    legacy_observation = SimpleNamespace(recent_total_mm=4.2)

    assert optional_weather_field(legacy_observation, "precipitation_mm") is None
    assert optional_weather_field(legacy_observation, "temperature_c") is None


def test_fetch_recent_rainfall_maps_recent_values(monkeypatch):
    responses = iter(
        [
            {
                "results": [
                    {
                        "name": "Guwahati",
                        "country": "India",
                        "latitude": 26.1,
                        "longitude": 91.7,
                    }
                ]
            },
            {
                "current": {
                    "time": "2026-09-18T04:00",
                    "temperature_2m": 28.5,
                    "precipitation": 0.4,
                    "wind_speed_10m": 12.0,
                    "wind_direction_10m": 90,
                },
                "timezone": "Asia/Kolkata",
                "hourly": {
                    "time": [
                        "2026-09-17T02:00",
                        "2026-09-17T03:00",
                        "2026-09-17T04:00",
                        "2026-09-18T03:00",
                        "2026-09-18T04:00",
                        "2026-09-18T05:00",
                    ],
                    "precipitation": [0, 2, 4, 1, 0, 50],
                },
            },
        ]
    )

    monkeypatch.setattr(
        "core.open_meteo.urlopen",
        lambda request, timeout: FakeResponse(next(responses)),
    )

    result = fetch_recent_rainfall("Guwahati")

    assert result.intensity == "Moderate"
    assert result.duration_hours == 3
    assert result.recent_total_mm == 7
    assert result.latitude == 26.1
    assert result.temperature_c == 28.5
    assert result.precipitation_mm == 0.4
    assert result.wind_speed_kmh == 12
    assert result.timezone == "Asia/Kolkata"


def test_invalid_location_is_reported(monkeypatch):
    monkeypatch.setattr(
        "core.open_meteo.urlopen",
        lambda request, timeout: FakeResponse({"results": []}),
    )

    with pytest.raises(LocationNotFoundError):
        fetch_recent_rainfall("not a real place")


def test_missing_rainfall_is_reported(monkeypatch):
    responses = iter(
        [
            {"results": [{"name": "Guwahati", "latitude": 26.1, "longitude": 91.7}]},
            {"hourly": {}},
        ]
    )
    monkeypatch.setattr(
        "core.open_meteo.urlopen",
        lambda request, timeout: FakeResponse(next(responses)),
    )

    with pytest.raises(RainfallDataMissingError):
        fetch_recent_rainfall("Guwahati")


def test_network_failure_is_reported(monkeypatch):
    def raise_network_error(request, timeout):
        raise URLError("timed out")

    monkeypatch.setattr("core.open_meteo.urlopen", raise_network_error)

    with pytest.raises(OpenMeteoUnavailableError):
        fetch_recent_rainfall("Guwahati")