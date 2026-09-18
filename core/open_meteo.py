"""Small Open-Meteo adapter for location lookup and recent rainfall."""

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class OpenMeteoError(Exception):
    """Base error for user-facing Open-Meteo failures."""


class LocationNotFoundError(OpenMeteoError):
    """The geocoder returned no usable location."""


class RainfallDataMissingError(OpenMeteoError):
    """The weather response did not contain usable rainfall data."""


class OpenMeteoUnavailableError(OpenMeteoError):
    """Open-Meteo could not be reached or returned an invalid response."""


@dataclass(frozen=True)
class RainfallObservation:
    location_name: str
    country: str
    latitude: float
    longitude: float
    recent_total_mm: float
    wet_hours: float
    intensity: str
    duration_hours: float
    temperature_c: float | None = None
    precipitation_mm: float | None = None
    wind_speed_kmh: float | None = None
    wind_direction_degrees: float | None = None
    observation_time: str | None = None
    timezone: str | None = None


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def optional_weather_field(observation: Any, field_name: str) -> Any:
    """Return optional weather metadata without breaking older session objects."""
    return getattr(observation, field_name, None)


def _get_json(url: str, params: Dict[str, Any], timeout: float = 8.0) -> Dict[str, Any]:
    request = Request(
        f"{url}?{urlencode(params)}",
        headers={"User-Agent": "RIVORA-AI prototype"},
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise OpenMeteoUnavailableError(
            "Open-Meteo is currently unavailable. You can enter rainfall manually."
        ) from exc

    if not isinstance(payload, dict):
        raise OpenMeteoUnavailableError(
            "Open-Meteo returned an unexpected response. You can enter rainfall manually."
        )
    return payload


def _find_location(query: str) -> Dict[str, Any]:
    if not query.strip():
        raise LocationNotFoundError(
            "Enter a city or general area name, not an exact private address."
        )

    payload = _get_json(
        GEOCODING_URL,
        {"name": query.strip(), "count": 1, "language": "en", "format": "json"},
    )
    results = payload.get("results")
    if not isinstance(results, list) or not results or not isinstance(results[0], dict):
        raise LocationNotFoundError(
            "No matching city or general area was found. Check the spelling or use manual rainfall input."
        )

    location = results[0]
    if not isinstance(location.get("latitude"), (int, float)) or not isinstance(
        location.get("longitude"), (int, float)
    ):
        raise LocationNotFoundError(
            "The location result did not include usable coordinates. Use manual rainfall input."
        )
    return location


def _recent_hourly_values(
    hourly: Dict[str, Any], current_time: str | None = None
) -> List[float]:
    values = hourly.get("precipitation")
    if not isinstance(values, list):
        raise RainfallDataMissingError(
            "Rainfall data was not included for this location. Enter it manually."
        )

    if current_time and isinstance(hourly.get("time"), list):
        try:
            cutoff = datetime.fromisoformat(current_time)
            recent_indices = [
                index
                for index, timestamp in enumerate(hourly["time"])
                if isinstance(timestamp, str)
                and datetime.fromisoformat(timestamp) <= cutoff
            ]
            if recent_indices:
                values = [values[index] for index in recent_indices[-24:] if index < len(values)]
        except (TypeError, ValueError):
            pass

    numeric_values = [value for value in values if isinstance(value, (int, float))]
    if not numeric_values:
        raise RainfallDataMissingError(
            "No usable recent rainfall values were returned. Enter rainfall manually."
        )
    return numeric_values[-24:]


def _classify_rainfall(values: List[float]) -> tuple[str, float, float]:
    total_mm = sum(max(value, 0.0) for value in values)
    wet_hours = sum(1 for value in values if value > 0)
    maximum_hourly_mm = max(values)

    if maximum_hourly_mm >= 15 or total_mm >= 50:
        intensity = "Very Heavy"
    elif maximum_hourly_mm >= 7.5 or total_mm >= 20:
        intensity = "Heavy"
    elif maximum_hourly_mm >= 2.5 or total_mm >= 5:
        intensity = "Moderate"
    else:
        intensity = "Light"

    return intensity, float(wet_hours), round(total_mm, 1)


def fetch_recent_rainfall(location_query: str) -> RainfallObservation:
    """Geocode a general location and retrieve its recent hourly precipitation."""
    location = _find_location(location_query)
    latitude = float(location["latitude"])
    longitude = float(location["longitude"])

    weather = _get_json(
        FORECAST_URL,
        {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "precipitation",
            "current": "temperature_2m,precipitation,wind_speed_10m,wind_direction_10m",
            "past_days": 1,
            "forecast_days": 1,
            "timezone": "auto",
        },
    )
    hourly = weather.get("hourly")
    if not isinstance(hourly, dict):
        raise RainfallDataMissingError(
            "Rainfall data was not included for this location. Enter it manually."
        )

    current = weather.get("current")
    current_time = current.get("time") if isinstance(current, dict) else None
    intensity, duration_hours, total_mm = _classify_rainfall(
        _recent_hourly_values(hourly, current_time)
    )
    return RainfallObservation(
        location_name=str(location.get("name", location_query.strip())),
        country=str(location.get("country", "")),
        latitude=latitude,
        longitude=longitude,
        recent_total_mm=total_mm,
        wet_hours=duration_hours,
        intensity=intensity,
        duration_hours=duration_hours,
        temperature_c=(
            float(current["temperature_2m"])
            if isinstance(current, dict)
            and isinstance(current.get("temperature_2m"), (int, float))
            else None
        ),
        precipitation_mm=(
            float(current["precipitation"])
            if isinstance(current, dict)
            and isinstance(current.get("precipitation"), (int, float))
            else None
        ),
        wind_speed_kmh=(
            float(current["wind_speed_10m"])
            if isinstance(current, dict)
            and isinstance(current.get("wind_speed_10m"), (int, float))
            else None
        ),
        wind_direction_degrees=(
            float(current["wind_direction_10m"])
            if isinstance(current, dict)
            and isinstance(current.get("wind_direction_10m"), (int, float))
            else None
        ),
        observation_time=current_time,
        timezone=str(weather.get("timezone")) if weather.get("timezone") else None,
    )