import logging
import json
import time
from pathlib import Path
from datetime import datetime
from config.settings import LOG_LEVEL, LOG_DIR


LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


class OperationLogger:
    """Structured logger for tracking agent operations."""

    def __init__(self, operation: str, logger_name: str = "operation"):
        self.operation = operation
        self.logger = get_logger(logger_name)
        self.start_time = time.time()
        self.log_path = LOG_DIR / f"ops_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        self.record: dict = {
            "operation": operation,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "documents_created": [],
            "rows_updated": [],
            "errors": [],
            "retries": 0,
            "metadata": {},
        }
        self.logger.info(f"Starting: {operation}")

    def add_document(self, doc_id: str, title: str):
        self.record["documents_created"].append({"id": doc_id, "title": title})
        self.logger.info(f"Document created: {title} ({doc_id})")

    def add_row_update(self, row: int, field: str, value: str):
        self.record["rows_updated"].append({"row": row, "field": field, "value": value})
        self.logger.debug(f"Row {row} updated: {field}={value}")

    def add_error(self, error: str):
        self.record["errors"].append({"time": datetime.now().isoformat(), "error": error})
        self.logger.error(f"Error in {self.operation}: {error}")

    def increment_retry(self):
        self.record["retries"] += 1
        self.logger.warning(f"Retry #{self.record['retries']} for {self.operation}")

    def set_metadata(self, key: str, value):
        self.record["metadata"][key] = value

    def finish(self):
        elapsed = time.time() - self.start_time
        self.record["end_time"] = datetime.now().isoformat()
        self.record["duration_seconds"] = round(elapsed, 2)
        self.logger.info(f"Completed: {self.operation} in {elapsed:.2f}s")
        with open(self.log_path, "a") as f:
            f.write(json.dumps(self.record) + "\n")
        return self.record
