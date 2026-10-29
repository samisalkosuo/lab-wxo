"""Tests for api_eval: prompt collection, CSV generation, and upload/evaluation flows."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from helpers import make_scenario, write
from wxodemo import api_eval
from wxodemo.chats import Api
from wxodemo.discovery import StandaloneAgent, Target


def test_build_test_case_csv():
    prompts = ["Hello, world!", 'Test with "quotes" and, commas']
    raw = api_eval.build_test_case_csv(prompts)
    text = raw.decode("utf-8")
    assert text.startswith("prompt\r\n") or text.startswith("prompt\n")
    assert "Hello, world!" in text
    assert 'Test with "quotes" and, commas' in text or 'Test with ""quotes"" and, commas' in text


def test_collect_test_prompts_scenario(tmp_path: Path):
    make_scenario(tmp_path, "demo-agent")
    tc_dir = tmp_path / "evaluation" / "demo-agent" / "test_cases"
    write(tc_dir / "tc_1.json", json.dumps({"starting_sentence": "Prompt 1"}))
    write(tc_dir / "tc_2.json", json.dumps({"prompt": "Prompt 2"}))

    from wxodemo.manifest import Scenario

    scenario = Scenario("demo-agent", {"evaluation": {"path": "evaluation/demo-agent"}}, tmp_path)
    target = Target("scenario", "demo-agent", "live", "desc", scenario=scenario)

    prompts = api_eval.collect_test_prompts(tmp_path, target)
    assert "Prompt 1" in prompts
    assert "Prompt 2" in prompts
    assert "hi" in prompts  # from make_scenario's ground_truth.json smoke_prompts


def test_collect_test_prompts_standalone(tmp_path: Path):
    agent_dir = tmp_path / "standalone" / "my-agent"
    tc_dir = agent_dir / "test_cases"
    write(tc_dir / "tc_1.json", json.dumps({"starting_sentence": "Standalone prompt 1"}))

    agent = StandaloneAgent("my-agent", agent_dir, agent_dir / "agent.yaml", "desc", [])
    target = Target("standalone", "my-agent", "-", "desc", agent=agent)

    prompts = api_eval.collect_test_prompts(tmp_path, target)
    assert prompts == ["Standalone prompt 1"]


def test_find_agent_id():
    api = MagicMock(spec=Api)
    api.request.return_value = {
        "data": [
            {"id": "uuid-1234", "name": "incident_triage"},
            {"id": "uuid-5678", "name": "other_agent"},
        ]
    }

    found = api_eval.find_agent_id(api, "https://api.example.com", "incident_triage")
    assert found == "uuid-1234"

    not_found = api_eval.find_agent_id(api, "https://api.example.com", "unknown_agent")
    assert not_found is None


def test_run_test_upload_dry_run(tmp_path: Path, capsys):
    from wxodemo.logging_setup import setup_logging

    setup_logging(tmp_path / "local" / "t.log")
    make_scenario(tmp_path, "alpha")
    from wxodemo.manifest import Scenario

    scenario = Scenario(
        "alpha",
        {"agents": [{"name": "agent_alpha"}], "evaluation": {"path": "evaluation/alpha"}},
        tmp_path,
    )
    target = Target("scenario", "alpha", "live", "desc", scenario=scenario)

    ret = api_eval.run_test_upload(tmp_path, target, None, evaluate=True, dry_run=True)
    assert ret == 0
    captured = capsys.readouterr().out
    assert "Collected 1 test prompt(s)" in captured
    assert "[dry-run]" in captured
    assert "POST /v1/orchestrate/agent/<agent_id>/test_case" in captured
    assert "POST /v1/orchestrate/agent/<agent_id>/evaluate" in captured
