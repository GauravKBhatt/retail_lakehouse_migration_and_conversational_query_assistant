import json
import logging
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"

_logger = logging.getLogger("retail_lakehouse")
_handler = logging.FileHandler(LOG_DIR/"server.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)

def log_event(event: str, data:dict) -> None:
    """Write a structured JSON line to the log file + python logger"""
    record = {
        "timestamp":datetime.now(timezone.utc).isoformat(),
        "event":event,
        **data,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str)+"\n")
    _logger.info("%s | %s",event,json.dumps(data,default=str)[:500])