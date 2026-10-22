import re
import time
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_REQUEST_ID_PATTERN = re.compile(r"[a-zA-Z0-9._-]{1,64}")


class ResponseHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()

        request_headers = dict(scope.get("headers", []))
        incoming_id = request_headers.get(b"x-request-id", b"").decode("latin-1")

        request_id = (
            incoming_id if _REQUEST_ID_PATTERN.fullmatch(incoming_id) else str(uuid4())
        )

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower()
                    not in {
                        b"x-request-id",
                        b"x-process-time",
                        b"x-content-type-options",
                        b"x-frame-options",
                        b"referrer-policy",
                        b"permissions-policy",
                    }
                ]

                headers.extend(
                    [
                        (b"x-request-id", request_id.encode("ascii")),
                        (
                            b"x-process-time",
                            f"{time.perf_counter() - start_time:.6f}".encode("ascii"),
                        ),
                        (b"x-content-type-options", b"nosniff"),
                        (b"x-frame-options", b"DENY"),
                        (
                            b"referrer-policy",
                            b"strict-origin-when-cross-origin",
                        ),
                        (
                            b"permissions-policy",
                            b"camera=(), microphone=(), geolocation=()",
                        ),
                    ]
                )

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_with_headers)
