"""
monitor.py
----------
Monitor the progress of an ongoing or completed parallel CMEMS download.

Reads logs/download_status.json written by download_cmems_parallel.py
and reports:
  - percentage complete
  - counts per status (done / running / failed / pending)
  - elapsed time and estimated time remaining
  - whether the downloader process is still alive

Usage:
    # Single snapshot
    python src/acquisition/monitor.py

    # Watch mode (refresh every 10 s)
    python src/acquisition/monitor.py --watch

    # Custom refresh interval
    python src/acquisition/monitor.py --watch --interval 30

    # Show individual task list
    python src/acquisition/monitor.py --tasks
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

STATUS_FILE = Path("logs/download_status.json")

# ANSI helpers
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
RESET  = "\033[0m"
CLEAR  = "\033[2J\033[H"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_alive(pid: int) -> bool:
    """Return True if a process with the given PID is running."""
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _fmt_duration(seconds: float) -> str:
    seconds = int(seconds)
    h, rem  = divmod(seconds, 3600)
    m, s    = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def _bar(fraction: float, width: int = 40) -> str:
    filled = int(round(fraction * width))
    return f"[{'█' * filled}{'░' * (width - filled)}]"


def _avg_task_duration(tasks: list[dict]) -> float | None:
    durations = [t["duration_s"] for t in tasks if t.get("duration_s") is not None]
    if not durations:
        return None
    return sum(durations) / len(durations)


# ---------------------------------------------------------------------------
# Core render
# ---------------------------------------------------------------------------

def render(data: dict, show_tasks: bool = False) -> str:
    pid        = data.get("pid", 0)
    total      = data.get("total", 0)
    completed  = data.get("completed", 0)
    failed     = data.get("failed", 0)
    running    = data.get("running", 0)
    pending    = data.get("pending", 0)
    started_at = data.get("started_at", "")
    tasks      = data.get("tasks", [])
    cfg_file   = data.get("config_file", "—")

    alive   = _is_alive(pid) if pid else False
    status_str = f"{GREEN}RUNNING{RESET} (PID {pid})" if alive else f"{YELLOW}STOPPED{RESET} (PID {pid})"

    # Elapsed
    elapsed_str = "—"
    if started_at:
        try:
            started = datetime.fromisoformat(started_at)
            elapsed = (datetime.now(timezone.utc) - started).total_seconds()
            elapsed_str = _fmt_duration(elapsed)
        except ValueError:
            pass
    else:
        elapsed = 0.0

    # ETA
    eta_str     = "—"
    avg_dur     = _avg_task_duration(tasks)
    active_workers = max(running, 1)
    remaining   = pending + running
    if avg_dur and remaining > 0:
        eta_s   = (remaining / active_workers) * avg_dur
        eta_str = _fmt_duration(eta_s)

    # Progress bar
    fraction = completed / total if total else 0.0
    pct      = fraction * 100

    lines: list[str] = []
    lines.append(f"{BOLD}OSR11 — CMEMS Download Monitor{RESET}")
    lines.append(f"Config  : {cfg_file}")
    lines.append(f"Process : {status_str}")
    lines.append(f"Elapsed : {elapsed_str}   ETA: {eta_str}")
    lines.append("")
    lines.append(f"  {_bar(fraction)}  {pct:5.1f}%  ({completed}/{total})")
    lines.append("")

    col = lambda s, c: f"{c}{s}{RESET}"
    lines.append(
        f"  {col(f'Done    {completed:>4}', GREEN)}   "
        f"{col(f'Running {running:>4}', CYAN)}   "
        f"{col(f'Pending {pending:>4}', RESET)}   "
        f"{col(f'Failed  {failed:>4}', RED if failed else RESET)}"
    )

    if show_tasks and tasks:
        lines.append("")
        lines.append(f"  {'Task ID':<30} {'Status':<10} {'Duration':>10}  File")
        lines.append("  " + "-" * 80)
        for t in sorted(tasks, key=lambda x: x["task_id"]):
            st  = t["status"]
            dur = _fmt_duration(t["duration_s"]) if t.get("duration_s") else "—"
            fname = Path(t["output_path"]).name if t.get("output_path") else "—"
            color = {
                "done":    GREEN,
                "running": CYAN,
                "failed":  RED,
                "pending": "",
            }.get(st, "")
            err_hint = f"  ← {t['error'][:60]}" if st == "failed" and t.get("error") else ""
            lines.append(f"  {t['task_id']:<30} {color}{st:<10}{RESET} {dur:>10}  {fname}{err_hint}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor OSR11 CMEMS parallel download progress.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--watch",    "-w", action="store_true",
                        help="Refresh continuously until download completes.")
    parser.add_argument("--interval", "-i", type=int, default=10,
                        help="Refresh interval in seconds (watch mode).")
    parser.add_argument("--tasks",    "-t", action="store_true",
                        help="Show individual task list.")
    parser.add_argument("--status-file", type=Path, default=STATUS_FILE,
                        help="Path to the JSON status file.")
    return parser.parse_args()


def load_status(path: Path) -> dict:
    if not path.exists():
        print(f"Status file not found: {path}")
        print("Start a download with: python src/acquisition/download_cmems_parallel.py")
        sys.exit(1)
    return json.loads(path.read_text())


def main() -> None:
    args = parse_args()

    if not args.watch:
        data = load_status(args.status_file)
        print(render(data, show_tasks=args.tasks))
        return

    try:
        while True:
            data = load_status(args.status_file)
            print(CLEAR + render(data, show_tasks=args.tasks), flush=True)

            pid   = data.get("pid", 0)
            done  = data.get("completed", 0)
            total = data.get("total", 0)
            alive = _is_alive(pid) if pid else False

            if not alive and done >= total and total > 0:
                print(f"\n{GREEN}All tasks complete.{RESET}")
                break

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")


if __name__ == "__main__":
    main()
