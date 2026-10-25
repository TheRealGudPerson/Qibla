import unittest
from datetime import datetime, timezone
from qibla_core import (
    qibla_bearing, compass_direction, distance_to_kaaba_km,
    destination_point, solar_position, prayer_times
)


class QiblaTests(unittest.TestCase):
    def test_tallahassee_bearing(self):
        self.assertAlmostEqual(qibla_bearing(30.4383, -84.2807), 53.1, delta=1.0)

    def test_compass_directions(self):
        self.assertEqual(compass_direction(0), "N")
        self.assertEqual(compass_direction(53), "NE")
        self.assertEqual(compass_direction(180), "S")

    def test_distance_positive(self):
        self.assertGreater(distance_to_kaaba_km(30.4383, -84.2807), 0)

    def test_kaaba_distance_near_zero(self):
        self.assertAlmostEqual(distance_to_kaaba_km(21.422487, 39.826206), 0, places=5)

    def test_invalid_coordinates(self):
        with self.assertRaises(ValueError):
            qibla_bearing(91, 0)
        with self.assertRaises(ValueError):
            qibla_bearing(0, 181)

    def test_destination_point(self):
        lat, lon = destination_point(30.4383, -84.2807, qibla_bearing(30.4383, -84.2807), 100)
        self.assertTrue(-90 <= lat <= 90)
        self.assertTrue(-180 <= lon <= 180)

    def test_solar_position(self):
        result = solar_position(30.4383, -84.2807, datetime(2026, 6, 21, 16, tzinfo=timezone.utc))
        self.assertIn("azimuth", result)
        self.assertIn("elevation", result)
        self.assertTrue(0 <= result["azimuth"] < 360)

    def test_prayer_times_complete(self):
        result = prayer_times(30.4383, -84.2807, datetime(2026, 10, 25, 12, tzinfo=timezone.utc),
                              method="ISNA", asr="hanafi", utc_offset_minutes=-240)
        self.assertFalse(result["unavailable"])
        self.assertEqual(set(result["times"]), {"Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha"})
        for value in result["times"].values():
            self.assertRegex(value, r"^\d{2}:\d{2}$")
        self.assertEqual(result["asr"], "Hanafi")

    def test_prayer_times_methods_change_fajr(self):
        when = datetime(2026, 10, 25, 12, tzinfo=timezone.utc)
        a = prayer_times(30.4383, -84.2807, when, "ISNA", utc_offset_minutes=-240)
        b = prayer_times(30.4383, -84.2807, when, "MWL", utc_offset_minutes=-240)
        self.assertNotEqual(a["times"]["Fajr"], b["times"]["Fajr"])


if __name__ == "__main__":
    unittest.main()
