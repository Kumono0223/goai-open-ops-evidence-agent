from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .analyzer import analyze_csv, profile_csv


class Handler(BaseHTTPRequestHandler):
    root = Path.cwd().resolve()

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if urlparse(self.path).path == "/health":
            self._json(200, {"ok": True, "service": "local-productivity-analytics", "root": str(self.root)})
            return
        self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path not in ("/analyze", "/profile"):
            self._json(404, {"error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 128_000:
                raise ValueError("request too large")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            requested = (self.root / str(payload.get("csv_path", ""))).resolve()
            if self.root not in requested.parents and requested != self.root:
                raise ValueError("csv_path must stay inside the configured root")
            if requested.suffix.lower() != ".csv":
                raise ValueError("csv_path must point to a .csv file")
            result = profile_csv(requested) if urlparse(self.path).path == "/profile" else analyze_csv(requested, str(payload.get("query", "")))
            self._json(200, result)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})

    def log_message(self, *_args) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(description="Local productivity analytics HTTP server")
    parser.add_argument("--root", default=".", help="allowed CSV root directory")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    Handler.root = Path(args.root).resolve()
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()

