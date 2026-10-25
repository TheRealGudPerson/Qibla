# Qibla

The default branch retains the original Termux Qibla Finder. The `v2-full-islamic-utility` branch contains the next iteration under `qibla_v2/`, including the updated web app, shared calculation engine, prayer-time calculations, offline caching, and an Android Studio project.

## Try the development branch

```sh
git clone --branch v2-full-islamic-utility https://github.com/TheRealGudPerson/Qibla.git
cd Qibla/qibla_v2
python -m unittest -v
node test_qibla_engine.js
python server.py
```

Open `http://127.0.0.1:8765` on the Android device running Termux. No pip dependencies are required.

See [Qibla 2.0 documentation](qibla_v2/README.md) for setup and limitations. This branch is a development version, not a signed APK release. Prayer-time estimates should be checked against a trusted local timetable. Offline map tiles cache as visited; the app does not bulk-download map regions.
