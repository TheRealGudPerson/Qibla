# Qibla

Qibla is a mobile-friendly Qibla direction and prayer-time utility. The current version lives in [`qibla_v2/`](qibla_v2/), with a web app that can run locally in Termux and an Android Studio project. Both share the same JavaScript calculation engine.

## Features

- Calculates the great-circle bearing to the Kaaba and distance from your location.
- Finds your location using browser GPS, manual coordinates, or an online city search.
- Displays a map, Qibla line, and GPS accuracy when location data is available.
- Uses device orientation for compass heading where supported; the Android app also uses the native rotation-vector sensor with magnetic-declination correction.
- Calculates Fajr, sunrise, Dhuhr, Asr, Maghrib, and Isha using seven method presets and Standard or Hanafi Asr.
- Saves settings and the selected location locally.
- Caches the web app shell and previously viewed map tiles for limited offline use.

## Run the web app

The web app uses Python's standard library only. No Python packages need to be installed.

### Android with Termux

Install Termux, then run:

```sh
pkg update
pkg install git python
git clone https://github.com/TheRealGudPerson/Qibla.git
cd Qibla/qibla_v2
python -m unittest -v
python server.py
```

Open **http://127.0.0.1:8765** in the Android browser on the same device.

The JavaScript engine test is optional and requires Node.js:

```sh
node test_qibla_engine.js
```

### Linux, macOS, or Windows

Install Python 3, clone the repository, and run:

```sh
git clone https://github.com/TheRealGudPerson/Qibla.git
cd Qibla/qibla_v2
python -m unittest -v
python server.py
```

Then open **http://127.0.0.1:8765** in a browser on the same computer.

## Build the Android app

Open the `qibla_v2/android/` folder in Android Studio with Android SDK 35 installed. Sync Gradle, then select **Build → Build APK(s)**.

On a computer with Gradle and the required Android SDK configured, you can also run:

```sh
cd qibla_v2/android
gradle assembleDebug
```

The expected debug APK path is `qibla_v2/android/app/build/outputs/apk/debug/app-debug.apk`.

**Build status:** The Android project has not yet been built or tested on a physical device. This repository does not currently provide a signed release APK.

## Offline use and limitations

- Qibla direction and prayer-time calculations run locally once the app is loaded.
- The web app's service worker caches the app shell and map tiles as you view them. It does not download entire map regions for offline use.
- The Android app bundles its HTML and calculation engine, but map tiles and map styling require internet unless available in the WebView cache.
- City search uses OpenStreetMap Nominatim and requires internet.
- Prayer times are astronomical estimates. Local mosque timetables, calculation conventions, and high-latitude rules may differ. Confirm the method and times with a trusted local source.
- Compass accuracy depends on the device sensors and calibration; nearby magnets and metal can affect readings.

## Project layout

- `qibla_v2/qibla_core.py` — Python geographic and prayer-time calculations.
- `qibla_v2/server.py` — local HTTP server and API.
- `qibla_v2/web/` — mobile web app, JavaScript engine, PWA manifest, and service worker.
- `qibla_v2/android/` — Android Studio project.
- `qibla_v2/test_qibla_core.py` and `qibla_v2/test_qibla_engine.js` — calculation tests.

See the [Qibla 2.0 README](qibla_v2/README.md) for more detailed setup notes.
