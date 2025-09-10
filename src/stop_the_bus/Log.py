import atexit
import contextlib
import logging
import os
import queue
import time
from datetime import UTC, datetime
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path
from uuid import uuid4


class UTCFormatter(logging.Formatter):
    converter = staticmethod(time.gmtime)


class ContextFilter(logging.Filter):
    def __init__(self, run_id: str) -> None:
        super().__init__()
        self.run_id: str = run_id

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "run_id"):
            record.run_id = self.run_id
        return True


def get_log_level(level: str | int | None) -> int:
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")

    return getattr(logging, level.upper(), logging.INFO) if isinstance(level, str) else int(level)


def get_log_file_path(run_id: str, log_dir: str | Path) -> Path:
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")

    return log_dir / f"{ts}-{run_id}.log"


def setup_logging(
    logger_name: str = "",
    level: str | int | None = None,
    log_dir: str | Path = "logs",
) -> logging.Logger:
    level = get_log_level(level)
    run_id: str = uuid4().hex[:8]
    log_file: Path = get_log_file_path(run_id, log_dir)

    root: logging.Logger = logging.getLogger()
    print(level)
    root.setLevel(level)
    for h in root.handlers[:]:
        root.removeHandler(h)

    log_queue: queue.Queue[logging.LogRecord] = queue.Queue(-1)
    log_handler = QueueHandler(log_queue)
    root.addHandler(log_handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8", delay=True)
    file_handler.setLevel(level=level)

    fmt = "%(asctime)s %(levelname)s %(message)s"
    datefmt = "%Y-%m-%dT%H:%M:%S"

    formatter = UTCFormatter(fmt=fmt, datefmt=datefmt)
    file_handler.setFormatter(formatter)

    ctx = ContextFilter(run_id)
    file_handler.addFilter(ctx)

    listener = QueueListener(log_queue, file_handler, respect_handler_level=True)
    listener.start()

    def _shutdown() -> None:
        try:
            listener.stop()
        finally:
            with contextlib.suppress(Exception):
                file_handler.flush()
            with contextlib.suppress(Exception):
                file_handler.close()

    atexit.register(_shutdown)

    logger: logging.Logger = logging.getLogger(logger_name)
    return logger
