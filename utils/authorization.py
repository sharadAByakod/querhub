from fastapi import HTTPException

from constants.actions import Actions
from constants.views import Views
from model.client_model import Client


def authorize(view: Views, action: Actions, client: Client) -> None:
    permissions = client.permissions
    allowed_actions = permissions.get(view.name)

    if not allowed_actions:
        raise HTTPException(403, f"No access to {view.name}")

    if action.value not in allowed_actions:
        raise HTTPException(403, f"{action.value} not allowed on {view.name}")

    return None
