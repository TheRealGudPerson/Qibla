# Qibla Finder Plus

A mobile-friendly Qibla finder designed to run in Termux on Android. It intentionally does not use the phone's magnetometer or gyroscope.

## Features

- Qibla bearing clockwise from true north, plus distance to the Kaaba.
- Current location through browser geolocation.
- Search for a city or place using OpenStreetMap Nominatim.
- Manual latitude/longitude entry.
- North-up map with a Qibla bearing line and Kaaba marker.
- Reported location accuracy indicator.
- Approximate solar azimuth and elevation for optional sun-position guidance.
- Optional manual entry of a trusted external **true-north** heading.
- Python standard-library calculation engine and automated tests.

## Run in Termux

1. Install Termux from a trusted distribution.
2. Extract or clone this repository into a folder accessible to Termux.
3. Run:

   ```sh
   pkg update
   pkg install python
   python -m unittest -v
   python server.py
   ```

4. Open **http://127.0.0.1:8765** in Chrome or another Android browser.
5. Tap **Use current GPS** and grant location permission.

Keep the Termux session running while using the app. Browser geolocation may use GPS, Wi-Fi, or network location depending on Android settings.

## Python requirements

The app currently uses only the Python standard library. No third-party Python packages are required. See [requirements.txt](requirements.txt).

## Internet requirements

- Qibla math and solar-position calculation work offline.
- City lookup requires internet and uses OpenStreetMap Nominatim.
- Map tiles and the Leaflet JavaScript library are loaded online.
- If offline, calculation features remain available once coordinates are known, but the map background and city lookup will not work.

## Accuracy and limitations

- Bearings are measured clockwise from **true north**, not magnetic north.
- A north-up map does not know which way the phone is physically facing. Use visible landmarks or another external reference to align the map with the real world.
- Solar position is approximate and should be treated as a supplementary guide.
- GPS accuracy is the value reported by the browser; it is not a guarantee of Qibla-direction accuracy.
- The external heading field is manual. The app does not connect to or validate a GNSS heading device.
- Map data © OpenStreetMap contributors. Nominatim has a usage policy; avoid bulk or repeated automated geocoding.

## Test on Fedora

```sh
python3 -m unittest -v
python3 server.py
```

Then open http://127.0.0.1:8765 in a browser.
