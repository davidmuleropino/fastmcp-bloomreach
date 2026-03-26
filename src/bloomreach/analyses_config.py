"""Shared load/save logic for the analyses ID→name config.

Storage priority (read):
  1. BLOOMREACH_ANALYSES_JSON env var  — full JSON string, useful for cloud deployments
     where the filesystem is ephemeral (e.g. Cloud Run).  Set this to the JSON output
     returned by upsert_analysis / delete_analysis to persist changes across restarts.
  2. File at BLOOMREACH_ANALYSES_CONFIG  — default: <repo-root>/analyses.json
     Suitable for local / stdio use or cloud with a mounted volume.

Storage priority (write):
  1. File path (if writable)
  2. In-memory only for the session — every mutating tool returns the full JSON
     so the caller can update BLOOMREACH_ANALYSES_JSON in their deployment config.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

_DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "analyses.json"

ANALYSIS_TYPES = ("reports", "funnels", "retentions", "segmentations")


def _config_path() -> Path:
    return Path(os.environ.get("BLOOMREACH_ANALYSES_CONFIG", str(_DEFAULT_CONFIG_PATH)))


def load() -> dict[str, dict[str, str]]:
    """Return the full analyses config dict."""
    # Priority 1: env var with full JSON blob (cloud-friendly)
    env_json = os.environ.get("BLOOMREACH_ANALYSES_JSON", "").strip()
    if env_json:
        try:
            return json.loads(env_json)
        except json.JSONDecodeError:
            pass

    # Priority 2: config file
    path = _config_path()
    if path.exists():
        with open(path) as f:
            return json.load(f)

    return {t: {} for t in ANALYSIS_TYPES}


def save(config: dict[str, dict[str, str]]) -> bool:
    """Persist config to file. Returns True if written, False if filesystem is read-only."""
    path = _config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(config, f, indent=2)
            f.write("\n")
        return True
    except OSError:
        return False
