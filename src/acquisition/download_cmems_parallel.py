"""
download_cmems_parallel.py
--------------------------
Parallel download of GLORYS and WAVERYS data from CMEMS.
Splits the configured time range into monthly tasks and runs them
concurrently using a thread pool.

Progress is written to logs/download_status.json and can be monitored
in a separate terminal with:
    python src/acquisition/monitor.py

Usage:
    python src/acquisition/download_cmems_parallel.py
    python src/acquisition/download_cmems_parallel.py --config config/download_config.yml
    python src/acquisition/download_cmems_parallel.py --product glorys
    python src/acquisition/download_cmems_parallel.py --workers 6
    python src/acquisition/download_cmems_parallel.py --resume   # skip already-done files
"""

from __future__ import annotations

import argparse
import calendar
import json
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

# Allow running from project root: python src/acquisition/download_cmems_parallel.py
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import copernicusmarine
from src.acquisition.download_cmems import load_config

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("osr11.parallel")

STATUS_FILE = Path("logs/download_status.json")


# ---------------------------------------------------------------------------
# Task model
# ---------------------------------------------------------------------------

@dataclass
class DownloadTask:
    task_id: str           # e.g. "glorys_1993-01"
    product_key: str       # "glorys" or "waverys"
    dataset_id: str
    variables: list[str]
    bbox: dict
    month_start: str       # ISO date "YYYY-MM-DD"
    month_end: str         # ISO date "YYYY-MM-DD"
    output_path: str
    status: str = "pending"   # pending | running | done | failed
    started_at: str | None = None
    finished_at: str | None = None
    duration_s: float | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Status file (thread-safe)
# ---------------------------------------------------------------------------

class StatusTracker:
    def __init__(self, tasks: list[DownloadTask], config_file: str) -> None:
        self._lock = threading.Lock()
        self._tasks: dict[str, DownloadTask] = {t.task_id: t for t in tasks}
        self._config_file = config_file
        self._started_at = datetime.now(timezone.utc).isoformat()
        self._pid = os.getpid()
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        self._flush()

    def mark_running(self, task_id: str) -> None:
        with self._lock:
            t = self._tasks[task_id]
            t.status = "running"
            t.started_at = datetime.now(timezone.utc).isoformat()
            self._flush()

    def mark_done(self, task_id: str) -> None:
        with self._lock:
            t = self._tasks[task_id]
            t.status = "done"
            t.finished_at = datetime.now(timezone.utc).isoformat()
            if t.started_at:
                dt = datetime.fromisoformat(t.finished_at) - datetime.fromisoformat(t.started_at)
                t.duration_s = dt.total_seconds()
            self._flush()

    def mark_failed(self, task_id: str, error: str) -> None:
        with self._lock:
            t = self._tasks[task_id]
            t.status = "failed"
            t.finished_at = datetime.now(timezone.utc).isoformat()
            t.error = error
            self._flush()

    def _flush(self) -> None:
        tasks_list = [asdict(t) for t in self._tasks.values()]
        total     = len(tasks_list)
        completed = sum(1 for t in tasks_list if t["status"] == "done")
        failed    = sum(1 for t in tasks_list if t["status"] == "failed")
        running   = sum(1 for t in tasks_list if t["status"] == "running")
        pending   = sum(1 for t in tasks_list if t["status"] == "pending")

        payload = {
            "pid":          self._pid,
            "config_file":  self._config_file,
            "started_at":   self._started_at,
            "total":        total,
            "completed":    completed,
            "failed":       failed,
            "running":      running,
            "pending":      pending,
            "tasks":        tasks_list,
        }
        tmp = STATUS_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2))
        tmp.replace(STATUS_FILE)   # atomic on POSIX


# ---------------------------------------------------------------------------
# Period helpers
# ---------------------------------------------------------------------------

def iter_months(start: str, end: str):
    """Yield (month_start_iso, month_end_iso) for each month in [start, end]."""
    d     = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    while d <= end_d:
        last_day  = calendar.monthrange(d.year, d.month)[1]
        month_end = min(date(d.year, d.month, last_day), end_d)
        yield d.isoformat(), month_end.isoformat()
        # advance to first day of next month
        if d.month == 12:
            d = date(d.year + 1, 1, 1)
        else:
            d = date(d.year, d.month + 1, 1)


