# Qibla 2.0

Qibla is an offline-first Qibla direction and prayer-time utility. This folder contains the Termux-hosted web app, shared JavaScript calculation engine, Python API/calculation module, tests, and Android WebView project.

## Features

- Great-circle Qibla bearing from true north and distance to the Kaaba.
- Location through browser GPS, manual coordinates, and city search.
- North-up map with Qibla line and reported GPS accuracy.
- Live browser orientation where supported and native Android rotation-vector heading with geomagnetic correction.
- Prayer times for Fajr, sunrise, Dhuhr, Asr, Maghrib, and Isha; seven method presets and Standard/Hanafi Asr.
- Local settings and saved location.
- PWA app-shell caching and bounded cache for map tiles as viewed.
- Native Android Studio project loading the shared UI and calculation engine from assets.

## Termux setup

```sh
pkg update && pkg upgrade
pkg install python git
cd qibla_v2
python -m unittest -v
node test_qibla_engine.js
python server.py
```

Open `http://127.0.0.1:8765`. Python uses only its standard library. Node.js is optional and needed only for the JavaScript test.

## Android build

Open `android/` in Android Studio with Android SDK 35 installed, sync Gradle, then choose **Build → Build APK(s)**. The expected output is `android/app/build/outputs/apk/debug/app-debug.apk`. Command-line build on a configured computer:

```sh
cd android
gradle assembleDebug
```

The APK has not been built or device-tested in this environment.

## Offline and accuracy notes

- Qibla and prayer calculations run locally. Saved settings use local storage.
- On the Termux web app, the service worker caches the app shell and previously viewed map tiles. Map tiles are not bulk-downloaded.
- The Android app bundles the HTML and calculation engine, but map styling and map tiles still require internet unless already available to the WebView cache.
- City search uses OpenStreetMap Nominatim and requires internet.
- Prayer times are compact astronomical estimates. High-latitude rules and local conventions can differ; verify times and method choices with a trusted local mosque before relying on them for worship.
- Phone compass readings can be distorted by magnets, metal, and poor calibration.
