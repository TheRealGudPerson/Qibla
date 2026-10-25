#!/usr/bin/env python3
"""Local Qibla web server. Python standard library only."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime
import json
import os

from qibla_core import (
    qibla_bearing, compass_direction, distance_to_kaaba_km,
    solar_position, prayer_times,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web") if os.path.isdir(os.path.join(BASE_DIR, "web")) else BASE_DIR
HOST = "127.0.0.1"
PORT = int(os.environ.get("QIBLA_PORT", "8765"))
STATIC = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/qibla-engine.js": ("qibla-engine.js", "text/javascript; charset=utf-8"),
    "/service-worker.js": ("service-worker.js", "text/javascript; charset=utf-8"),
    "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json; charset=utf-8"),
    "/qibla-icon.svg": ("qibla-icon.svg", "image/svg+xml"),
}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json; charset=utf-8", cache="no-store"):
        raw = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", cache)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in STATIC:
            filename, content_type = STATIC[parsed.path]
            try:
                with open(os.path.join(WEB_DIR, filename), "rb") as f:
                    cache = "no-cache" if filename in ("service-worker.js", "index.html") else "public, max-age=3600"
                    self._send(200, f.read(), content_type, cache)
            except OSError as exc:
                self._send(500, json.dumps({"error": str(exc)}))
            return
        if parsed.path == "/api/health":
            self._send(200, json.dumps({"ok": True, "app": "Qibla", "version": 2}))
            return
        if parsed.path == "/api/qibla":
            try:
                q = parse_qs(parsed.query)
                lat, lon = float(q["lat"][0]), float(q["lon"][0])
                b = qibla_bearing(lat, lon)
                self._send(200, json.dumps({
                    "latitude": lat, "longitude": lon, "bearing": b,
                    "direction": compass_direction(b),
                    "distance_km": distance_to_kaaba_km(lat, lon),
                    "sun": solar_position(lat, lon),
                }))
            except (KeyError, ValueError, IndexError) as exc:
                self._send(400, json.dumps({"error": f"Invalid coordinates: {exc}"}))
            return
        if parsed.path == "/api/prayer-times":
            try:
                q = parse_qs(parsed.query)
                lat, lon = float(q["lat"][0]), float(q["lon"][0])
                date_text = q.get("date", [""])[0]
                when = datetime.fromisoformat(date_text) if date_text else datetime.now().astimezone()
                method = q.get("method", ["MWL"])[0]
                asr = q.get("asr", ["standard"])[0]
                default_offset = int(when.astimezone().utcoffset().total_seconds() / 60) if when.tzinfo else 0
                offset = int(q.get("offset", [str(default_offset)])[0])
                result = prayer_times(lat, lon, when, method, asr, offset)
                self._send(200, json.dumps(result))
            except (KeyError, ValueError, IndexError, TypeError) as exc:
                self._send(400, json.dumps({"error": f"Invalid prayer-time request: {exc}"}))
            return
        if parsed.path == "/api/geocode":
            place = parse_qs(parsed.query).get("q", [""])[0].strip()
            if not place:
                self._send(400, json.dumps({"error": "Enter a city or place name."}))
                return
            try:
                url = "https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=" + quote(place)
                req = Request(url, headers={"User-Agent": "Qibla/2.0 (personal use)", "Accept-Language": "en"})
                with urlopen(req, timeout=15) as response:
                    results = json.loads(response.read().decode("utf-8"))
                if not results:
                    self._send(404, json.dumps({"error": "Place not found. Try adding state or country."}))
                    return
                item = results[0]
                self._send(200, json.dumps({
                    "latitude": float(item["lat"]), "longitude": float(item["lon"]),
                    "name": item.get("display_name", place),
                }))
            except (URLError, HTTPError, TimeoutError, ValueError, KeyError) as exc:
                self._send(502, json.dumps({"error": f"City lookup failed: {exc}"}))
            return
        self._send(404, json.dumps({"error": "Not found"}))

    def log_message(self, fmt, *args):
        print("[http] " + fmt % args)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Qibla is running at http://{HOST}:{PORT}")
    print("Open this address in your Android browser. Keep Termux running.")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Qibla.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
