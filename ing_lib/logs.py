import logging
import os
from rich.logging import RichHandler
from rich.console import Console

# ----------------------------------------------------------------------
# Formatting constants 
INGENIUM_LOGGER_NAME = "ingenium"     
CONSOLE_LOG_FORMAT = '[%(funcName)s] %(message)s'
FILE_LOG_FORMAT = '%(asctime)s %(levelname)s [%(funcName)s] %(message)s [%(filename)s:%(lineno)d]'
LOG_DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

# ----------------------------------------------------------------------
# Internal flag – we only configure the root logger once
_engine_configured = False

# ----------------------------------------------------------------------
# The shared Ingenium logger (created once at import time)
_ingen_logger = logging.getLogger(INGENIUM_LOGGER_NAME)

# ----------------------------------------------------------------------
# Helper – clear any existing handlers from a logger
def _clear_logger_handlers(logger: logging.Logger) -> None:
    """Remove any handlers that might already be attached to *logger*."""
    for h in list(logger.handlers):
        logger.removeHandler(h)

def init_console_logger(level: int = logging.INFO) -> None:
    """
    Initialise a *single* Rich console (or fallback) handler on the root logger.
    Re-entrant – calling it multiple times simply replaces the old handler.
    """
    global _engine_configured
    if _engine_configured:
        _clear_logger_handlers(_ingen_logger)

    # Keep DEBUG on the logger so child loggers can emit any level.
    _ingen_logger.setLevel(logging.DEBUG)


    console_handler = RichHandler(
        show_level=True,
        rich_tracebacks=True,
        show_time=True,
        show_path=True,
        omit_repeated_times=False,
        log_time_format=LOG_DATE_FORMAT,
        console=Console(width=255)
        )


    # -----------------------------------------------------------------
    # Allow an environment variable to override the level.
    # -----------------------------------------------------------------
    env_level = os.getenv('ING_LOG_LEVEL')
    if env_level:
        try:
            level = int(env_level)
        except ValueError:
            level = logging.INFO   # safe default

    console_handler.setLevel(level)

    # Ensure a formatter is present for non‑Rich handlers
    if not isinstance(console_handler, RichHandler):
        console_handler.setFormatter(logging.Formatter(CONSOLE_LOG_FORMAT))

    _ingen_logger.addHandler(console_handler)
    _engine_configured = True


# ----------------------------------------------------------------------
# Initialise file handler on the same Ingenium logger
def init_file_logger(level: int, file_path: str) -> None:
    """
    Attach a file handler to the already‑configured Ingenium logger.
    The function does not reset the console handler.
    """
    global _engine_configured
    if not _engine_configured:
        # Ensure console logger exists – otherwise the file logger would be
        # the only output and may hide console output.
        init_console_logger()

    try:
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(FILE_LOG_FORMAT, LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)


        _ingen_logger.addHandler(file_handler)
    except Exception:  # pragma: no cover
        _ingen_logger.warning('Failed to initialise file logger', exc_info=True)


# ----------------------------------------------------------------------
# Public accessor – returns the Ingenium logger or a child thereof
def get_logger(name: str = None) -> logging.Logger:
    """
    Return a logger that is a child of the dedicated Ingenium logger.
    If ``name`` is ``None`` the Ingenium logger itself is returned.
    """
    if name is None:
        return _ingen_logger
    # ``getChild`` creates a hierarchical name: ingenium.<name>
    return _ingen_logger.getChild(name)

