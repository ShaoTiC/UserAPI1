"""HTTP server for the local ticket grabbing demo."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .skill import SEAT_TYPES, TicketGrabRequest, TicketGrabber


STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


class TicketSkillHandler(SimpleHTTPRequestHandler):
    """Serves the Vue page and the JSON API used by the page."""

    grabber = TicketGrabber()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        if parsed.path == "/api/stations":
            self._json_response(
                {
                    "stations": self.grabber.stations(),
                    "seat_types": [
                        {"value": value, "label": label}
                        for value, label in SEAT_TYPES.items()
                    ],
                }
            )
            return

        if parsed.path == "/api/trains":
            query = parse_qs(parsed.query)
            origin = _first(query, "origin")
            destination = _first(query, "destination")
            travel_date = _first(query, "travel_date")
            self._json_response(
                {
                    "trains": self.grabber.trains(origin, destination, travel_date),
                    "seat_types": [
                        {"value": value, "label": label}
                        for value, label in SEAT_TYPES.items()
                    ],
                }
            )
            return

        if parsed.path in ("", "/"):
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        if parsed.path != "/api/grab-ticket":
            self.send_error(HTTPStatus.NOT_FOUND, "API endpoint not found")
            return

        try:
            payload = self._read_json_body()
            request = TicketGrabRequest.from_dict(payload)
            result = self.grabber.grab(request)
            self._json_response(result.to_dict(), status=HTTPStatus.OK)
        except json.JSONDecodeError:
            self._json_response(
                {"success": False, "message": "请求体不是合法 JSON"},
                status=HTTPStatus.BAD_REQUEST,
            )
        except Exception as exc:  # pragma: no cover - defensive HTTP boundary
            self._json_response(
                {"success": False, "message": f"服务器处理失败：{exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        super().end_headers()

    def do_OPTIONS(self) -> None:  # noqa: N802 - http.server API
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        if not body:
            return {}
        data = json.loads(body.decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _json_response(
        self,
        payload: dict[str, Any],
        *,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def _first(query: dict[str, list[str]], key: str) -> str:
    values = query.get(key) or [""]
    return values[0]


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), TicketSkillHandler)
    print(f"Ticket skill page: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
