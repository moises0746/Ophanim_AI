"""Local runtime composition for authenticated Desktop chat and events."""

from __future__ import annotations

from dataclasses import dataclass

from ophanim.adapters.cloud_model_providers import build_configured_cloud_providers
from ophanim.adapters.default_deny_policy import DefaultDenyPolicyEngine
from ophanim.adapters.environment_secrets import EnvironmentSecretResolver
from ophanim.adapters.event_broadcaster import IdentityEventStreamAuthorizer
from ophanim.adapters.knowledge import InMemoryKnowledgeAdapter
from ophanim.adapters.lmstudio import build_configured_lmstudio_provider
from ophanim.adapters.model_router import ModelRouter
from ophanim.adapters.portal import (
    InMemoryReferencePortalAdapter,
    seed_transaction_investigation_knowledge,
)
from ophanim.adapters.runtime_identity import EnvironmentRuntimeIdentity
from ophanim.application.assistant_chat import AssistantChatService
from ophanim.config import Settings
from ophanim.diagnostics.db_query import DatabaseQueryTool
from ophanim.diagnostics.log_search import LogSearchTool
from ophanim.diagnostics.service import DiagnosticsService, diagnostics_policy_rules
from ophanim.domain.identifiers import WorkspaceId
from ophanim.domain.values import Environment
from ophanim.ports.event_broadcaster import EventBroadcasterPort, EventStreamAuthorizerPort
from ophanim.ports.identity import IdentityAuthenticationPort
from ophanim.ports.knowledge import KnowledgeRepositoryPort
from ophanim.ports.model_router import ModelProviderPort
from ophanim.ports.skills import SkillRegistryPort
from ophanim.skills.registry import SkillRegistry
from ophanim.skills.transaction_investigation import (
    TransactionInvestigationSkill,
    skills_policy_rules,
)


@dataclass(frozen=True, slots=True)
class RuntimeComposition:
    identity: IdentityAuthenticationPort
    event_authorizer: EventStreamAuthorizerPort
    chat_service: AssistantChatService
    providers: tuple[ModelProviderPort, ...]
    knowledge_repo: KnowledgeRepositoryPort
    diagnostics_service: DiagnosticsService
    skill_registry: SkillRegistryPort


def _environment(value: str) -> Environment:
    normalized = value.strip().lower()
    if normalized in {"development", "dev", "local"}:
        return Environment.LOCAL
    try:
        return Environment(normalized)
    except ValueError:
        return Environment.LOCAL


def build_runtime(
    settings: Settings, event_broadcaster: EventBroadcasterPort
) -> RuntimeComposition:
    secret_resolver = EnvironmentSecretResolver(
        {
            settings.desktop_api_token_ref,
            settings.lmstudio_api_key_ref,
            settings.openai_api_key_ref,
            settings.gemini_api_key_ref,
            settings.anthropic_api_key_ref,
        }
    )
    identity = EnvironmentRuntimeIdentity(
        tenant_id=settings.runtime_tenant_id,
        workspace_id=settings.runtime_workspace_id,
        token_ref=settings.desktop_api_token_ref,
        secret_resolver=secret_resolver,
    )
    providers: list[ModelProviderPort] = []
    local_provider = build_configured_lmstudio_provider(settings, secret_resolver)
    if local_provider is not None:
        providers.append(local_provider)
    providers.extend(build_configured_cloud_providers(settings, secret_resolver))
    knowledge_repo = InMemoryKnowledgeAdapter()
    environment = _environment(settings.environment)
    policy_engine = DefaultDenyPolicyEngine(
        (*diagnostics_policy_rules(environment), *skills_policy_rules(environment))
    )
    diagnostics_service = DiagnosticsService(
        db_tool=DatabaseQueryTool(
            dsn=settings.diagnostics_db_dsn,
            max_rows=settings.diagnostics_max_rows,
            max_cell_chars=settings.diagnostics_max_cell_chars,
        ),
        log_tool=LogSearchTool(
            log_path=settings.diagnostics_log_path,
            max_records=settings.diagnostics_max_records,
        ),
        policy_engine=policy_engine,
        environment=environment,
    )
    workspace_id = WorkspaceId.from_str(settings.runtime_workspace_id)
    seed_transaction_investigation_knowledge(knowledge_repo, workspace_id)
    skill_registry = SkillRegistry()
    skill_registry.register(
        TransactionInvestigationSkill(
            portal=InMemoryReferencePortalAdapter(),
            db_tool=DatabaseQueryTool(
                dsn=settings.diagnostics_db_dsn,
                max_rows=settings.diagnostics_max_rows,
                max_cell_chars=settings.diagnostics_max_cell_chars,
            ),
            log_tool=LogSearchTool(
                log_path=settings.diagnostics_log_path,
                max_records=settings.diagnostics_max_records,
            ),
            knowledge_repo=knowledge_repo,
            policy_engine=policy_engine,
            event_broadcaster=event_broadcaster,
        )
    )
    chat_service = AssistantChatService(
        model_router=ModelRouter(providers),
        event_broadcaster=event_broadcaster,
        knowledge_repo=knowledge_repo,
        environment=environment,
    )
    return RuntimeComposition(
        identity=identity,
        event_authorizer=IdentityEventStreamAuthorizer(identity),
        chat_service=chat_service,
        providers=tuple(providers),
        knowledge_repo=knowledge_repo,
        diagnostics_service=diagnostics_service,
        skill_registry=skill_registry,
    )
