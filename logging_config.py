# logging_config.py
"""Central logging configuration for the Jarvis project.

Import once at application start:

    from logging_config import setup_logging
    log = setup_logging(__name__)

You can override the defaults by providing a *logging.yaml* file in the
project root **or** by pointing the environment variable ``LOG_CFG`` to a
YAML/JSON file with a standard ``logging.dictConfig`` schema.
"""
from __future__ import annotations

import logging
import logging.config
import os
from functools import lru_cache
from typing import Any, Dict

try:
    import yaml  # type: ignore
except ImportError:  # fallback — built‑in config only
    yaml = None  # type: ignore

# ────────────────────────── DEFAULT SCHEMA ──────────────────────────
DEFAULT_CONFIG: Dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s | %(message)s",
            "datefmt": "%H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
            "stream": "ext://sys.stdout",
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
}

# ---------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------

def _load_external_config() -> Dict[str, Any] | None:
    """Load YAML/JSON config if file present and *yaml* is available."""
    cfg_path = os.getenv("LOG_CFG", "logging.yaml")
    if not os.path.isfile(cfg_path):
        return None
    if yaml is None:
        raise RuntimeError("PyYAML not installed but external logging file requested")
    with open(cfg_path, "rt", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@lru_cache(1)
def setup_logging(logger_name: str | None = None) -> logging.Logger:
    """Configure root logger once; return child logger named *logger_name*.

    Subsequent calls return a logger but do **not** reconfigure again thanks
    to the ``@lru_cache`` decorator.
    """
    config = _load_external_config() or DEFAULT_CONFIG
    logging.config.dictConfig(config)
    return logging.getLogger(logger_name)


# ---------------------------------------------------------------------
# CLI quick‑test
# ---------------------------------------------------------------------
if __name__ == "__main__":
    log = setup_logging(__name__)
    log.debug("debug test")
    log.info("info test")
    log.warning("warning test")
    log.error("error test")
