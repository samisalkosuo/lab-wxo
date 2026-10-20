import logging

from wxodemo.logging_setup import mask, register_secret, setup_logging


def test_mask_replaces_registered_secret():
    register_secret("super-secret-key")
    assert "super-secret-key" not in mask("orchestrate env activate x --api-key super-secret-key")


def test_secret_never_reaches_log_file_or_console(tmp_path, capsys):
    register_secret("another-secret-value")
    log_file = tmp_path / "local" / "wxodemo.log"
    logger = setup_logging(log_file, verbose=True)
    logger.debug("token=another-secret-value")
    logger.info("using another-secret-value")
    for handler in logger.handlers:
        handler.flush()
        if isinstance(handler, logging.FileHandler):
            handler.close()
    assert "another-secret-value" not in log_file.read_text(encoding="utf-8")
    assert "another-secret-value" not in capsys.readouterr().out
