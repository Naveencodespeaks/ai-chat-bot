from typing import Any, Dict, List, Optional

from app.auth.context import UserContext


def match_any(key: str, values: List[str]) -> Dict[str, Any]:
    """Return a simple Qdrant-style `match any` payload filter.

    Example:
        {"key": "allowed_roles", "match": {"any": ["USER"]}}
    """
    return {"key": key, "match": {"any": values}}


def match_value(key: str, value: str) -> Dict[str, Any]:
    """Return a simple Qdrant-style `match value` payload filter."""
    return {"key": key, "match": {"value": value}}


def build_filters(
    *, must: Optional[List[Dict[str, Any]]] = None, must_not: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Compose a filter dict consumable by Qdrant clients.

    Only includes keys that have content so callers can merge safely.
    """
    payload: Dict[str, Any] = {}
    if must:
        payload["must"] = must
    if must_not:
        payload["must_not"] = must_not
    return payload


def merge_filters(base: Dict[str, Any], extra: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two filter dicts by concatenating `must` and `must_not` lists.

    This is a shallow merge intended for simple composition of RBAC + custom
    constraints.
    """
    out = {"must": [], "must_not": []}

    for key in ("must", "must_not"):
        if base.get(key):
            out[key].extend(base.get(key, []))
        if extra.get(key):
            out[key].extend(extra.get(key, []))

    # remove empty lists and return
    return {k: v for k, v in out.items() if v}


def build_rbac_filters(user_context: UserContext) -> Dict[str, Any]:
    """Build RBAC-aware filters from a trusted `UserContext`.

    Ensures only documents matching any of the user's roles and visible
    visibilities are returned. If a department is present on the context,
    it is added as an additional required match.
    """
    if not user_context or not getattr(user_context, "is_verified", False):
        raise PermissionError("Unverified user context")

    must: List[Dict[str, Any]] = [
        match_any("allowed_roles", user_context.roles),
        match_any("visibility", user_context.allowed_visibility),
    ]

    if getattr(user_context, "department", None):
        must.append(match_value("department", user_context.department))

    return build_filters(must=must)


__all__ = [
    "match_any",
    "match_value",
    "build_filters",
    "merge_filters",
    "build_rbac_filters",
]
 
