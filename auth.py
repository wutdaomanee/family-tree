"""
Session-based authentication for the Family Tree web UI.
Uses in-memory session store with signed tokens (no Flask dependency).
"""
import secrets
import time
from functools import wraps
from database import get_user

# session_token → {user_id, username, role, expires}
_sessions: dict = {}
SESSION_TTL = 60 * 60 * 8  # 8 hours
COOKIE_NAME = "ft_session"


def create_session(user) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "user_id":  user["id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "role":     user["role"],
        "expires":  time.time() + SESSION_TTL,
    }
    return token


def get_session(token: str) -> dict | None:
    if not token:
        return None
    sess = _sessions.get(token)
    if not sess:
        return None
    if time.time() > sess["expires"]:
        del _sessions[token]
        return None
    return sess


def destroy_session(token: str):
    _sessions.pop(token, None)


def get_token_from_request(handler) -> str:
    """Parse Cookie header and return session token."""
    cookie_header = handler.headers.get("Cookie", "")
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith(COOKIE_NAME + "="):
            return part[len(COOKIE_NAME) + 1:]
    return ""


def set_session_cookie(handler, token: str):
    handler.send_header(
        "Set-Cookie",
        f"{COOKIE_NAME}={token}; Path=/; HttpOnly; Max-Age={SESSION_TTL}"
    )


def clear_session_cookie(handler):
    handler.send_header(
        "Set-Cookie",
        f"{COOKIE_NAME}=; Path=/; HttpOnly; Max-Age=0"
    )


def current_user(handler) -> dict | None:
    return get_session(get_token_from_request(handler))


def is_admin(handler) -> bool:
    user = current_user(handler)
    return user is not None and user["role"] == "admin"


def is_admin_or_contribute(user: dict | None) -> bool:
    return user is not None and user["role"] in ("admin", "contribute")


def can_edit_member(user: dict | None, member_created_by) -> bool:
    """Admin can edit all; contribute can only edit members they created."""
    if user is None:
        return False
    if user["role"] == "admin":
        return True
    if user["role"] == "contribute":
        return member_created_by is not None and int(member_created_by) == int(user["user_id"])
    return False


def require_contribute(handler) -> dict | None:
    """Return user if admin or contribute, else 403."""
    user = current_user(handler)
    if not user:
        handler.redirect("/login?next=" + handler.path)
        return None
    if user["role"] not in ("admin", "contribute"):
        handler.send_error_page(403)
        return None
    return user


def require_login(handler) -> dict | None:
    """
    Return current user if logged in.
    If not, send a redirect to /login and return None.
    Call as: user = require_login(self); if not user: return
    """
    user = current_user(handler)
    if not user:
        handler.redirect("/login?next=" + handler.path)
        return None
    return user


def require_admin(handler) -> dict | None:
    """Return current user only if admin, else send 403."""
    user = current_user(handler)
    if not user:
        handler.redirect("/login?next=" + handler.path)
        return None
    if user["role"] != "admin":
        handler.send_error_page(403)
        return None
    return user
