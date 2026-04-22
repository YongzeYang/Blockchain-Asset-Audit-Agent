"""Invite code gate for write endpoints.

The list is intentionally hard-coded (per project owner request) so a public
deployment cannot be drained by anonymous traffic. Treat it as a lightweight
deterrent, not as authentication.
"""
from __future__ import annotations

from fastapi import Header, HTTPException, status

VALID_INVITE_CODES: frozenset[str] = frozenset({"Chrissy", "Ethan"})


def require_invite_code(
    x_invite_code: str | None = Header(default=None, alias="X-Invite-Code"),
) -> str:
    if not x_invite_code or x_invite_code.strip() not in VALID_INVITE_CODES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_invite_code",
            headers={"WWW-Authenticate": "InviteCode"},
        )
    return x_invite_code.strip()
