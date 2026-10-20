"""Discovery, name resolution and manifest validation, on a throwaway repo layout."""

from pathlib import Path

import pytest

from helpers import TOOL_SRC, make_scenario, make_standalone, write
from wxodemo.config import UsageError, repo_root
from wxodemo.discovery import all_targets, resolve_targets
from wxodemo.manifest import (
    deploy_plan,
    load_scenarios,
    name_clashes,
    teardown_plan,
    validate_scenario,
)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    make_scenario(tmp_path, "alpha")
    make_scenario(tmp_path, "beta", status="soon", tool="other")
    make_standalone(tmp_path, "hello-world", "hello_world", tool="greeting")
    return tmp_path


def test_all_targets_lists_scenarios_then_standalone(repo):
    targets, problems = all_targets(repo)
    assert [(t.kind, t.name) for t in targets] == [
        ("scenario", "alpha"),
        ("scenario", "beta"),
        ("standalone", "hello_world"),
    ]
    assert problems == []
    assert targets[2].agent.tools[0].names == ["greeting"]
    assert targets[2].summary == "some agent"


def test_standalone_without_name_is_reported_not_fatal(repo):
    write(repo / "standalone" / "broken" / "agent.yaml", "description: no name\n")
    _, problems = all_targets(repo)
    assert any("broken" in p for p in problems)


def test_resolve_by_name_and_directory_name(repo):
    targets, _ = all_targets(repo)
    assert resolve_targets(targets, ["alpha"])[0].name == "alpha"
    assert resolve_targets(targets, ["hello-world"])[0].name == "hello_world"


def test_resolve_all_deploy_skips_soon_scenarios(repo):
    targets, _ = all_targets(repo)
    names = [t.name for t in resolve_targets(targets, [], select_all=True, live_only=True)]
    assert names == ["alpha", "hello_world"]
    everything = resolve_targets(targets, [], select_all=True)
    assert [t.name for t in everything] == ["alpha", "beta", "hello_world"]


def test_resolve_kind_filter(repo):
    targets, _ = all_targets(repo)
    chosen = resolve_targets(targets, [], select_all=True, kind="standalone")
    assert [t.name for t in chosen] == ["hello_world"]


def test_resolve_name_matching_both_kinds_needs_kind(repo):
    make_standalone(repo, "alpha", "alpha")
    targets, _ = all_targets(repo)
    with pytest.raises(UsageError, match="--kind"):
        resolve_targets(targets, ["alpha"])
    chosen = resolve_targets(targets, ["alpha"], kind="standalone")
    assert chosen[0].kind == "standalone"


@pytest.mark.parametrize(
    ("names", "select_all"),
    [([], False), (["alpha"], True)],
)
def test_resolve_needs_names_or_all_but_not_both(repo, names, select_all):
    targets, _ = all_targets(repo)
    with pytest.raises(UsageError):
        resolve_targets(targets, names, select_all=select_all)


def test_resolve_unknown_name_lists_known(repo):
    targets, _ = all_targets(repo)
    with pytest.raises(UsageError, match="alpha"):
        resolve_targets(targets, ["nope"])


def test_deploy_plan_order_is_tools_kbs_flows_agents(repo):
    scenarios = load_scenarios(repo)
    steps = deploy_plan(scenarios, [scenarios["alpha"]])
    assert [s.kind for s in steps] == ["tool_py", "kb", "agent"]
    assert steps[-1].name == "agent_alpha"


def test_teardown_plan_removes_agents_first(repo):
    scenarios = load_scenarios(repo)
    steps = teardown_plan([scenarios["alpha"]])
    assert [(s.kind, s.name) for s in steps] == [
        ("agent", "agent_alpha"),
        ("tool", "do_it"),
        ("kb", "kb_alpha"),
    ]


def test_valid_scenario_has_no_problems(repo):
    assert validate_scenario(load_scenarios(repo)["alpha"]) == []


def test_validate_reports_tool_name_mismatch_and_missing_demo(repo):
    write(repo / "tools" / "alpha.py", TOOL_SRC.replace("do_it", "renamed"))
    (repo / "docs" / "demo" / "alpha-demo.md").unlink()
    problems = "\n".join(validate_scenario(load_scenarios(repo)["alpha"]))
    assert "renamed" in problems
    assert "demo.script" in problems


def test_name_clash_across_scenarios_is_detected(repo):
    make_scenario(repo, "gamma", tool="do_it")
    clashes = name_clashes(load_scenarios(repo))
    assert any("do_it" in c for c in clashes)


def test_real_repo_scenarios_validate_clean():
    root = repo_root()
    scenarios = load_scenarios(root)
    assert scenarios, "expected scenarios in the repo"
    for scenario in scenarios.values():
        assert validate_scenario(scenario) == []
    assert name_clashes(scenarios) == []
