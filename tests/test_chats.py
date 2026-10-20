"""export-chats: parsing and formatting helpers, and a full export against a fake API."""

import datetime as dt
import json
from pathlib import Path

import pytest

from wxodemo import chats
from wxodemo.config import Config, UsageError
from wxodemo.logging_setup import setup_logging

CFG = Config(api_key="k-secret-1234", url="https://x/instances/1", env_name="demo")


@pytest.fixture(autouse=True)
def logging_ready(tmp_path: Path, capsys):
    setup_logging(tmp_path / "local" / "t.log")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("90m", dt.timedelta(minutes=90)),
        ("24h", dt.timedelta(hours=24)),
        ("7d", dt.timedelta(days=7)),
        (" 2 D ", dt.timedelta(days=2)),
    ],
)
def test_parse_window(text, expected):
    assert chats.parse_window(text) == expected


@pytest.mark.parametrize("bad", ["", "7", "d", "7w", "-1d", "0h", "abc"])
def test_parse_window_rejects_bad_values(bad):
    with pytest.raises(UsageError):
        chats.parse_window(bad)


def test_time_chunks_cover_the_window_without_gaps_or_overlong_chunks():
    now = dt.datetime(2026, 1, 10, 12, 0, tzinfo=dt.UTC)
    pieces = chats.time_chunks(dt.timedelta(hours=10), now)
    assert pieces[0][1] == now
    assert pieces[-1][0] == now - dt.timedelta(hours=10)
    for (start, _), (next_start, next_end) in zip(pieces, pieces[1:], strict=False):
        assert start == next_end
        assert next_start < start
    assert all(end - start <= chats.MAX_CHUNK for start, end in pieces)


def test_slugify():
    assert chats.slugify("Hello, World! What's up?") == "Hello_World_Whats_up"
    assert chats.slugify("") == "Untitled"
    assert chats.slugify("!!!") == "Untitled"
    assert len(chats.slugify("x" * 200)) == 50
    assert chats.slugify("a\nb\tc") == "a_b_c"


def test_parse_iso_handles_z_naive_and_garbage():
    assert chats.parse_iso("2026-01-01T10:00:00Z") == dt.datetime(2026, 1, 1, 10, tzinfo=dt.UTC)
    assert chats.parse_iso("2026-01-01T10:00:00").tzinfo is not None
    assert chats.parse_iso("not a date").tzinfo is not None
    assert chats.parse_iso(None).tzinfo is not None


def test_set_file_times(tmp_path: Path):
    target = tmp_path / "f.txt"
    target.write_text("x")
    when = dt.datetime(2020, 5, 17, 8, 30, tzinfo=dt.UTC)
    chats.set_file_times(target, when)
    assert target.stat().st_mtime == pytest.approx(when.timestamp(), abs=2)


# ---------------------------------------------------------------------------
# transcripts
# ---------------------------------------------------------------------------

MESSAGES = [
    {"role": "user", "created_on": "2026-01-01T10:00:00Z", "content": [{"text": "Hello there"}]},
    {
        "role": "assistant",
        "created_on": "2026-01-01T10:00:05Z",
        "content": [
            {"text": "Hi!", "citations": [{"title": "Runbook A"}, {"url": "http://x"}]},
            {"response_type": "forms", "json_schema": {"title": "Approve"}},
        ],
        "step_history": [{"step_details": [{"tool_calls": [{"name": "t1"}, {"name": "t1"}]}]}],
    },
]


def test_parse_transcript():
    turns, first = chats.parse_transcript(MESSAGES)
    assert first == "Hello there"
    assert turns[1]["text"] == "Hi!\n\n[Form: Approve]"
    assert turns[1]["tools_used"] == ["t1"]
    assert turns[1]["citations"] == ["Runbook A", "http://x"]


def test_parse_transcript_without_text():
    turns, first = chats.parse_transcript([{"role": "assistant", "content": []}])
    assert turns[0]["text"] == "[No text content]" and first == ""


def test_render_markdown_quotes_user_and_lists_tools():
    turns, _ = chats.parse_transcript(MESSAGES)
    text = chats.render_markdown("agent_x", "Hello", "2026-01-01", turns, "abc")
    assert "# Chat Transcript: agent_x" in text
    assert "> Hello there" in text
    assert "`t1`" in text and "_Runbook A_" in text
    assert "(10:00:05 UTC)" in text


