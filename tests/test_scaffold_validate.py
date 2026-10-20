"""new-scenario scaffolding and the demo-consistency checks, against a throwaway repo."""

from pathlib import Path

import pytest

from helpers import make_scenario, write
from wxodemo import scaffold, validate
from wxodemo.config import UsageError
from wxodemo.logging_setup import setup_logging
from wxodemo.manifest import load_scenarios

TAGS = (
    '<html>\r\n  <script src="scenarios/alpha.js"></script>\r\n'
    '  <script src="scenarios/beta.js"></script>\r\n</html>\r\n'
)
TEMPLATE = "# {{NAME}} ({{ID}}) agent {{AGENT_NAME}}\n"


@pytest.fixture
def repo(tmp_path: Path, capsys) -> Path:
    setup_logging(tmp_path / "local" / "t.log")
    make_scenario(tmp_path, "alpha")
    write(tmp_path / scaffold.TEMPLATE, TEMPLATE)
    (tmp_path / "docs" / "demo").mkdir(parents=True, exist_ok=True)
    (tmp_path / scaffold.PRESENTATION).write_bytes(TAGS.encode())
    return tmp_path


# ---------------------------------------------------------------------------
# new-scenario
# ---------------------------------------------------------------------------


def test_scaffold_creates_files_and_script_tag(repo: Path):
    assert scaffold.run_new_scenario(repo, "gamma-one", "Gamma One", "A thing", None, False) == 0
    assert (repo / "scenarios/gamma-one/scenario.yaml").is_file()
    assert (repo / "agents/gamma-one/agent.yaml").is_file()
    assert (repo / "evaluation/gamma-one/ground_truth.json").is_file()
    assert (repo / "docs/demo/scenarios/gamma-one.js").is_file()
    assert (
        repo / "docs/demo/gamma-one-demo.md"
    ).read_text() == "# Gamma One (gamma-one) agent gamma_one\n"

    raw = (repo / scaffold.PRESENTATION).read_bytes().decode()
    assert '<script src="scenarios/gamma-one.js"></script>' in raw
    assert raw.count("\r\n") == raw.count("\n"), "CRLF line endings must be preserved"
    assert raw.index("beta.js") < raw.index("gamma-one.js")
    # the new slide knows its sidebar position (third script tag)
    assert "Scenario 3" in (repo / "docs/demo/scenarios/gamma-one.js").read_text(encoding="utf-8")


def test_scaffold_manifest_is_valid_yaml_with_soon_status(repo: Path):
    scaffold.run_new_scenario(repo, "gamma-one", "Gamma One", "A thing", None, False)
    created = load_scenarios(repo)["gamma-one"]
    assert created.get("status") == "soon"
    assert created.get("agents")[0]["name"] == "gamma_one"


def test_scaffold_dry_run_writes_nothing(repo: Path):
    before = (repo / scaffold.PRESENTATION).read_bytes()
    assert scaffold.run_new_scenario(repo, "gamma-one", "Gamma One", "A thing", None, True) == 0
    assert not (repo / "scenarios/gamma-one").exists()
    assert (repo / scaffold.PRESENTATION).read_bytes() == before


def test_scaffold_is_idempotent_refusing_to_overwrite(repo: Path):
    scaffold.run_new_scenario(repo, "gamma-one", "Gamma One", "A thing", None, False)
    with pytest.raises(UsageError, match="already exists"):
        scaffold.run_new_scenario(repo, "gamma-one", "Gamma One", "A thing", None, False)


@pytest.mark.parametrize("bad", ["Gamma", "gamma_one", "1gamma", "gamma--one", "hello-world"])
def test_scaffold_rejects_bad_ids(repo: Path, bad: str):
    with pytest.raises(UsageError):
        scaffold.run_new_scenario(repo, bad, "N", "D", None, True)


def test_scaffold_rejects_agent_name_in_use(repo: Path):
    with pytest.raises(UsageError, match="already used by scenario 'alpha'"):
        scaffold.run_new_scenario(repo, "gamma-one", "G", "D", "agent_alpha", True)


def test_scaffold_rejects_bad_agent_name(repo: Path):
    with pytest.raises(UsageError, match="snake_case"):
        scaffold.run_new_scenario(repo, "gamma-one", "G", "D", "Bad-Name", True)


def test_scaffold_needs_template(repo: Path):
    (repo / scaffold.TEMPLATE).unlink()
    with pytest.raises(UsageError, match="template not found"):
        scaffold.run_new_scenario(repo, "gamma-one", "G", "D", None, True)


def test_scaffold_keeps_existing_js_and_tag(repo: Path):
    write(repo / "docs/demo/scenarios/beta.js", "// mine")
    scaffold.run_new_scenario(repo, "beta", "Beta", "D", None, False)
    assert (repo / "docs/demo/scenarios/beta.js").read_text() == "// mine"
    assert (repo / scaffold.PRESENTATION).read_bytes().decode().count("scenarios/beta.js") == 1


