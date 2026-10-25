"""Offline Qibla bearing, distance, destination, and approximate solar position."""
import math
from datetime import datetime, timezone, timedelta

KAABA_LATITUDE = 21.422487
KAABA_LONGITUDE = 39.826206
EARTH_RADIUS_KM = 6371.0088


def _validate(latitude: float, longitude: float) -> None:
    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")
    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")


def qibla_bearing(latitude: float, longitude: float) -> float:
    """Initial great-circle bearing clockwise from true north, in [0, 360)."""
    _validate(latitude, longitude)
    lat1 = math.radians(latitude)
    lat2 = math.radians(KAABA_LATITUDE)
    delta_lon = math.radians(KAABA_LONGITUDE - longitude)
    y = math.sin(delta_lon) * math.cos(lat2)
    x = (math.cos(lat1) * math.sin(lat2)
         - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon))
    return math.degrees(math.atan2(y, x)) % 360


def compass_direction(bearing: float) -> str:
    directions = ("N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW")
    return directions[round((bearing % 360) / 22.5) % 16]


def distance_to_kaaba_km(latitude: float, longitude: float) -> float:
    _validate(latitude, longitude)
    lat1, lon1 = math.radians(latitude), math.radians(longitude)
    lat2, lon2 = math.radians(KAABA_LATITUDE), math.radians(KAABA_LONGITUDE)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    a = min(1.0, max(0.0, a))
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def destination_point(latitude: float, longitude: float, bearing: float,
                      distance_km: float = 500.0) -> tuple[float, float]:
    """Destination reached by travelling distance_km along a bearing."""
    _validate(latitude, longitude)
    angular = distance_km / EARTH_RADIUS_KM
    brng = math.radians(bearing)
    lat1, lon1 = math.radians(latitude), math.radians(longitude)
    lat2 = math.asin(math.sin(lat1) * math.cos(angular)
                     + math.cos(lat1) * math.sin(angular) * math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng) * math.sin(angular) * math.cos(lat1),
                             math.cos(angular) - math.sin(lat1) * math.sin(lat2))
    return math.degrees(lat2), (math.degrees(lon2) + 540) % 360 - 180


def solar_position(latitude: float, longitude: float, when: datetime | None = None) -> dict:
    """Approximate solar azimuth/elevation using NOAA-style equations.

    Azimuth is clockwise from true north. Intended as an orientation aid, not
    a precision astronomical instrument.
    """
    _validate(latitude, longitude)
    if when is None:
        when = datetime.now(timezone.utc)
    elif when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    when = when.astimezone(timezone.utc)
    day = when.timetuple().tm_yday
    hour = when.hour + when.minute / 60 + when.second / 3600
    gamma = 2 * math.pi / 365 * (day - 1 + (hour - 12) / 24)
    eqtime = 229.18 * (0.000075 + 0.001868 * math.cos(gamma)
                       - 0.032077 * math.sin(gamma)
                       - 0.014615 * math.cos(2 * gamma)
                       - 0.040849 * math.sin(2 * gamma))
    decl = (0.006918 - 0.399912 * math.cos(gamma)
            + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma)
            + 0.000907 * math.sin(2 * gamma)
            - 0.002697 * math.cos(3 * gamma)
            + 0.00148 * math.sin(3 * gamma))
    true_solar_minutes = (hour * 60 + eqtime + 4 * longitude) % 1440
    hour_angle = math.radians(true_solar_minutes / 4 - 180)
    lat = math.radians(latitude)
    cos_zenith = (math.sin(lat) * math.sin(decl)
                  + math.cos(lat) * math.cos(decl) * math.cos(hour_angle))
    elevation = 90 - math.degrees(math.acos(min(1.0, max(-1.0, cos_zenith))))
    azimuth = (math.degrees(math.atan2(
        math.sin(hour_angle),
        math.cos(hour_angle) * math.sin(lat) - math.tan(decl) * math.cos(lat)
    )) + 180) % 360
    return {"azimuth": azimuth, "elevation": elevation,
            "is_daylight": elevation > 0, "utc_time": when.isoformat()}


