"""
Run-id generator for BETSE simulation uploads.

Prompt: implement _betse and betse_cfg_wizard routes to the server infrastructure
(paste routes, adapt settings).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

def generate_id(time=False) -> str:
    """CHAR: short opaque id for betse_data/<run_id>/ folders."""
    return uuid.uuid4().hex if time is False else str(datetime.now(timezone.utc).isoformat())
