"""Authenticated, policy-governed Skill API routes (R1-15, ADR-018)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from ophanim.config import get_settings
from ophanim.domain.errors import DomainValidationError
from ophanim.domain.identifiers import CorrelationId, SkillRunId
from ophanim.domain.identity import IdentityPrincipal
from ophanim.domain.policy import PolicyDecision
from ophanim.domain.skills import (
    SkillExecutorContext,
    SkillReferenceType,
    SkillResult,
    SkillRunRequest,
    SkillRunStatus,
)
from ophanim.domain.values import Environment
from ophanim.ports.identity import IdentityAuthenticationPort
from ophanim.ports.skills import SkillRegistryPort
from ophanim.runtime import _environment

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


def get_skill_registry() -> SkillRegistryPort:
    raise RuntimeError("Skill registry is not configured")


def get_skills_identity() -> IdentityAuthenticationPort:
    raise RuntimeError("Skills identity is not configured")


def get_skill_environment() -> Environment:
    return _environment(get_settings().environment)


SkillRegistryDep = Annotated[SkillRegistryPort, Depends(get_skill_registry)]
SkillsIdentityDep = Annotated[IdentityAuthenticationPort, Depends(get_skills_identity)]
SkillEnvironmentDep = Annotated[Environment, Depends(get_skill_environment)]


def _principal(
    identity: IdentityAuthenticationPort,
    authorization: str | None,
) -> IdentityPrincipal:
    scheme, _, bearer_token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not bearer_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="bearer authorization required",
        )
    principal = identity.authenticate_token(bearer_token)
    if principal is None:
        raise HTTPException(status_code=403, detail="skills access denied")
    return principal


class SkillManifestResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_id: str
    name: str
    version: str
    description: str
    read_only: bool
    input_label: str
    input_hint: str
    input_pattern: str
    sources: list[str]
    capabilities: list[str]
    outputs: list[str]


class SkillRunRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_number: str = Field(min_length=3, max_length=64)
    reference_type: str = Field(default=SkillReferenceType.TRANSACTION.value, max_length=32)


class SkillRunStepResponse(BaseModel):
    step: str
    source: str
    status: str
    detail: str
    evidence_refs: list[str]
    duration_ms: float


class FindingResponse(BaseModel):
    finding_id: str
    severity: str
    title: str
    detail: str
    source: str
    evidence_refs: list[str]


class PolicyDecisionResponse(BaseModel):
    effect: str
    reason: str
    rule_id: str | None = None


class SkillRunResponse(BaseModel):
    run_id: str
    skill_id: str
    workspace_id: str
    reference_number: str
    status: str
    classification: str | None = None
    recommendation: str | None = None
    limitation: str | None = None
    denied_reason: str | None = None
    failed_reason: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    steps: list[SkillRunStepResponse]
    findings: list[FindingResponse]
    decision: PolicyDecisionResponse | None = None


def _manifest_response(manifest) -> SkillManifestResponse:
    return SkillManifestResponse(
        skill_id=manifest.definition.skill_id,
        name=manifest.definition.name,
        version=manifest.definition.version,
        description=manifest.definition.description,
        read_only=manifest.read_only,
        input_label=manifest.input_label,
        input_hint=manifest.input_hint,
        input_pattern=manifest.input_pattern,
        sources=list(manifest.sources),
        capabilities=list(manifest.capabilities),
        outputs=list(manifest.outputs),
    )


def _step_response(step) -> SkillRunStepResponse:
    return SkillRunStepResponse(
        step=step.step,
        source=step.source,
        status=step.status.value,
        detail=step.detail,
        evidence_refs=[str(ref) for ref in step.evidence_refs],
        duration_ms=round(step.duration_ms, 3),
    )


def _finding_response(finding) -> FindingResponse:
    return FindingResponse(
        finding_id=finding.finding_id,
        severity=finding.severity.value,
        title=finding.title,
        detail=finding.detail,
        source=finding.source,
        evidence_refs=[str(ref) for ref in finding.evidence_refs],
    )


def _decision_response(decision: PolicyDecision | None) -> PolicyDecisionResponse | None:
    if decision is None:
        return None
    return PolicyDecisionResponse(
        effect=decision.effect.value,
        reason=decision.reason,
        rule_id=decision.rule_id,
    )


def _run_response(result: SkillResult) -> SkillRunResponse:
    run = result.run
    return SkillRunResponse(
        run_id=str(run.run_id),
        skill_id=run.skill_id,
        workspace_id=run.workspace_id,
        reference_number=run.reference_number,
        status=run.status.value,
        classification=run.classification.value if run.classification else None,
        recommendation=run.recommendation,
        limitation=run.limitation,
        denied_reason=run.denied_reason,
        failed_reason=run.failed_reason,
        started_at=run.started_at,
        completed_at=run.completed_at,
        steps=[_step_response(step) for step in run.steps],
        findings=[_finding_response(finding) for finding in run.findings],
        decision=_decision_response(result.decision),
    )


@router.get("", response_model=list[SkillManifestResponse])
async def list_skills(
    registry: SkillRegistryDep,
    identity: SkillsIdentityDep,
    authorization: Annotated[str | None, Header()] = None,
) -> list[SkillManifestResponse]:
    _principal(identity, authorization)
    return [_manifest_response(manifest) for manifest in registry.list_skills()]


@router.post("/{skill_id}/runs", response_model=SkillRunResponse)
async def create_run(
    skill_id: str,
    body: SkillRunRequestModel,
    registry: SkillRegistryDep,
    identity: SkillsIdentityDep,
    environment: SkillEnvironmentDep,
    authorization: Annotated[str | None, Header()] = None,
) -> SkillRunResponse:
    principal = _principal(identity, authorization)
    try:
        reference_type = SkillReferenceType(body.reference_type)
        request = SkillRunRequest(
            reference_number=body.reference_number, reference_type=reference_type
        )
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    context = SkillExecutorContext(correlation_id=CorrelationId.new(), environment=environment)
    try:
        result = await registry.execute(
            skill_id=skill_id, principal=principal, request=request, context=context
        )
    except DomainValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if result.run.status is SkillRunStatus.DENIED:
        raise HTTPException(status_code=403, detail=result.run.denied_reason or "skill run denied")
    return _run_response(result)


@router.get("/{skill_id}/runs", response_model=list[SkillRunResponse])
async def list_runs(
    skill_id: str,
    registry: SkillRegistryDep,
    identity: SkillsIdentityDep,
    authorization: Annotated[str | None, Header()] = None,
) -> list[SkillRunResponse]:
    principal = _principal(identity, authorization)
    if registry.get_manifest(skill_id) is None:
        raise HTTPException(status_code=404, detail=f"unknown skill '{skill_id}'")
    results = registry.list_runs(skill_id=skill_id, workspace_id=str(principal.workspace_id))
    return [_run_response(result) for result in results]


@router.get("/{skill_id}/runs/{run_id}", response_model=SkillRunResponse)
async def get_run(
    skill_id: str,
    run_id: str,
    registry: SkillRegistryDep,
    identity: SkillsIdentityDep,
    authorization: Annotated[str | None, Header()] = None,
) -> SkillRunResponse:
    principal = _principal(identity, authorization)
    try:
        parsed_run_id = SkillRunId.from_str(run_id)
    except (ValueError, DomainValidationError) as exc:
        raise HTTPException(status_code=404, detail="run not found") from exc
    result = registry.get_run(parsed_run_id)
    if (
        result is None
        or result.run.skill_id != skill_id
        or result.run.workspace_id != str(principal.workspace_id)
    ):
        raise HTTPException(status_code=404, detail="run not found")
    return _run_response(result)