def test_detect_agent_prefers_catalog_then_hints():
    catalog = {"id1": "translator"}
    assert chats.detect_agent({"agent_id": "id1"}, [], catalog) == "translator"

    tool_msg = [{"step_history": [{"step_details": [{"tool_calls": [{"name": "get_Incident"}]}]}]}]
    assert chats.detect_agent({}, tool_msg, {}) == "incident_triage"

    named = [{"step_history": [{"step_details": [{"agent_display_name": "my_agent"}]}]}]
    assert chats.detect_agent({}, named, {}) == "my_agent"

    text_msg = [{"content": [{"text": "Hello World! friend"}]}]
    assert chats.detect_agent({}, text_msg, {}) == "hello_world"
    assert chats.detect_agent({}, [], {}) == "general"


def test_trace_helpers():
    trace = {
        "input": {"content": [{"text": "question"}]},
        "observations": [
            {"type": "GENERATION", "model": "m1", "output": {"content": "answer"}},
            {"type": "TOOL", "name": "lookup"},
            {"type": "SPAN", "name": "POST /x"},
            {"type": "SPAN", "name": "LangGraph"},
            {"type": "TOOL", "name": "lookup"},
        ],
    }
    assert chats.trace_user_text(trace) == "question"
    assert chats.trace_answer(trace) == ("answer", "m1", ["lookup"])
    assert chats.trace_user_text({"input": "plain"}) == "plain"
    assert chats.trace_user_text({"input": {"text": "t"}}) == "t"
    assert chats.trace_user_text({}) == ""


# ---------------------------------------------------------------------------
# a full export against a fake API
# ---------------------------------------------------------------------------

BASE = "https://x/instances/1"


class FakeApi:
    def __init__(self, routes: dict[str, object]):
        self.routes, self.urls = routes, []

    def request(self, url, **_):
        self.urls.append(url)
        for prefix, result in self.routes.items():
            if url.startswith(BASE + prefix):
                if isinstance(result, Exception):
                    raise result
                return result
        raise chats.ExportError(f"404 {url}")


def make_routes():
    return {
        "/v1/orchestrate/agents": [
            {"id": "a1", "name": "hello_world"},
            {"id": "a2", "name": "translator"},
        ],
        "/v1/orchestrate/threads/t1/messages": MESSAGES,
        "/v1/orchestrate/threads/t2/messages": [],
        "/v1/orchestrate/threads": [
            {"id": "t1", "agent_id": "a1", "created_on": "2026-01-01T10:00:00Z", "title": "Hi"},
            {"id": "t2", "agent_id": "a1", "created_on": "2026-01-01T11:00:00Z"},
        ],
        "/v1/agentops-v3/traces/tr1": {
            "id": "tr1",
            "agentId": "a2",
            "timestamp": "2026-01-02T09:00:00Z",
            "input": {"content": [{"text": "Translate cat"}]},
            "observations": [{"type": "GENERATION", "model": "m", "output": {"content": "kissa"}}],
        },
        "/v1/agentops-v3/traces/tr-dup": {
            "id": "tr-dup",
            "agentId": "a1",
            "conversationId": "t1",
            "input": {"text": "duplicate of thread t1"},
        },
        "/v1/agentops-v3/traces?": {
            "data": [{"id": "tr1", "timestamp": "2026-01-02T09:00:00Z"}, {"id": "tr-dup"}],
            "meta": {"totalPages": 1},
        },
    }


def export(tmp_path: Path, **overrides):
    api = FakeApi(make_routes())
    exporter = chats.Exporter(api, BASE, tmp_path, **overrides)
    exporter.load_catalog()
    exporter.resolve_filter()
    exporter.export_threads()
    exporter.export_traces()
    return exporter, exporter.write_summaries()


def test_full_export_writes_threads_traces_and_summaries(tmp_path: Path):
    _, summary = export(tmp_path, last="1d")

    assert summary == {
        "hello_world": {"conversations": 1, "messages": 2},
        "translator": {"conversations": 1, "messages": 2},
    }
    hello = sorted((tmp_path / "hello_world").glob("*.md"))
    assert len(hello) == 1 and hello[0].name.startswith("20260101_100000_Hello_there_t1")
    data = json.loads(next((tmp_path / "hello_world").glob("*.json")).read_text("utf-8"))
    assert data["source"] == "api_thread" and data["first_prompt"] == "Hello there"
    assert (tmp_path / "translator").glob("*.md")
    trace_json = json.loads(next((tmp_path / "translator").glob("*.json")).read_text("utf-8"))
    assert trace_json["source"] == "web_ui_trace_run"

    index = json.loads((tmp_path / "hello_world" / "summary.json").read_text("utf-8"))
    assert index["total_conversations"] == 1
    assert "created_dt" not in index["conversations"][0]


