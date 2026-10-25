#!/usr/bin/env python3
"""Local web server for the Qibla Finder UI. Standard library only."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HOST = "127.0.0.1"
PORT = 8765


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json; charset=utf-8"):
        raw = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            try:
                with open(os.path.join(BASE_DIR, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError as exc:
                self._send(500, json.dumps({"error": str(exc)}))
            return

        if parsed.path == "/api/geocode":
            place_query = parse_qs(parsed.query).get("q", [""])[0].strip()
            if not place_query:
                self._send(400, json.dumps({"error": "Enter a city or place name."}))
                return
            try:
                url = ("https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q="
                       + quote(place_query))
                req = Request(url, headers={
                    "User-Agent": "QiblaFinderTermux/1.0 (personal use)"
                })
                with urlopen(req, timeout=15) as response:
                    results = json.loads(response.read().decode("utf-8"))
                if not results:
                    self._send(404, json.dumps({
                        "error": "Place not found. Try adding state or country."
                    }))
                    return
                item = results[0]
                self._send(200, json.dumps({
                    "latitude": float(item["lat"]),
                    "longitude": float(item["lon"]),
                    "name": item.get("display_name", place_query),
                }))
            except (URLError, HTTPError, TimeoutError, ValueError, KeyError) as exc:
                self._send(502, json.dumps({"error": f"City lookup failed: {exc}"}))
            return

        self._send(404, json.dumps({"error": "Not found"}))

    def log_message(self, fmt, *args):
        print("[http] " + fmt % args)


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Qibla Finder is running at http://{HOST}:{PORT}")
    print("Open this address in your Android browser.")
    print("Keep this Termux session running; press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Qibla Finder.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
