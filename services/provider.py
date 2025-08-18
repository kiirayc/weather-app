from __future__ import annotations
import requests
from datetime import date
from typing import Optional

def geocode_location(query: str) -> Optional[dict]:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    r = requests.get(
        url,
        params={"name": query, "count": 1, "language": "en", "format": "json"},
        timeout=20,
    )
    if r.status_code != 200:
        return None
    js = r.json() or {}
    results = js.get("results") or []
    if not results:
        return None
    top = results[0]
    return {
        "name": top.get("name"),
        "country": top.get("country"),
        "latitude": top.get("latitude"),
        "longitude": top.get("longitude"),
    }

def get_current_weather_openweather(lat: float, lon: float, api_key: str) -> dict:
    url = "https://api.openweathermap.org/data/2.5/weather"
    r = requests.get(
        url,
        params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
        timeout=20,
    )
    r.raise_for_status()
    js = r.json()
    return {
        "provider": "openweather",
        "coord": js.get("coord"),
        "weather": js.get("weather", []),
        "main": js.get("main", {}),
        "wind": js.get("wind", {}),
        "clouds": js.get("clouds", {}),
        "name": js.get("name"),
        "dt": js.get("dt"),
        "sys": js.get("sys", {}),
    }

def get_forecast_openweather(lat: float, lon: float, api_key: str) -> dict:
    url = "https://api.openweathermap.org/data/2.5/forecast"
    r = requests.get(
        url,
        params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()

def get_historical_open_meteo(lat: float, lon: float, start: date, end: date) -> list[dict]:
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        # API expects comma-separated string
        "daily": "temperature_2m_min,temperature_2m_max,temperature_2m_mean",
        "timezone": "auto",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    js = r.json()
    days = js.get("daily", {})
    out: list[dict] = []
    for i, d in enumerate(days.get("time", []) or []):
        out.append(
            {
                "date": d,
                "t_min": _safe_num(days.get("temperature_2m_min", []), i),
                "t_max": _safe_num(days.get("temperature_2m_max", []), i),
                "t_mean": _safe_num(days.get("temperature_2m_mean", []), i),
            }
        )
    return out

def _safe_num(arr, i):
    try:
        return float(arr[i]) if arr and arr[i] is not None else None
    except Exception:
        return None
