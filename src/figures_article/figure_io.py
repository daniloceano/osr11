"""Shared output policy for the article figures.

These helpers lived in ``make_article_risk_figures``, which was split into the
per-figure scripts in 43c7c2e and deleted without its importers being updated.
Every module that referenced it has been failing at import since; they now
import from here.

The policy itself is unchanged: article figures are PNG only, at 300 dpi, with
semantic file names — an ordinal stem such as ``fig03_`` is rejected, because
figure numbers change between manuscript revisions while file names should not.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterator

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs" / "article_figures"
METADATA_DIR = OUT_DIR / "metadata"

ARTICLE_FIGURE_FORMAT = "png"
ARTICLE_FIGURE_DPI = 300
ORDINAL_FILENAME_PATTERN = re.compile(
    r"^(?:(?:fig(?:ure)?|main_figure|primary)_?\d+|[a-z]?\d+)_",
    re.IGNORECASE,
)

IMAGE_EXTENSIONS = {
    ".png", ".pdf", ".svg", ".jpg", ".jpeg", ".tif", ".tiff", ".webp",
}


def _relative(path: Path) -> str:
    """Path relative to the repository root, for provenance records."""
    try:
        return str(Path(path).relative_to(ROOT))
    except ValueError:
        return str(path)


def _save_figure(fig: plt.Figure, stem: str) -> list[str]:
    """Save one article figure using the repository-wide PNG-only policy."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if ORDINAL_FILENAME_PATTERN.match(stem):
        raise ValueError(f"Article figure stem must be semantic, not ordinal: {stem!r}")
    path = OUT_DIR / f"{stem}.{ARTICLE_FIGURE_FORMAT}"
    fig.savefig(path, dpi=ARTICLE_FIGURE_DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return [_relative(path)]


def _iter_json_strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_json_strings(item)


def validate_article_figure_outputs() -> None:
    """Fail clearly when images or manifest paths violate article-figure rules."""
    errors: list[str] = []
    for path in OUT_DIR.rglob("*"):
        if not path.is_file() or path.name == "README.md":
            continue
        suffix = path.suffix.lower()
        if suffix in IMAGE_EXTENSIONS and suffix != ".png":
            errors.append(f"non-PNG article figure: {_relative(path)}")
        if suffix == ".png" and ORDINAL_FILENAME_PATTERN.match(path.stem):
            errors.append(f"ordinal article-figure filename: {_relative(path)}")

    for manifest in METADATA_DIR.glob("*.json"):
        with manifest.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        for value in _iter_json_strings(payload):
            suffix = Path(value).suffix.lower()
            if suffix not in IMAGE_EXTENSIONS:
                continue
            if suffix != ".png":
                errors.append(f"non-PNG path in {_relative(manifest)}: {value}")
                continue
            figure_path = Path(value)
            if not figure_path.is_absolute():
                figure_path = ROOT / figure_path
            if ORDINAL_FILENAME_PATTERN.match(figure_path.stem):
                errors.append(f"ordinal path in {_relative(manifest)}: {value}")
            if not figure_path.is_file():
                errors.append(f"missing figure recorded in {_relative(manifest)}: {value}")

    if errors:
        raise RuntimeError("Article-figure validation failed:\n- " + "\n- ".join(errors))
