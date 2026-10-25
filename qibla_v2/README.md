# Qibla 2.0

This development branch contains the next Qibla iteration: a shared calculation engine, prayer-time calculations, a Termux-hosted web app, offline-first caching, and an Android WebView project.

## Source bundle

The complete generated project bundle is available as `qibla_v2.zip` in the ChatGPT conversation that prepared this branch. This repository branch is being populated with source files in reviewable form; do not treat this branch as a tested Android APK release.

## Termux

```sh
pkg update && pkg upgrade
pkg install python git
python -m unittest -v
python server.py
```

Open `http://127.0.0.1:8765`. The Python backend uses only the standard library. Map tiles and city search need internet; calculations and saved settings are designed to work offline.

## Important limitations

Prayer times are compact astronomical estimates and need verification against a trusted local timetable. Map tiles cache as visited; this branch does not bulk-download offline map regions. The Android project requires Android Studio/SDK to build and has not yet been device-tested.