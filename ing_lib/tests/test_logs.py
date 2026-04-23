"""
Tests for the logs module - logger initialization and configuration.
"""

import logging
import os
import tempfile
import pytest
from unittest.mock import patch

from ing_lib.logs import (
    get_logger, init_console_logger, init_file_logger,
    INGENIUM_LOGGER_NAME, _clear_logger_handlers,
    _ingen_logger,
)
import ing_lib.logs as logs_module


class TestGetLogger:
    """Nominal and off-nominal tests for get_logger."""

    def test_returns_child_logger(self):
        lg = get_logger('my_module')
        assert lg.name == f'{INGENIUM_LOGGER_NAME}.my_module'

    def test_returns_root_ingenium_logger_when_none(self):
        lg = get_logger(None)
        assert lg.name == INGENIUM_LOGGER_NAME

    def test_child_loggers_share_parent(self):
        lg1 = get_logger('mod_a')
        lg2 = get_logger('mod_b')
        assert lg1.parent is lg2.parent


class TestInitConsoleLogger:
    """Nominal and off-nominal tests for init_console_logger."""

    def setup_method(self):
        self._orig = logs_module._engine_configured
        _clear_logger_handlers(_ingen_logger)

    def teardown_method(self):
        logs_module._engine_configured = self._orig
        _clear_logger_handlers(_ingen_logger)

    def test_adds_handler(self):
        logs_module._engine_configured = False
        init_console_logger(logging.WARNING)
        assert len(_ingen_logger.handlers) >= 1

    def test_reentrant_replaces_handler(self):
        logs_module._engine_configured = False
        init_console_logger(logging.INFO)
        count_after_first = len(_ingen_logger.handlers)
        init_console_logger(logging.DEBUG)
        assert len(_ingen_logger.handlers) == count_after_first

    def test_env_override(self):
        logs_module._engine_configured = False
        with patch.dict(os.environ, {'ING_LOG_LEVEL': '30'}):
            init_console_logger()
        handler = _ingen_logger.handlers[-1]
        assert handler.level == 30  # WARNING

    def test_env_override_invalid_falls_back(self):
        logs_module._engine_configured = False
        with patch.dict(os.environ, {'ING_LOG_LEVEL': 'not_a_number'}):
            init_console_logger()
        handler = _ingen_logger.handlers[-1]
        assert handler.level == logging.INFO


class TestInitFileLogger:
    """Nominal and off-nominal tests for init_file_logger."""

    def setup_method(self):
        self._orig = logs_module._engine_configured
        _clear_logger_handlers(_ingen_logger)

    def teardown_method(self):
        logs_module._engine_configured = self._orig
        _clear_logger_handlers(_ingen_logger)

    def test_creates_file_handler(self):
        logs_module._engine_configured = False
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
            path = f.name
        try:
            init_file_logger(logging.DEBUG, path)
            file_handlers = [h for h in _ingen_logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) >= 1
        finally:
            os.unlink(path)

    def test_auto_inits_console_if_not_configured(self):
        logs_module._engine_configured = False
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
            path = f.name
        try:
            init_file_logger(logging.INFO, path)
            assert logs_module._engine_configured is True
        finally:
            os.unlink(path)


class TestClearLoggerHandlers:
    """Tests for _clear_logger_handlers."""

    def test_removes_all_handlers(self):
        test_logger = logging.getLogger('test_clear')
        test_logger.addHandler(logging.StreamHandler())
        test_logger.addHandler(logging.StreamHandler())
        assert len(test_logger.handlers) == 2
        _clear_logger_handlers(test_logger)
        assert len(test_logger.handlers) == 0
