"""Serve the Streamline landing page and live demo recommendation API."""

from __future__ import annotations

import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from landing.demo_recommend import build_demo_recommendation  # noqa: E402


class LandingHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/recommend":
            self._handle_recommend(parsed.query)
            return
        super().do_GET()

    def _handle_recommend(self, query: str) -> None:
        params = parse_qs(query)
        raw = (params.get("q") or params.get("ticker") or [""])[0]
        try:
            payload = build_demo_recommendation(raw)
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except ValueError as exc:
            body = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(400)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            body = json.dumps(
                {"error": "Unable to fetch live data right now. Try again in a moment."}
            ).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def main() -> None:
    port = 8080
    # Bind all interfaces so localhost / 127.0.0.1 both work reliably.
    server = ThreadingHTTPServer(("0.0.0.0", port), LandingHandler)
    print(f"Landing + live demo API at http://127.0.0.1:{port}", flush=True)
    print(f"Also try http://localhost:{port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()
