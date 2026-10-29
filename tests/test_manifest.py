"""Manifest validation branches and plan building that the happy-path tests do not reach."""

import json
from pathlib import Path

import pytest

from helpers import make_scenario, write
from wxodemo import manifest
from wxodemo.manifest import ManifestError, load_scenarios, validate_scenario


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    make_scenario(tmp_path, "alpha")
    return tmp_path


def problems(repo: Path) -> list[str]:
    return validate_scenario(load_scenarios(repo)["alpha"])


def edit_manifest(repo: Path, old: str, new: str) -> None:
    path = repo / "scenarios/alpha/scenario.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8")


def test_clean_scenario_has_no_problems(repo):
    assert problems(repo) == []


@pytest.mark.parametrize("field", ["name", "description"])
def test_required_fields(repo, field):
    edit_manifest(repo, f"{field}: ", f"x_{field}: ")
    assert any(f"missing required field '{field}'" in p for p in problems(repo))


def test_id_must_match_folder_and_status_must_be_known(repo):
    edit_manifest(repo, "id: alpha", "id: other")
    edit_manifest(repo, "status: live", "status: maybe")
    found = problems(repo)
    assert any("must equal the folder name" in p for p in found)
    assert any("status must be one of" in p for p in found)


def test_evaluation_tier_and_missing_ground_truth(repo):
    edit_manifest(repo, "tier: core", "tier: huge")
    (repo / "evaluation/alpha/ground_truth.json").unlink()
    found = problems(repo)
    assert any("evaluation.tier" in p for p in found)
    assert any("ground_truth.json not found" in p for p in found)


def test_full_evaluation_tier_needs_config_and_test_cases(repo):
    edit_manifest(repo, "tier: core", "tier: full")
    found = problems(repo)
    assert any("eval_config.yaml not found" in p for p in found)
    assert any("test_cases/*.json not found" in p for p in found)

    write(repo / "evaluation/alpha/eval_config.yaml", "test_paths: []\n")
    found = problems(repo)
    assert not any("eval_config.yaml" in p for p in found)
    assert any("test_cases/*.json not found" in p for p in found)

    write(repo / "evaluation/alpha/test_cases/tc_01.json", "{}")
    assert not any("evaluation" in p or "test_cases" in p for p in problems(repo))


def test_live_scenario_needs_an_evaluation_section(repo):
    edit_manifest(repo, "evaluation:\n  path: evaluation/alpha\n  tier: core\n", "")
    assert any("evaluation section missing" in p for p in problems(repo))


def test_soon_scenario_may_skip_evaluation(repo):
    edit_manifest(repo, "evaluation:\n  path: evaluation/alpha\n  tier: core\n", "")
    edit_manifest(repo, "status: live", "status: soon")
    assert not any("evaluation" in p for p in problems(repo))


def test_smoke_agent_must_be_a_scenario_agent(repo):
    edit_manifest(repo, "agents:\n", "smoke_agent: agent_alpha\nagents:\n")
    assert problems(repo) == []
    edit_manifest(repo, "smoke_agent: agent_alpha", "smoke_agent: nope")
    assert any("smoke_agent 'nope'" in p for p in problems(repo))


def test_live_scenario_needs_valid_smoke_prompts(repo):
    write(repo / "evaluation/alpha/ground_truth.json", "{bad json")
    assert any("not valid JSON" in p for p in problems(repo))
    write(repo / "evaluation/alpha/ground_truth.json", json.dumps({"smoke_prompts": [{"id": "x"}]}))
    assert any("non-empty 'smoke_prompts'" in p for p in problems(repo))
    write(repo / "evaluation/alpha/ground_truth.json", json.dumps({}))
    assert any("non-empty 'smoke_prompts'" in p for p in problems(repo))


def test_live_scenario_needs_demo_script_and_slides(repo):
    (repo / "docs/demo/alpha-demo.md").unlink()
    (repo / "docs/demo/scenarios/alpha.js").unlink()
    found = problems(repo)
    assert any("demo.script" in p for p in found)
    assert any("alpha.js" in p for p in found)


def test_tool_functions_must_match_manifest_names(repo):
    write(repo / "tools/alpha.py", "from x import tool\n\n@tool\ndef renamed():\n    pass\n")
    assert any("@tool functions" in p and "renamed" in p for p in problems(repo))


def test_tool_with_arguments_is_still_recognised(repo):
    write(
        repo / "tools/alpha.py",
        "from x import tool\n\n@tool(permission='read')\ndef do_it():\n    pass\n",
    )
    assert problems(repo) == []


def test_attached_must_be_subset_of_names(repo):
    edit_manifest(repo, "attached: [do_it]", "attached: [do_it, ghost]")
    assert any("not subset" in p and "ghost" in p for p in problems(repo))


def test_missing_tool_file_and_unsupported_type(repo):
    (repo / "tools/alpha.py").unlink()
    assert any("not found" in p for p in problems(repo))
    write(repo / "tools/alpha.py", "x")
    edit_manifest(repo, "path: tools/alpha.py", "path: tools/alpha.py")
    write(repo / "tools/odd.txt", "x")
    edit_manifest(repo, "tools/alpha.py", "tools/odd.txt")
    assert any("unsupported file type" in p for p in problems(repo))


