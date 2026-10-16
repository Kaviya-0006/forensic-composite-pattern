import secrets
from typing import Dict, Optional

from .errors import AuthError

USERS = {"kaviya": {"password": "forensic123", "name": "Kaviya J", "title": "Lead Forensic Examiner"},
         "arjun": {"password": "forensic123", "name": "Arjun Rao", "title": "Digital Forensics Analyst"},
         "meera": {"password": "forensic123", "name": "Meera Nair", "title": "Mobile Forensics Specialist"}}
_sessions: Dict[str, Dict[str, str]] = {}


def login(username: str, password: str) -> Dict[str, object]:
    user = USERS.get(username.lower())
    if not user or user["password"] != password:
        raise AuthError("Invalid username or password.")
    token = secrets.token_urlsafe(24)
    _sessions[token] = {"username": username.lower(), "name": user["name"], "title": user["title"]}
    return {"token": token, "user": _sessions[token]}


def user_for(token: Optional[str]) -> Dict[str, str]:
    if not token or token not in _sessions:
        raise AuthError("Not authenticated.")
    return _sessions[token]
