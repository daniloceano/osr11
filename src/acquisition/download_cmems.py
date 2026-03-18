"""
download_cmems.py
-----------------
Download GLORYS (sea level) and WAVERYS (wave) data from CMEMS
for the OSR11 compound coastal flooding project.

Authentication:
    Run once before use:
        copernicusmarine login

    Or set environment variables:
        COPERNICUSMARINE_SERVICE_USERNAME
        COPERNICUSMARINE_SERVICE_PASSWORD

Usage:
    # Download both products with default config
    python src/acquisition/download_cmems.py

    # Specify a config file
    python src/acquisition/download_cmems.py --config config/download_config.yml

    # Download only one product
    python src/acquisition/download_cmems.py --product glorys
    python src/acquisition/download_cmems.py --product waverys

    # Inspect catalog only (no download)
    python src/acquisition/download_cmems.py --inspect
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml
import copernicusmarine

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("osr11.download")


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

DEFAULT_CONFIG_PATH = Path("config/download_config.yml")
EXAMPLE_CONFIG_PATH = Path("config/download_config.example.yml")


def load_config(path: Path) -> dict:
    """Load YAML config. Falls back to example config if path not found."""
    if not path.exists():
        log.warning(
            "Config file not found at %s — falling back to example config at %s",
            path, EXAMPLE_CONFIG_PATH,
        )
        path = EXAMPLE_CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"No config file found. Copy config/download_config.example.yml "
            f"to config/download_config.yml and adjust as needed."
        )
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Catalog inspection
# ---------------------------------------------------------------------------

def _get_dataset_id(product_id: str) -> str:
    """
    Resolve the primary dataset_id for a given CMEMS product_id.

    CMEMS products may contain multiple datasets (e.g. monthly vs daily).
    This function returns the first available dataset_id and logs all
    options so the user can override via config if needed.
    """
    log.info("Inspecting catalog for product '%s' …", product_id)
    catalogue = copernicusmarine.describe(product_id=product_id)

    dataset_ids: list[str] = []
    for product in catalogue.products:
        for dataset in product.datasets:
            dataset_ids.append(dataset.dataset_id)

    if not dataset_ids:
        raise RuntimeError(
            f"No datasets found for product '{product_id}'. "
            "Check the product ID or your CMEMS credentials."
        )

    if len(dataset_ids) > 1:
        log.info(
            "Multiple datasets found for %s:\n  %s\nUsing the first: %s",
            product_id,
            "\n  ".join(dataset_ids),
            dataset_ids[0],
        )
    else:
        log.info("Dataset found: %s", dataset_ids[0])

    return dataset_ids[0]


def inspect_variables(product_id: str) -> None:
    """Print all variables available in a product (for reference)."""
    catalogue = copernicusmarine.describe(product_id=product_id)
    print(f"\nProduct: {product_id}")
    for product in catalogue.products:
        for dataset in product.datasets:
            print(f"  Dataset: {dataset.dataset_id}")
            for version in dataset.versions:
                for part in version.parts:
                    for svc in part.services:
                        for var in svc.variables:
                            print(
                                f"    {var.short_name:25s} "
                                f"std={getattr(var,'standard_name','—')}"
                            )


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_product(
    *,
    product_id: str,
    variables: list[str],
    bbox: dict,
    period: dict,
    output_dir: Path,
    output_filename: str,
    dataset_id: str | None = None,
) -> Path:
    """
    Download a CMEMS product subset and save as NetCDF.

    Parameters
    ----------
    product_id    : CMEMS product identifier (used for catalog lookup if
                    dataset_id is not supplied).
    variables     : List of variable short names to download.
    bbox          : Dict with keys lon_min, lon_max, lat_min, lat_max.
    period        : Dict with keys start, end (ISO date strings).
    output_dir    : Directory where the file will be saved.
    output_filename: Name of the output NetCDF file.
    dataset_id    : Explicit dataset_id. If None, resolved from catalog.
    """
    if dataset_id is None:
        dataset_id = _get_dataset_id(product_id)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_filename

    log.info(
        "Downloading %s\n"
        "  dataset   : %s\n"
        "  variables : %s\n"
        "  lon       : [%.2f, %.2f]\n"
        "  lat       : [%.2f, %.2f]\n"
        "  period    : %s → %s\n"
        "  output    : %s",
        product_id,
        dataset_id,
        variables,
        bbox["lon_min"], bbox["lon_max"],
        bbox["lat_min"], bbox["lat_max"],
        period["start"], period["end"],
        output_path,
    )

    copernicusmarine.subset(
        dataset_id=dataset_id,
        variables=variables,
        minimum_longitude=bbox["lon_min"],
        maximum_longitude=bbox["lon_max"],
        minimum_latitude=bbox["lat_min"],
        maximum_latitude=bbox["lat_max"],
        start_datetime=period["start"],
        end_datetime=period["end"],
        output_filename=str(output_path),
        force_download=True,
    )

    log.info("Saved: %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download GLORYS/WAVERYS data from CMEMS for OSR11.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to YAML config file.",
    )
    parser.add_argument(
        "--product", "-p",
        choices=["glorys", "waverys", "both"],
        default="both",
        help="Which product to download.",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Inspect catalog only; do not download.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg  = load_config(args.config)

    bbox       = cfg["bbox"]
    period     = cfg["period"]
    output_dir = Path(cfg.get("output_dir", "data/raw"))

    if args.inspect:
        for key in ("glorys", "waverys"):
            if args.product in (key, "both"):
                inspect_variables(cfg[key]["product_id"])
        return

    if args.product in ("glorys", "both"):
        gcfg = cfg["glorys"]
        download_product(
            product_id=gcfg["product_id"],
            variables=gcfg["variables"],
            bbox=bbox,
            period=period,
            output_dir=output_dir / "glorys",
            output_filename=f"glorys_sealevel_{period['start']}_{period['end']}.nc",
            dataset_id=gcfg.get("dataset_id"),
        )

    if args.product in ("waverys", "both"):
        wcfg = cfg["waverys"]
        download_product(
            product_id=wcfg["product_id"],
            variables=wcfg["variables"],
            bbox=bbox,
            period=period,
            output_dir=output_dir / "waverys",
            output_filename=f"waverys_waves_{period['start']}_{period['end']}.nc",
            dataset_id=wcfg.get("dataset_id"),
        )


if __name__ == "__main__":
    main()
