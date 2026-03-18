"""
catalog_inspect.py
------------------
Utility to inspect CMEMS catalog and report available datasets,
variables, and coordinate ranges for a given product ID.

Usage:
    python src/acquisition/catalog_inspect.py GLOBAL_MULTIYEAR_PHY_001_030
    python src/acquisition/catalog_inspect.py GLOBAL_MULTIYEAR_WAV_001_032
"""

import sys
import logging
import copernicusmarine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def inspect_product(product_id: str) -> None:
    """Print all datasets and their variables for a CMEMS product."""
    log.info("Fetching catalog for product: %s", product_id)

    catalogue = copernicusmarine.describe(product_id=product_id, include_datasets=True)

    print(f"\n{'='*60}")
    print(f"Product: {product_id}")
    print(f"{'='*60}")

    for product in catalogue.products:
        print(f"\n  Title   : {product.title}")
        print(f"  Product : {product.product_id}")

        for dataset in product.datasets:
            print(f"\n    Dataset ID : {dataset.dataset_id}")
            print(f"    Title      : {dataset.title}")

            for version in dataset.versions:
                for part in version.parts:
                    srv = part.services[0] if part.services else None
                    if srv is None:
                        continue
                    print(f"\n      Service: {srv.service_type.short_name}")
                    for var in srv.variables:
                        short = var.short_name
                        std   = getattr(var, "standard_name", "—")
                        units = getattr(var, "units", "—")
                        print(f"        var: {short:20s}  std_name: {std:40s}  units: {units}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python catalog_inspect.py <PRODUCT_ID>")
        print("  e.g. python catalog_inspect.py GLOBAL_MULTIYEAR_PHY_001_030")
        sys.exit(1)

    product_id = sys.argv[1]
    inspect_product(product_id)


if __name__ == "__main__":
    main()
