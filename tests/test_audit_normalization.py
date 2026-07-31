from pathlib import Path

import numpy as np
import pandas as pd

from src.risk_integration.exposure_index import effective_population, exposure_inform
from src.risk_integration.hazard_index import derive_native_hazard_index
from src.site.export_risk_index_data import integrated_risk


def test_cumulative_band_weights_and_ring_interpretation() -> None:
    frame = pd.DataFrame({
        "pop_1km": [10.0], "pop_2km": [20.0],
        "pop_5km": [30.0], "pop_10km": [40.0],
    })
    # Rings contain 10 people each: 10*(1.0 + 0.6 + 0.3 + 0.1) = 20.
    assert effective_population(frame).iloc[0] == 20.0


def test_effective_population_is_used_without_a_floor() -> None:
    population = pd.Series([0.0, 10_000.0])
    total = pd.Series([100.0, 20_000.0])
    exposure = exposure_inform(population, total)
    assert exposure.iloc[0] == 0.0
    assert 0.0 < exposure.iloc[1] < 1.0


def test_fixed_hazard_anchors_fill_no_event_severity_nan(tmp_path: Path) -> None:
    source = tmp_path / "hazard.csv"
    pd.DataFrame({
        "grid_lat": [0.0, 0.2, 0.4], "grid_lon": [-40.0, -40.0, -40.0],
        "compound_count_total": [0, 99, 198],
        "mean_integrated_severity": [np.nan, 0.5, 2.0],
    }).to_csv(source, index=False)
    result, _ = derive_native_hazard_index(source)
    assert result["Hazard_Frequency"].tolist() == [0.0, 1.0, 1.0]
    assert result["Hazard_Severity"].tolist() == [0.0, 0.5, 1.0]
    assert result["Hazard_Index"].tolist() == [0.0, 0.75, 1.0]
    assert result["Hazard_Index"].equals(result["Hazard_Index_raw"])


def test_risk_has_correct_cube_root_precedence_and_preserves_zero() -> None:
    result = integrated_risk(
        pd.Series([0.0, 0.125]),
        pd.Series([0.8, 0.8]),
        pd.Series([0.6, 0.6]),
    )
    assert result.iloc[0] == 0.0
    assert np.isclose(result.iloc[1], (0.125 * 0.8 * 0.6) ** (1.0 / 3.0))
    assert result.between(0.0, 1.0).all()
