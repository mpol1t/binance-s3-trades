import logging as py_logging
from unittest.mock import Mock

import binance_s3_trades.logging as mod


def test_setup_logging_configures_basic_config_and_boto_loggers(monkeypatch):
    # Patch ONLY inside the module under test, so pytest/logging internals are untouched.
    basic = Mock()
    monkeypatch.setattr(mod.logging, "basicConfig", basic)

    # Provide distinct logger mocks per name, and support getLogger() with no args.
    loggers: dict[str, Mock] = {}
    root_logger = Mock(spec=py_logging.Logger)

    def fake_get_logger(name: str | None = None) -> Mock:
        if not name:
            return root_logger
        if name not in loggers:
            loggers[name] = Mock(spec=py_logging.Logger)
        return loggers[name]

    monkeypatch.setattr(mod.logging, "getLogger", fake_get_logger)

    mod.setup_logging("INFO")

    basic.assert_called_once()
    _, kwargs = basic.call_args
    assert kwargs["level"] == "INFO"
    assert "%(asctime)s" in kwargs["format"]

    # These three are explicitly tuned by setup_logging
    assert set(loggers.keys()) >= {"boto3", "botocore", "s3transfer"}
    loggers["boto3"].setLevel.assert_called_once_with(py_logging.WARNING)
    loggers["botocore"].setLevel.assert_called_once_with(py_logging.WARNING)
    loggers["s3transfer"].setLevel.assert_called_once_with(py_logging.WARNING)
