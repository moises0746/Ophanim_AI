# Security Documentation

Security is an architectural boundary for Ophanim Core. The documents below define the current baseline without implementing authentication, authorization, secret storage, encryption, persistence, or runtime security controls.

- [Security Model](security-model.md) — existing concise security overview.
- [Threat Model](threat-model.md) — assets, STRIDE/AI threats, and control objectives.
- [Trust Boundaries](trust-boundaries.md) — explicit boundary-by-boundary assumptions and failure behavior.
- [Asset Classification](asset-classification.md) — practical data classes and handling direction.
- [Abuse Cases](abuse-cases.md) — threat scenarios and safe expected behavior.
- [Security Test Matrix](security-test-matrix.md) — conceptual future tests mapped to requirements, ADRs, and threats.

Organization-specific classification mapping, retention durations, compliance standards, identity provider, vault, encryption implementation, and deployment controls remain TBD and require explicit authorization.
