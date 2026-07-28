"""
Download script: IBGE Grade Estatistica 2022 tiles covering the study coastline
Dataset: Grade Estatistica do IBGE - Censo Demografico 2022
Institution: Instituto Brasileiro de Geografia e Estatistica (IBGE)
Edition: Notas metodologicas 01/2025; vector files dated 2025-06-12
Cells: 200 m x 200 m in urban census tracts, 1 km x 1 km in rural ones
Variables: TOTAL (resident population), TOTAL_DOM (occupied households)
CRS: SIRGAS 2000 geographic (EPSG:4674)
Tool: urllib (standard library only)
Run: python -m src.01_data_preparation.acquisition.download_ibge_grade
Output: data/raw/ibge/grade_estatistica_2022/grade_id<NN>.zip
        data/metadata/ibge_grade_estatistica_2022_download.json

Why tiles and not the national file
-----------------------------------
The native grid is published only as tiles keyed by the 500 km articulation
quadrant, and the quadrant identifiers are *not* state codes: ``grade_id27``
covers the Cabo Frio region of Rio de Janeiro, not Alagoas. The quadrants that
matter are therefore discovered geometrically, by intersecting the published
500 km layer (8.5 kB) with the coastal municipalities of this study. Twenty
quadrants intersect them, for roughly 264 MB of compressed tiles.

The national 1 km file (``BR1KM``, 416 MB) is an aggregation of the same data
and is not downloaded here: it would discard the 200 m detail exactly where the
coastal population concentrates.

Provenance and reproducibility
------------------------------
IBGE embeds a revision date in several file names (``BR1KM_20251002.zip``) and
revises products in place, so a hard-coded URL can rot silently. This script
therefore lists the remote directory, matches the file names with a pattern, and
records the resolved name, the server ``Last-Modified``, the byte size and a
local SHA-256 for every file it downloads. A file already on disk whose size
matches the server is not downloaded again.

Note on sizes: the IBGE server does not answer ``HEAD`` with ``Content-Length``.
The remote size is read from the ``Content-Range`` header of a two-byte ranged
``GET`` instead.
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import geopandas as gpd


ROOT = Path(__file__).resolve().parents[3]

BASE_URL = (
    "https://geoftp.ibge.gov.br/recortes_para_fins_estatisticos"
    "/grade_estatistica/censo_2022"
)
ARTICULATION_URL = f"{BASE_URL}/grade_500km"
TILE_URL = f"{BASE_URL}/grade_estatistica"
DOCUMENTATION_FILES = (
    "Notas_metodologicas_grade_estatistica_2022.pdf",
    "Tutorial_grade_estatistica_2022.pdf",
)

#: Municipal layer that defines which quadrants are relevant. It carries the
#: 282 coastal municipalities of the study, already in EPSG:4326.
MUNICIPALITY_SOURCE = (
    ROOT / "site" / "public" / "data" / "risk_index_municipalities.geojson"
)

OUTPUT_DIR = ROOT / "data" / "raw" / "ibge" / "grade_estatistica_2022"
METADATA_DIR = ROOT / "data" / "metadata"
METADATA_FILE = METADATA_DIR / "ibge_grade_estatistica_2022_download.json"

#: The default urllib agent is refused by some IBGE front ends.
USER_AGENT = "osr11-research-download/1.0 (IAG-USP; academic use)"
TIMEOUT_S = 300


@dataclass
class RemoteFile:
    """A file on the IBGE server, as resolved at run time."""

    url: str
    name: str
    size_bytes: int
    last_modified: str | None


def _request(url: str, headers: dict[str, str] | None = None) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, **(headers or {})},
    )


def list_directory(url: str) -> list[str]:
    """Return the file and directory names linked from an IBGE listing page."""
    with urllib.request.urlopen(_request(url), timeout=TIMEOUT_S) as response:
        html = response.read().decode("utf-8", errors="replace")
    names = re.findall(r'href="([^"?/][^"]*)"', html)
    return sorted({n for n in names if not n.startswith(("http", "#"))})


def resolve_remote(url: str) -> RemoteFile:
    """Resolve a URL to its size and modification date without downloading it.

    The IBGE server omits ``Content-Length`` from ``HEAD`` responses, so the
    size is taken from the ``Content-Range`` of a two-byte ranged ``GET``.
    """
    request = _request(url, {"Range": "bytes=0-1"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
        content_range = response.headers.get("Content-Range")
        last_modified = response.headers.get("Last-Modified")
    if not content_range or "/" not in content_range:
        raise RuntimeError(
            f"{url} did not answer a ranged GET with Content-Range; "
            "the remote size cannot be verified"
        )
    return RemoteFile(
        url=url,
        name=url.rsplit("/", 1)[-1],
        size_bytes=int(content_range.rsplit("/", 1)[-1]),
        last_modified=last_modified,
    )


def sha256(path: Path, chunk_bytes: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_bytes), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(remote: RemoteFile, destination: Path) -> bool:
    """Download ``remote`` unless ``destination`` already matches its size.

    Returns ``True`` when bytes were transferred.
    """
    if destination.exists() and destination.stat().st_size == remote.size_bytes:
        print(f"  = {remote.name} already complete ({remote.size_bytes:,} B)")
        return False

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    print(f"  > {remote.name} ({remote.size_bytes / 1e6:.1f} MB)")
    with urllib.request.urlopen(_request(remote.url), timeout=TIMEOUT_S) as response:
        with open(partial, "wb") as handle:
            while chunk := response.read(1 << 20):
                handle.write(chunk)

    written = partial.stat().st_size
    if written != remote.size_bytes:
        partial.unlink(missing_ok=True)
        raise RuntimeError(
            f"{remote.name}: expected {remote.size_bytes} bytes, received {written}"
        )
    partial.replace(destination)
    return True


def discover_quadrants(
    articulation_zip: Path,
    municipality_source: Path = MUNICIPALITY_SOURCE,
) -> tuple[list[str], dict[str, Any]]:
    """Return the articulation quadrants intersecting the coastal municipalities."""
    if not municipality_source.exists():
        raise FileNotFoundError(
            f"{municipality_source} is required to decide which grid tiles to "
            "download. Generate it with src.site.export_risk_index_data first."
        )
    municipalities = gpd.read_file(municipality_source)
    quadrants = gpd.read_file(f"zip://{articulation_zip}")
    if quadrants.crs != municipalities.crs:
        quadrants = quadrants.to_crs(municipalities.crs)

    matched = gpd.sjoin(
        quadrants,
        municipalities[["geometry"]],
        how="inner",
        predicate="intersects",
    )
    selected = sorted(set(matched["QUADRANTE"]))
    if not selected:
        raise RuntimeError(
            "No articulation quadrant intersects the coastal municipalities; "
            "the layers are probably misaligned"
        )
    provenance = {
        "method": (
            "Articulation quadrants of the 500 km layer intersecting the "
            "coastal municipalities of the study"
        ),
        "municipality_source": str(municipality_source.relative_to(ROOT)),
        "municipality_count": int(len(municipalities)),
        "quadrant_count_total": int(len(quadrants)),
        "quadrant_count_selected": len(selected),
        "quadrants": selected,
    }
    return selected, provenance


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    def fetch(url: str, destination: Path) -> RemoteFile:
        remote = resolve_remote(url)
        download(remote, destination)
        records.append(
            {
                **asdict(remote),
                "path": str(destination.relative_to(ROOT)),
                "sha256": sha256(destination),
            }
        )
        return remote

    print("Articulation layer (500 km quadrants)")
    articulation_names = list_directory(ARTICULATION_URL)
    articulation_zips = [n for n in articulation_names if n.endswith(".zip")]
    if len(articulation_zips) != 1:
        raise RuntimeError(
            f"Expected exactly one archive in {ARTICULATION_URL}, "
            f"found: {articulation_zips}"
        )
    articulation_path = OUTPUT_DIR / articulation_zips[0]
    fetch(f"{ARTICULATION_URL}/{articulation_zips[0]}", articulation_path)

    print("Selecting quadrants")
    quadrants, quadrant_provenance = discover_quadrants(articulation_path)
    print(f"  {len(quadrants)} quadrants: {', '.join(quadrants)}")

    print("Documentation")
    for name in DOCUMENTATION_FILES:
        fetch(f"{BASE_URL}/{name}", OUTPUT_DIR / name)

    print("Grid tiles (200 m urban / 1 km rural)")
    available = set(list_directory(TILE_URL))
    for quadrant in quadrants:
        # QUADRANTE is published as ``ID_27`` and the archive as ``grade_id27``.
        name = f"grade_{quadrant.replace('ID_', 'id')}.zip"
        if name not in available:
            raise RuntimeError(
                f"{name} is expected for quadrant {quadrant} but is not listed "
                f"at {TILE_URL}; the remote layout has changed"
            )
        fetch(f"{TILE_URL}/{name}", OUTPUT_DIR / name)

    total_bytes = sum(record["size_bytes"] for record in records)
    metadata = {
        "dataset": "Grade Estatistica do IBGE",
        "product": "Grade Estatistica - Censo Demografico 2022",
        "institution": "Instituto Brasileiro de Geografia e Estatistica (IBGE)",
        "edition": "Notas metodologicas 01/2025",
        "reference_year": 2022,
        "reference_date": "2022-07-31",
        "spatial_coverage": "Brazil, restricted here to the coastal quadrants",
        "spatial_unit": "regular grid cell",
        "resolution": "200 m in urban census tracts, 1 km in rural ones",
        "crs": "EPSG:4674 (SIRGAS 2000 geographic)",
        "working_projection": (
            "Albers equal-area, SIRGAS 2000, central meridian -54, standard "
            "parallels -2 and -22, latitude of origin -12"
        ),
        "variables": {
            "TOTAL": "resident population in the cell",
            "TOTAL_DOM": "occupied households in the cell (private and collective)",
        },
        "allocation": (
            "Census 2022 universe microdata linked to CNEFE 2022 household "
            "coordinates. Geocoding quality levels 1-4 are included; levels 5 "
            "and 6 (median of street/postcode and census-tract centroid) are "
            "excluded by IBGE, which removes 0.028% of the national population "
            "and 0.019% of the households. The excluded share is regionally "
            "uneven and largest in the North (0.370% in Roraima, 0.161% in "
            "Amapa)."
        ),
        "known_limitations": [
            "Only population and occupied households are published for 2022; "
            "the 2010 edition also carried sex and age.",
            "Cell geometry is inherited from the 2010 grid: 1 km cells that "
            "became urban were split into 200 m cells, but no 200 m cell was "
            "merged back.",
            "The grid is not a complete tessellation of the territory.",
            "The methodological notes do not describe any suppression or "
            "perturbation of small counts.",
        ],
        "license": "Public data distributed by IBGE; cite the source.",
        "documentation": [f"{BASE_URL}/{name}" for name in DOCUMENTATION_FILES],
        "source_url": BASE_URL,
        "tool": "urllib (standard library)",
        "downloaded_by": "Danilo Couto de Souza",
        "download_date": datetime.now(timezone.utc).isoformat(),
        "quadrant_selection": quadrant_provenance,
        "files": records,
        "file_count": len(records),
        "total_bytes": total_bytes,
        "notes": (
            "Downloaded to build a coastal population-exposure layer for the "
            "compound coastal extremes study. Raw archives are not versioned; "
            "this metadata file is."
        ),
    }
    with open(METADATA_FILE, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(
        f"\n{len(records)} files, {total_bytes / 1e6:.1f} MB total\n"
        f"Provenance: {METADATA_FILE.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