PRAYER_METHODS = {
    "MWL": {"label": "Muslim World League", "fajr": 18.0, "isha": 17.0},
    "ISNA": {"label": "ISNA", "fajr": 15.0, "isha": 15.0},
    "EGYPT": {"label": "Egyptian General Authority", "fajr": 19.5, "isha": 17.5},
    "MAKKAH": {"label": "Umm al-Qura (Makkah)", "fajr": 18.5, "isha": None, "isha_minutes": 90},
    "KARACHI": {"label": "University of Islamic Sciences, Karachi", "fajr": 18.0, "isha": 18.0},
    "TEHRAN": {"label": "Institute of Geophysics, Tehran", "fajr": 17.7, "isha": 14.0},
    "SINGAPORE": {"label": "MUIS Singapore", "fajr": 20.0, "isha": 18.0},
}


def prayer_times(latitude: float, longitude: float, when: datetime | None = None,
                 method: str = "MWL", asr: str = "standard",
                 utc_offset_minutes: int | None = None) -> dict:
    """Calculate approximate prayer times. Offset is minutes east of UTC."""
    _validate(latitude, longitude)
    if when is None:
        when = datetime.now().astimezone()
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    local_date = when.date()
    if utc_offset_minutes is None:
        offset = when.utcoffset()
        utc_offset_minutes = int(offset.total_seconds() / 60) if offset else 0
    method_key = method.upper() if method.upper() in PRAYER_METHODS else "MWL"
    config = PRAYER_METHODS[method_key]
    asr_factor = 2 if asr.lower() == "hanafi" else 1
    utc_noon = datetime(local_date.year, local_date.month, local_date.day, 12, tzinfo=timezone.utc) - timedelta(minutes=utc_offset_minutes)
    day = utc_noon.timetuple().tm_yday
    hour = utc_noon.hour + utc_noon.minute / 60
    gamma = 2 * math.pi / 365 * (day - 1 + (hour - 12) / 24)
    eq = 229.18 * (0.000075 + 0.001868 * math.cos(gamma) - 0.032077 * math.sin(gamma)
                   - 0.014615 * math.cos(2 * gamma) - 0.040849 * math.sin(2 * gamma))
    decl = (0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma)
            - 0.002697 * math.cos(3 * gamma) + 0.00148 * math.sin(3 * gamma))
    phi = math.radians(latitude)
    solar_noon = 12 + utc_offset_minutes / 60 - longitude / 15 - eq / 60

    def hour_angle(altitude: float) -> float | None:
        alt = math.radians(altitude)
        denom = math.cos(phi) * math.cos(decl)
        if abs(denom) < 1e-12:
            return None
        c = (math.sin(alt) - math.sin(phi) * math.sin(decl)) / denom
        if c < -1 or c > 1:
            return None
        return math.degrees(math.acos(c)) / 15

    sunrise_angle = hour_angle(-0.833)
    if sunrise_angle is None:
        return {"date": local_date.isoformat(), "method": config["label"], "asr": asr,
                "times": {}, "unavailable": True,
                "message": "Sunrise/sunset cannot be estimated at this latitude for this date."}
    fajr_angle = hour_angle(-config["fajr"])
    isha_angle = hour_angle(-config["isha"]) if config.get("isha") is not None else None
    if fajr_angle is None:
        fajr_angle = sunrise_angle * min(1, config["fajr"] / 60)
    if isha_angle is None and config.get("isha") is not None:
        isha_angle = sunrise_angle * min(1, config["isha"] / 60)
    sunrise, sunset = solar_noon - sunrise_angle, solar_noon + sunrise_angle
    asr_alt = math.degrees(math.atan(1 / (asr_factor + math.tan(abs(phi - decl)))))
    asr_angle = hour_angle(asr_alt)
    if asr_angle is None:
        asr_angle = sunrise_angle * 0.5
    raw = {
        "Fajr": solar_noon - (fajr_angle if fajr_angle is not None else sunrise_angle * 0.5),
        "Sunrise": sunrise, "Dhuhr": solar_noon + 1 / 60, "Asr": solar_noon + asr_angle,
        "Maghrib": sunset,
        "Isha": sunset + config["isha_minutes"] / 60 if config.get("isha_minutes") is not None
        else solar_noon + (isha_angle if isha_angle is not None else sunrise_angle * 0.5),
    }
    def format_time(value: float) -> str:
        minutes = int(math.floor((((value % 24) + 24) % 24) * 60 + 0.5)) % (24 * 60)
        return f"{minutes // 60:02d}:{minutes % 60:02d}"
    return {"date": local_date.isoformat(), "method": config["label"], "method_id": method_key,
            "asr": "Hanafi" if asr_factor == 2 else "Standard",
            "times": {name: format_time(value) for name, value in raw.items()}, "unavailable": False}
