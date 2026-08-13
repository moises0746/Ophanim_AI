"""Bounded agent role and capability model for the autonomous workflow.

Agents are capability profiles, not autonomous principals with unrestricted
access. Each role grants the minimum permission set required by the workflow.
Roles such as Security, DevOps, Documentation, Architect, and Product Manager
can be added later by extending ``AgentRole`` and ``ROLE_PERMISSIONS`` without
changing the Orchestrator or provider contracts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .errors import DomainValidationError
from .values import _text


class AgentRole(StrEnum):
    ORCHESTRATOR = "orchestrator"
    PLANNER = "planner"
    DEVELOPER = "developer"
    QA = "qa"
    REVIEWER = "reviewer"


class AgentPermission(StrEnum):
    """Named permissions enforced at the workflow boundary."""

    READ_REPOSITORY = "read_repository"
    GENERATE_PLANNING_ARTIFACTS = "generate_planning_artifacts"
    WRITE_SOURCE_CODE = "write_source_code"
    RUN_DEVELOPMENT_COMMANDS = "run_development_commands"
    COMMIT_TO_TASK_BRANCH = "commit_to_task_branch"
    RUN_APPROVED_TESTS = "run_approved_tests"
    READ_DIFF = "read_diff"
    MANAGE_WORKFLOW = "manage_workflow"
    ASSIGN_AGENTS = "assign_agents"
    MANAGE_STATE = "manage_state"


ROLE_PERMISSIONS: dict[AgentRole, frozenset[AgentPermission]] = {
    AgentRole.ORCHESTRATOR: frozenset(
        {
            AgentPermission.MANAGE_WORKFLOW,
            AgentPermission.ASSIGN_AGENTS,
            AgentPermission.MANAGE_STATE,
            AgentPermission.READ_REPOSITORY,
        }
    ),
    AgentRole.PLANNER: frozenset(
        {
            AgentPermission.READ_REPOSITORY,
            AgentPermission.GENERATE_PLANNING_ARTIFACTS,
        }
    ),
    AgentRole.DEVELOPER: frozenset(
        {
            AgentPermission.READ_REPOSITORY,
            AgentPermission.WRITE_SOURCE_CODE,
            AgentPermission.RUN_DEVELOPMENT_COMMANDS,
            AgentPermission.COMMIT_TO_TASK_BRANCH,
        }
    ),
    AgentRole.QA: frozenset(
        {
            AgentPermission.READ_REPOSITORY,
            AgentPermission.RUN_APPROVED_TESTS,
        }
    ),
    AgentRole.REVIEWER: frozenset(
        {
            AgentPermission.READ_REPOSITORY,
            AgentPermission.READ_DIFF,
        }
    ),
}


def has_permission(role: AgentRole, permission: AgentPermission) -> bool:
    """Return whether a role may exercise the given permission.

    Deny-by-default: unknown roles and permissions yield ``False``.
    """
    return permission in ROLE_PERMISSIONS.get(role, frozenset())


def verify_permission(role: AgentRole, permission: AgentPermission) -> None:
    """Raise ``DomainValidationError`` when the role lacks the permission."""
    if not has_permission(role, permission):
        raise DomainValidationError(f"role {role.value} is not permitted to {permission.value}")


@dataclass(frozen=True, slots=True)
class AgentProfile:
    """Versioned bounded capability profile for one agent role."""

    role: AgentRole
    name: str
    description: str = ""
    permissions: frozenset[AgentPermission] = field(default_factory=frozenset)
    version: str = "1"

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "name", max_length=128))
        description = self.description.strip()
        if description and len(description) > 4000:
            raise DomainValidationError("description exceeds 4000 characters")
        object.__setattr__(self, "description", description)
        permissions = frozenset(self.permissions)
        for permission in permissions:
            if not isinstance(permission, AgentPermission):
                raise DomainValidationError("permissions must be AgentPermission values")
        object.__setattr__(self, "permissions", permissions)
        object.__setattr__(self, "version", _text(self.version, "version", max_length=64))
        if self.role is AgentRole.ORCHESTRATOR:
            raise DomainValidationError("orchestrator is not a delegable agent role")


def default_profile(role: AgentRole) -> AgentProfile:
    """Return the canonical least-privilege profile for a delegable role."""
    if role is AgentRole.ORCHESTRATOR:
        raise DomainValidationError("orchestrator is not a delegable agent role")
    return AgentProfile(
        role=role,
        name=f"{role.value.title()} Agent",
        description=f"Bounded {role.value} agent profile for the autonomous workflow.",
        permissions=ROLE_PERMISSIONS[role],
    )
