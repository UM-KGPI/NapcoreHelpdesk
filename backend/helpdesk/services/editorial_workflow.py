from __future__ import annotations

from dataclasses import dataclass

from helpdesk.models import EditorialQueueItem, EditorialQueueTransition


@dataclass(frozen=True)
class TransitionRule:
    """Static workflow rule from one status to another under role constraints."""

    to_status: str
    allowed_roles: frozenset[str]


TRANSITION_RULES: dict[tuple[str, str], TransitionRule] = {
    (
        EditorialQueueItem.STATUS_IN_REVIEW,
        EditorialQueueTransition.ACTION_APPROVE,
    ): TransitionRule(
        to_status=EditorialQueueItem.STATUS_APPROVED,
        allowed_roles=frozenset({"reviewer", "admin"}),
    ),
    (
        EditorialQueueItem.STATUS_IN_REVIEW,
        EditorialQueueTransition.ACTION_REJECT,
    ): TransitionRule(
        to_status=EditorialQueueItem.STATUS_REJECTED,
        allowed_roles=frozenset({"reviewer", "admin"}),
    ),
    (
        EditorialQueueItem.STATUS_REJECTED,
        EditorialQueueTransition.ACTION_REOPEN,
    ): TransitionRule(
        to_status=EditorialQueueItem.STATUS_IN_REVIEW,
        allowed_roles=frozenset({"editor", "reviewer", "admin"}),
    ),
    (
        EditorialQueueItem.STATUS_APPROVED,
        EditorialQueueTransition.ACTION_REVOKE,
    ): TransitionRule(
        to_status=EditorialQueueItem.STATUS_REVOKED,
        allowed_roles=frozenset({"reviewer", "admin"}),
    ),
}


class WorkflowTransitionNotAllowed(ValueError):
    """Raised when an action is invalid for the queue item's current status."""


class WorkflowTransitionForbidden(PermissionError):
    """Raised when actor roles do not satisfy a valid transition rule."""


def allowed_actions_for_status(*, status: str, actor_roles: set[str]) -> list[str]:
    """Return transition actions permitted for the given status and caller roles."""

    if not actor_roles:
        return []

    actions: list[str] = []
    for (from_status, action), rule in TRANSITION_RULES.items():
        if from_status != status:
            continue
        if actor_roles.isdisjoint(rule.allowed_roles):
            continue
        actions.append(action)
    return sorted(actions)


def apply_transition(
    *,
    queue_item: EditorialQueueItem,
    action: str,
    actor_id: str,
    actor_roles: set[str],
    comment: str = "",
) -> EditorialQueueTransition:
    """Apply a validated transition and persist a corresponding audit entry."""

    key = (queue_item.status, action)
    rule = TRANSITION_RULES.get(key)
    if rule is None:
        raise WorkflowTransitionNotAllowed(
            f"Action '{action}' is not allowed from status '{queue_item.status}'."
        )

    if actor_roles.isdisjoint(rule.allowed_roles):
        raise WorkflowTransitionForbidden(
            f"Action '{action}' requires one of roles: {sorted(rule.allowed_roles)}"
        )

    from_status = queue_item.status
    queue_item.status = rule.to_status
    queue_item.save(update_fields=["status", "updated_at"])

    return EditorialQueueTransition.objects.create(
        queue_item=queue_item,
        action=action,
        from_status=from_status,
        to_status=rule.to_status,
        actor_id=actor_id,
        actor_roles=sorted(actor_roles),
        comment=comment,
    )
