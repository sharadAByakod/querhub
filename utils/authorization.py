from typing import Iterable

from fastapi import HTTPException

from constants.actions import Actions
from constants.views import Views
from model.client_model import Client


def _normalize_action(value: str | Actions) -> str:
    if isinstance(value, Actions):
        return value.value.lower()
    return str(value).lower()


def _allowed_actions_for_view(
    permissions: dict[str, Iterable[str | Actions]],
    view: Views,
) -> set[str]:
    valid_keys = {view.value.lower(), view.name.lower()}

    for permission_view, allowed_actions in permissions.items():
        if str(permission_view).lower() in valid_keys:
            return {_normalize_action(action) for action in allowed_actions}

    return set()


def authorize(view: Views, action: Actions, client: Client) -> None:
    permissions = client.permissions or {}
    allowed_actions = _allowed_actions_for_view(permissions, view)
    required_action = _normalize_action(action)

    if not allowed_actions:
        raise HTTPException(403, f"No access to {view.value}")

    if required_action not in allowed_actions:
        raise HTTPException(403, f"{required_action} not allowed on {view.value}")

    return None