# ---------------------------------------------------------------------------
# Task generation
# ---------------------------------------------------------------------------

def build_tasks(cfg: dict, product_filter: str, output_dir: Path) -> list[DownloadTask]:
    """Build the full list of monthly DownloadTask objects from config."""
    bbox   = cfg["bbox"]
    period = cfg["period"]
    tasks: list[DownloadTask] = []

    for key in ("glorys", "waverys"):
        if product_filter not in (key, "both"):
            continue

        pcfg       = cfg[key]
        dataset_id = pcfg.get("dataset_id") or _resolve_dataset_id(pcfg["product_id"])
        variables  = pcfg["variables"]
        var_tag    = "_".join(variables)
        subdir     = output_dir / key

        for m_start, m_end in iter_months(period["start"], period["end"]):
            month_tag = m_start[:7]  # "YYYY-MM"
            fname     = f"{key}_{var_tag}_{month_tag}.nc"
            tasks.append(DownloadTask(
                task_id     = f"{key}_{month_tag}",
                product_key = key,
                dataset_id  = dataset_id,
                variables   = variables,
                bbox        = bbox,
                month_start = m_start,
                month_end   = m_end,
                output_path = str(subdir / fname),
            ))

    return tasks


def _resolve_dataset_id(product_id: str) -> str:
    log.info("Resolving dataset_id for %s from catalog …", product_id)
    cat = copernicusmarine.describe(product_id=product_id)
    for product in cat.products:
        for dataset in product.datasets:
            return dataset.dataset_id
    raise RuntimeError(f"No datasets found for product '{product_id}'")


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

def run_task(task: DownloadTask, tracker: StatusTracker) -> None:
    tracker.mark_running(task.task_id)
    out = Path(task.output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    log.info("[START] %s → %s", task.task_id, out.name)
    try:
        copernicusmarine.subset(
            dataset_id        = task.dataset_id,
            variables         = task.variables,
            minimum_longitude = task.bbox["lon_min"],
            maximum_longitude = task.bbox["lon_max"],
            minimum_latitude  = task.bbox["lat_min"],
            maximum_latitude  = task.bbox["lat_max"],
            start_datetime    = task.month_start,
            end_datetime      = task.month_end,
            output_filename   = str(out),
            force_download    = True,
        )
        tracker.mark_done(task.task_id)
        log.info("[DONE]  %s", task.task_id)
    except Exception as exc:
        tracker.mark_failed(task.task_id, str(exc))
        log.error("[FAIL]  %s — %s", task.task_id, exc)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parallel monthly download of GLORYS/WAVERYS from CMEMS.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--config",  "-c", type=Path, default=Path("config/download_config.yml"))
    parser.add_argument("--product", "-p", choices=["glorys", "waverys", "both"], default="both")
    parser.add_argument("--workers", "-w", type=int, default=None,
                        help="Max concurrent downloads. Overrides config parallel.max_workers.")
    parser.add_argument("--resume", action="store_true",
                        help="Skip tasks whose output file already exists on disk.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg  = load_config(args.config)

    max_workers = args.workers or cfg.get("parallel", {}).get("max_workers", 4)
    output_dir  = Path(cfg.get("output_dir", "data/raw"))

    tasks = build_tasks(cfg, args.product, output_dir)

    if args.resume:
        skipped = [t for t in tasks if Path(t.output_path).exists()]
        for t in skipped:
            t.status = "done"
            log.info("[SKIP]  %s already exists", t.task_id)
        pending = [t for t in tasks if t.status == "pending"]
    else:
        pending = tasks

    log.info(
        "Tasks: %d total | %d to download | %d workers",
        len(tasks), len(pending), max_workers,
    )
    log.info("Status file: %s", STATUS_FILE)
    log.info("Monitor with: python src/acquisition/monitor.py")

    tracker = StatusTracker(tasks, str(args.config))

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(run_task, t, tracker): t for t in pending}
        for future in as_completed(futures):
            # Exceptions are already caught inside run_task; re-raise unexpected ones.
            exc = future.exception()
            if exc:
                log.error("Unhandled exception in worker: %s", exc)

    total     = len(tasks)
    completed = sum(1 for t in tasks if t.status == "done")
    failed    = sum(1 for t in tasks if t.status == "failed")
    log.info("Finished — %d/%d done, %d failed.", completed, total, failed)


if __name__ == "__main__":
    main()