def test_trace_already_exported_as_thread_is_skipped(tmp_path: Path):
    exporter, _ = export(tmp_path, last="1d")
    ids = {r["id"] for recs in exporter.records.values() for r in recs}
    assert "tr-dup" not in ids and {"t1", "tr1"} <= ids


def test_agent_filter_by_name_and_by_id(tmp_path: Path):
    _, by_name = export(tmp_path / "a", agent_filter="translator", last="1d")
    assert list(by_name) == ["translator"]
    _, by_id = export(tmp_path / "b", agent_filter="a1", last="1d")
    assert list(by_id) == ["hello_world"]


def test_raw_traces_are_saved_only_when_asked(tmp_path: Path):
    export(tmp_path / "off", last="1d")
    assert not (tmp_path / "off" / "raw_traces").exists()
    export(tmp_path / "on", last="1d", raw_traces=True)
    assert (tmp_path / "on" / "raw_traces" / "tr1.json").is_file()


def test_threads_failure_is_a_warning_not_a_crash(tmp_path: Path):
    routes = make_routes()
    routes["/v1/orchestrate/threads"] = chats.ExportError("down")
    exporter = chats.Exporter(FakeApi(routes), BASE, tmp_path, last="1d")
    exporter.load_catalog()
    exporter.export_threads()
    assert exporter.records == {}


def test_overview_readme(tmp_path: Path):
    manifest = {
        "timestamp": "20260101000000",
        "created_at": "2026-01-01T00:00:00",
        "environment_name": "demo",
        "instance_url": BASE,
        "components": {
            "chats": {
                "total_conversations": 1,
                "total_messages": 2,
                "agents": {"hello_world": {"conversations": 1, "messages": 2}},
            }
        },
    }
    text = chats.write_overview(tmp_path, manifest).read_text("utf-8")
    assert "`hello_world/`" in text and "**Total conversations:** 1" in text


# ---------------------------------------------------------------------------
# the command
# ---------------------------------------------------------------------------


def test_dry_run_needs_no_credentials(tmp_path: Path, capsys):
    code = chats.run_export_chats(
        None,
        output_dir=tmp_path / "out",
        agent=None,
        last="3d",
        raw_traces=False,
        workers=2,
        dry_run=True,
    )
    assert code == 0 and "would export chats of all agents" in capsys.readouterr().out
    assert not (tmp_path / "out").exists()


def test_bad_last_fails_before_any_network(tmp_path: Path):
    with pytest.raises(UsageError):
        chats.run_export_chats(
            CFG,
            output_dir=tmp_path,
            agent=None,
            last="soon",
            raw_traces=False,
            workers=2,
            dry_run=False,
        )


def test_run_export_end_to_end_with_fake_api(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(chats, "get_token", lambda cfg: "tok-123456")
    monkeypatch.setattr(chats, "Api", lambda token: FakeApi(make_routes()))
    out = tmp_path / "out"
    code = chats.run_export_chats(
        CFG, output_dir=out, agent=None, last="1d", raw_traces=False, workers=2, dry_run=False
    )
    assert code == 0
    folder = next(out.iterdir())
    manifest = json.loads((folder / "manifest.json").read_text("utf-8"))
    assert manifest["components"]["chats"]["total_conversations"] == 2
    assert "api_key" not in json.dumps(manifest).lower() and "k-secret" not in json.dumps(manifest)
    assert (folder / "README.md").is_file()
    assert "Exported 2 conversation(s)" in capsys.readouterr().out


def test_token_error_does_not_leak_the_key(monkeypatch):
    import urllib.error

    def boom(*a, **k):
        raise urllib.error.HTTPError("u", 400, "bad", {}, None)

    monkeypatch.setattr(chats.urllib.request, "urlopen", boom)
    with pytest.raises(chats.ExportError) as info:
        chats.get_token(CFG)
    assert "k-secret-1234" not in str(info.value) and "400" in str(info.value)
