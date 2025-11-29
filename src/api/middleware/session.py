"""Simple per-user session middleware.

Extracts a session_id from header, query, or cookie and ensures it is attached
to the request state. If missing, a new UUID is generated and returned in both
response headers and a cookie (non-httponly for frontend JS use).
"""

import uuid
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


SESSION_HEADER = "X-Session-Id"
SESSION_COOKIE = "session_id"


def _normalize(session_id: Optional[str]) -> Optional[str]:
    if not session_id:
        return None
    return session_id.strip().strip("\"'")


class SessionMiddleware(BaseHTTPMiddleware):
    """Attach a per-user session_id to request.state and response headers."""

    async def dispatch(self, request: Request, call_next):
        session_id = (
            request.query_params.get("session_id")
            or request.headers.get(SESSION_HEADER)
            or request.cookies.get(SESSION_COOKIE)
        )
        session_id = _normalize(session_id)
        new_session = False

        if not session_id:
            session_id = uuid.uuid4().hex
            new_session = True

        request.state.session_id = session_id

        response: Response = await call_next(request)
        response.headers[SESSION_HEADER] = session_id
        if new_session:
            response.set_cookie(
                SESSION_COOKIE,
                session_id,
                httponly=False,
                samesite="lax",
                secure=False,
            )
        return response
