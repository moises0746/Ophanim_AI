"""Compatibility smoke tests for unchanged runtime modules."""


def test_existing_runtime_modules_import() -> None:
    import ophanim
    from ophanim import main
    from ophanim.adapters import anythingllm, lmstudio
    from ophanim.browser import agent, models, policy

    assert ophanim is not None
    assert main.app.title == "Ophanim Core"
    assert anythingllm is not None
    assert lmstudio is not None
    assert agent is not None
    assert models is not None
    assert policy is not None
