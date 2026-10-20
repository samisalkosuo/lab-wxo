from pathlib import Path

import pytest

from wxodemo.config import ConfigError, load_config, parse_env_text


def write_cfg(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "env.cfg"
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_skips_comments_and_splits_on_first_equals():
    values = parse_env_text("# comment\n\nWXO_URL=https://x/y?a=b\n  WXO_ENV_NAME = demo \n")
    assert values == {"WXO_URL": "https://x/y?a=b", "WXO_ENV_NAME": "demo"}


def test_load_valid_config_defaults_env_type(tmp_path):
    path = write_cfg(
        tmp_path,
        "WXO_API_KEY=abc123\nWXO_URL=https://api.example.com/instances/1\nWXO_ENV_NAME=demo\n",
    )
    cfg = load_config(path)
    assert cfg.env_type == "ibm_iam"
    assert cfg.env_name == "demo"


def test_load_respects_env_type(tmp_path):
    path = write_cfg(
        tmp_path,
        "WXO_API_KEY=abc123\nWXO_URL=https://api.example.com/i/1\nWXO_ENV_NAME=d\nWXO_ENV_TYPE=mcsp\n",
    )
    assert load_config(path).env_type == "mcsp"


def test_missing_file_explains_how_to_create_it(tmp_path):
    with pytest.raises(ConfigError) as err:
        load_config(tmp_path / "env.cfg")
    message = str(err.value)
    assert "env.cfg.example" in message
    assert "WXO_API_KEY" in message


def test_missing_and_placeholder_values_are_all_listed(tmp_path):
    path = write_cfg(
        tmp_path,
        "WXO_API_KEY=your-api-key-here\nWXO_URL=https://api.<region>.x/instances/<instance-id>\n",
    )
    with pytest.raises(ConfigError) as err:
        load_config(path)
    message = str(err.value)
    for key in ("WXO_API_KEY", "WXO_URL", "WXO_ENV_NAME"):
        assert key in message


def test_bom_in_file_is_tolerated(tmp_path):
    path = tmp_path / "env.cfg"
    path.write_bytes(
        b"\xef\xbb\xbfWXO_API_KEY=abc123\nWXO_URL=https://a.example/i/1\nWXO_ENV_NAME=d\n"
    )
    assert load_config(path).api_key == "abc123"
