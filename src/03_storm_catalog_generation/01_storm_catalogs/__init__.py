"""Submodule 01 — Storm Catalogs.

Core storm catalog generation pipeline:
    main.py          CLI orchestrator (4-phase: load → tides → catalog → figures)
    segmentation.py  Exceedance detection + episode clustering
    metrics.py       Per-episode attribute computation
    io.py            I/O helpers (load thresholds, save catalogs/metadata)
    tides.py         FES2022 tide wrapper (runtime mode only)
    figures.py       QA diagnostic figures (annual counts, duration, seasonality)

Usage:
    python -m src.03_storm_catalog_generation.01_storm_catalogs.main [--phase all]
"""
