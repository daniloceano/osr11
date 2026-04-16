"""Step 3 — Hazard Characterization.

Architecture
------------
    01_storm_catalogs/       Storm catalog generation (main pipeline)
    02_compound_detection/   Compound event detection (temporal overlap)
    03_duration_persistence/ Duration & persistence statistics
    04_monthly_seasonality/  Monthly/seasonal climatology
    05_trends/               Mann–Kendall + Sen slope trend analysis
    06_univariate_eva/       POT–GPD extreme value analysis
    07_dependence/           Hs–SSH_total dependence (τ, ρ, χ, χ̄)
    08_site_export/          Unified JSON export for results website
    config/                  Central configuration
    shared/                  Shared utilities (catalog I/O, helpers)

Entry points
------------
    python -m src.03_storm_catalog_generation.01_storm_catalogs.main [--phase all]
    python -m src.03_storm_catalog_generation.hazard_characterization [--all]
"""