def test_scaffold_js_escapes_quotes(repo: Path):
    scaffold.run_new_scenario(repo, "gamma-one", 'The "Big" One', 'Say "hi"', None, False)
    js = (repo / "docs/demo/scenarios/gamma-one.js").read_text(encoding="utf-8")
    assert 'The \\"Big\\" One' in js


# ---------------------------------------------------------------------------
# demo consistency
# ---------------------------------------------------------------------------

MD_OK = "x\n**Prompt (type exactly):**\n```\nWhat is up?\n```\n"
JS_OK = (
    'status: "live", tag: "Scenario 1 \u2022 A"\n'
    '<div class="prompt-box" id="prompt-1">What is up?</div>\n'
    "<button onclick=\"copyPrompt('prompt-1')\">c</button>\n"
    '<span class="tool-chip">do_it</span>'
)


def demo(repo: Path, md: str | None, js: str | None):
    if md is not None:
        write(repo / "docs/demo/alpha-demo.md", md)
    if js is not None:
        write(repo / "docs/demo/scenarios/alpha.js", js)
    scenario = load_scenarios(repo)["alpha"]
    return validate.check_demo(repo, scenario, validate.script_order(repo))


def test_demo_consistent_passes(repo: Path):
    assert demo(repo, MD_OK, JS_OK).problems == []


def test_demo_prompt_mismatch(repo: Path):
    report = demo(repo, MD_OK.replace("What is up?", "Other?"), JS_OK)
    assert any("prompt 1 differs" in p for p in report.problems)


def test_demo_prompt_count_mismatch(repo: Path):
    report = demo(repo, MD_OK + MD_OK, JS_OK)
    assert any("prompt count differs" in p for p in report.problems)


def test_demo_html_entities_are_unescaped(repo: Path):
    js = JS_OK.replace("What is up?", "A &amp; B")
    report = demo(repo, MD_OK.replace("What is up?", "A & B"), js)
    assert report.problems == []


def test_demo_wrong_scenario_number(repo: Path):
    report = demo(repo, MD_OK, JS_OK.replace("Scenario 1", "Scenario 5"))
    assert any("Scenario 5 but sidebar position is 1" in p for p in report.problems)


def test_demo_unregistered_scenario(repo: Path):
    (repo / scaffold.PRESENTATION).write_bytes(b"<html></html>")
    assert any("no <script" in p for p in demo(repo, MD_OK, JS_OK).problems)


def test_demo_template_leftovers(repo: Path):
    report = demo(repo, MD_OK + "{{X}}\nAUTHOR NOTE\n", JS_OK)
    assert any("PLACEHOLDER" in p for p in report.problems)
    assert any("AUTHOR NOTE" in p for p in report.problems)


def test_demo_copy_prompt_ids_must_match(repo: Path):
    report = demo(repo, MD_OK, JS_OK.replace("copyPrompt('prompt-1')", "copyPrompt('prompt-9')"))
    assert any("copyPrompt ids" in p for p in report.problems)


def test_demo_unknown_tool_chip(repo: Path):
    report = demo(repo, MD_OK, JS_OK + '<span class="tool-chip">made_up</span>')
    assert any("made_up" in p for p in report.problems)


def test_demo_missing_md_for_live_scenario(repo: Path):
    report = demo(repo, None, JS_OK)
    # make_scenario writes a placeholder demo md; remove it to simulate a missing script
    (repo / "docs/demo/alpha-demo.md").unlink()
    report = validate.check_demo(repo, load_scenarios(repo)["alpha"], validate.script_order(repo))
    assert any("no docs/demo/alpha-demo.md" in p for p in report.problems)


def test_demo_check_skipped_without_slides(repo: Path):
    (repo / "docs/demo/scenarios/alpha.js").unlink()
    report = validate.check_demo(repo, load_scenarios(repo)["alpha"], [])
    assert report.problems == []
    assert report.notes


def test_run_validate_reports_ok_and_fail(repo: Path, capsys):
    write(repo / "docs/demo/alpha-demo.md", MD_OK)
    write(repo / "docs/demo/scenarios/alpha.js", JS_OK)
    scenarios = list(load_scenarios(repo).values())
    assert validate.run_validate(repo, scenarios, []) == 0
    assert "alpha" in capsys.readouterr().out

    write(repo / "docs/demo/scenarios/alpha.js", JS_OK.replace("What is up?", "Different"))
    assert validate.run_validate(repo, scenarios, []) == 1
    assert "problem(s)" in capsys.readouterr().out


def test_run_validate_fails_when_discovery_had_problems(repo: Path):
    write(repo / "docs/demo/alpha-demo.md", MD_OK)
    write(repo / "docs/demo/scenarios/alpha.js", JS_OK)
    scenarios = list(load_scenarios(repo).values())
    assert validate.run_validate(repo, scenarios, ["standalone/x has no name"]) == 1