def test_agent_yaml_checks(repo):
    write(repo / "agents/alpha/agent.yaml", "name: wrong\ntools: [do_it, stranger]\n")
    found = problems(repo)
    assert any("!= manifest" in p for p in found)
    assert any("does not own" in p and "stranger" in p for p in found)


def test_agent_must_list_attached_tools_and_known_kbs(repo):
    write(repo / "agents/alpha/agent.yaml", "name: agent_alpha\ntools: []\nknowledge_base: [zzz]\n")
    found = problems(repo)
    assert any("does not list attached tools" in p for p in found)
    assert any("knowledge bases this scenario does not own" in p for p in found)


def test_agent_must_not_use_unattached_tools(repo):
    edit_manifest(repo, "attached: [do_it]", "attached: []")
    assert any("not attached" in p for p in problems(repo))


def test_knowledge_base_folder_and_name(repo):
    write(repo / "knowledge/alpha/kb.yaml", "name: something_else\n")
    assert any("no *.yaml with that name" in p for p in problems(repo))
    (repo / "knowledge/alpha/kb.yaml").unlink()
    (repo / "knowledge/alpha").rmdir()
    assert any("folder knowledge/alpha not found" in p for p in problems(repo))


def test_flow_resolution(tmp_path):
    flow_dir = tmp_path / "flows" / "f"
    write(flow_dir / "a.py", "name='x'")
    write(flow_dir / "b.py", "name='y'")
    with pytest.raises(ManifestError, match="has 2 .py files"):
        manifest.flow_file(tmp_path, {"name": "x", "path": "flows/f"})
    assert (
        manifest.flow_file(tmp_path, {"name": "x", "path": "flows/f", "file": "b.py"}).name
        == "b.py"
    )
    with pytest.raises(ManifestError, match="not found"):
        manifest.flow_file(tmp_path, {"name": "x", "path": "flows/f", "file": "zz.py"})
    with pytest.raises(ManifestError, match="folder flows/none not found"):
        manifest.flow_file(tmp_path, {"name": "x", "path": "flows/none"})


def test_flow_name_must_appear_in_source(tmp_path, repo):
    write(repo / "flows/f/only.py", "name = 'different'\n")
    edit_manifest(repo, "flows: []", "flows:\n  - name: wanted\n    path: flows/f\n")
    assert any("flow name 'wanted' not found" in p for p in problems(repo))


def test_tool_package_requires_entry_and_requirements(tmp_path):
    pkg = tmp_path / "tools" / "pkg"
    write(pkg / "main.py", "x")
    with pytest.raises(ManifestError, match="'entry' is required"):
        manifest.tool_step(tmp_path, {"path": "tools/pkg"})
    with pytest.raises(ManifestError, match="entry nope.py not found"):
        manifest.tool_step(tmp_path, {"path": "tools/pkg", "entry": "nope.py"})
    with pytest.raises(ManifestError, match="requirements.txt not found"):
        manifest.tool_step(tmp_path, {"path": "tools/pkg", "entry": "main.py"})
    write(pkg / "requirements.txt", "")
    step = manifest.tool_step(tmp_path, {"path": "tools/pkg", "entry": "main.py"})
    assert step.kind == "tool_pkg" and step.requirements.name == "requirements.txt"


def test_tool_openapi_and_missing_path(tmp_path):
    write(tmp_path / "tools" / "api.yaml", "openapi: 3.0.0")
    assert manifest.tool_step(tmp_path, {"path": "tools/api.yaml"}).kind == "tool_openapi"
    with pytest.raises(ManifestError, match="not found"):
        manifest.tool_step(tmp_path, {"path": "tools/missing"})


def test_deploy_plan_refuses_name_clashes(tmp_path):
    make_scenario(tmp_path, "alpha")
    make_scenario(tmp_path, "beta", tool="other")
    scenarios = load_scenarios(tmp_path)
    assert manifest.name_clashes(scenarios) == []
    path = tmp_path / "scenarios/beta/scenario.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("agent_beta", "agent_alpha"), "utf-8")
    scenarios = load_scenarios(tmp_path)
    assert any("agent name 'agent_alpha'" in c for c in manifest.name_clashes(scenarios))
    with pytest.raises(ManifestError, match="name clash"):
        manifest.deploy_plan(scenarios, [scenarios["alpha"]])


def test_invalid_yaml_and_non_mapping_manifest(tmp_path):
    write(tmp_path / "scenarios/bad/scenario.yaml", "a: [unclosed\n")
    with pytest.raises(ManifestError, match="invalid YAML"):
        load_scenarios(tmp_path)
    write(tmp_path / "scenarios/bad/scenario.yaml", "- just\n- a list\n")
    with pytest.raises(ManifestError, match="not a YAML mapping"):
        load_scenarios(tmp_path)


def test_folders_without_a_manifest_are_ignored(tmp_path):
    (tmp_path / "scenarios" / "empty").mkdir(parents=True)
    write(tmp_path / "scenarios" / "README.md", "x")
    assert load_scenarios(tmp_path) == {}
    assert load_scenarios(tmp_path / "nowhere") == {}
