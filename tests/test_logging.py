def test_logging_creates_debug_file_and_rotation(tmp_path):
    import logging
    import velora.log as log

    log._configured = False
    logger = log.configure_logging(str(tmp_path))
    logger.debug("debug diagnostic marker")
    for handler in logger.handlers:
        handler.flush()

    text = (tmp_path / "velora.log").read_text(encoding="utf-8")
    assert "logging initialized" in text
    assert "debug diagnostic marker" in text
    assert logger.level == logging.DEBUG
