import json
from datetime import UTC, datetime

from . import config


def write_dead_letters(dead_letters: list[dict[str, object]]) -> None:
    """Append quarantined records to a local JSONL file, one run-batch per file.
    Each line has the raw resource, the resource type, and why it failed,
    so nothing is silently lost and you can inspect/reprocess later."""
    if not dead_letters:
        return
    config.DEAD_LETTER_DIR.mkdir(exist_ok=True)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = config.DEAD_LETTER_DIR / f"dead_letters_{ts}.jsonl"
    with open(out_path, "w") as f:
        f.writelines(json.dumps(entry) + "\n" for entry in dead_letters)
    print(f"⚠️  {len(dead_letters)} record(s) quarantined -> {out_path}")
