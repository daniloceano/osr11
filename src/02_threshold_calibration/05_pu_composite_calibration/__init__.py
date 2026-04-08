"""
Step 2e — Positive-Unlabeled Composite Calibration.

Part of STEP 2 — Threshold Calibration (umbrella step).
Location: src/02_threshold_calibration/05_pu_composite_calibration/

This sub-step recalibrates compound event detection thresholds under the
positive-unlabeled (PU) framework, treating unmatched detected episodes as
unlabeled rather than as automatically false alarms. The methodology accounts
for systematic under-reporting in the SC coastal disaster database.

The composite score balances:
    - Positive recall: R_pos(θ) = H(θ) / P
    - Annual burden: B(θ) = min(1, B_raw(θ) / B_target)
    - Soft unmatched penalty: F_soft(θ) = Σ(1 - q_i)

See SCIENTIFIC_NOTES.md for the full mathematical framework.
"""
