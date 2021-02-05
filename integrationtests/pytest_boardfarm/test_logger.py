def test_logger(bf_logger):
    bf_logger.log_step("Start Logging")
    assert getattr(bf_logger, "log_step", None)
