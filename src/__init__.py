"""
OSR11 source package.

Registers numbered analysis directories under their non-numbered import
aliases so that ``from src.xxx import`` statements continue to work after
directories are renamed to ``01_xxx``, ``02_xxx``, etc.

Adding a new numbered module:
    1. Rename the directory (git mv).
    2. Add an entry to _MODULE_ALIASES below — that is all.
"""
import importlib.util
import sys
from pathlib import Path

_src_dir = Path(__file__).parent

# alias (importable name) → real directory name (may start with digit)
_MODULE_ALIASES: dict[str, str] = {
    "explore_test_data_south_sc": "01_explore_test_data_south_sc",
    "threshold_calibration":      "02_threshold_calibration",
}


def _register_numbered_modules() -> None:
    for alias, real_name in _MODULE_ALIASES.items():
        real_dir  = _src_dir / real_name
        init_file = real_dir / "__init__.py"
        if not init_file.exists():
            continue
        pkg_key = f"src.{alias}"
        if pkg_key in sys.modules:
            continue
        spec = importlib.util.spec_from_file_location(
            pkg_key,
            str(init_file),
            submodule_search_locations=[str(real_dir)],
        )
        if spec is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        sys.modules[pkg_key] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]


_register_numbered_modules()
