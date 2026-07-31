"""Canonical definitions of the municipal exposure term.

Every candidate normalisation of the coastal population lives here, so the
website export and the exploratory figures cannot drift apart. They were
previously recomputed independently in three modules, over reference
populations that differed by two municipalities, which was enough to move
``E_rank`` by up to 0.005.

Why the count needs a normalisation at all
------------------------------------------
Min--Max is an affine rescaling: it changes a variable's range and never its
shape. The coastal population count has skewness above 7, so under a plain
Min--Max it stays that skewed inside [0, 1] and roughly nine municipalities in
ten fall below 0.05 — a term with a nominal weight of one third and almost no
influence. ``E_linear`` is kept only so that claim stays checkable.

The INFORM recipe
-----------------
The variant recommended for the risk index follows the Index for Risk
Management (INFORM, JRC), which treats exactly this problem for its physical
exposure indicators:

* **log before rescaling** (INFORM §6.2) — the log transformation is applied to
  indicators "based on a people count", to reduce positive skewness;
* **fixed goalposts rather than the observed extremes** (INFORM §6.3) — because
  outliers otherwise make the observed min and max unrepresentative of the bulk
  of the data. Fixed bounds "preserve the rescaling factor and make the
  transformation stable through the time series" and "exclude the distortion
  effect of outliers". INFORM's own absolute-exposure goalposts are round
  numbers on the log scale, e.g. Log(100)–Log(10E6) for flood and tropical
  cyclone exposure;
* **absolute and relative together** (INFORM Box 2) — "the absolute value of
  people exposed will favour more populated countries while the value of
  population exposed relative to the total population will reverse the problem
  and favour less populated hazard-prone countries", so INFORM computes the
  indicator both ways and aggregates the pair.

Two caveats on transferring that recipe here. INFORM sets the *relative*
goalposts to the realistic range as well, which at country scale is a fraction
of a percent; the natural interval [0, 1] is used below only because the
municipal coastal share actually spans it, with a median of 0.90. And INFORM's
Box 2 states an arithmetic average for the absolute/relative pair while its
Table 5 shows geometric averages inside the hazard components; the geometric
form is used here so that a single operator governs both this pair and the
final risk product, and the two agree to Spearman 0.995 on this dataset anyway.

``exposure_inform`` (the INFORM recipe above) feeds the published risk index:
``src/site/export_risk_index_data.py`` imports it and uses its result as the
``Exposure_Index`` factor of ``Risk_Hazard_raw``. ``exposure_absolute`` and
``exposure_relative`` are also imported by that exporter and published as the
auxiliary ``Exposure_absolute``/``Exposure_relative`` fields, but neither feeds
the risk product directly. The remaining candidates (``exposure_linear``,
``exposure_log10``, ``exposure_rank``, ``all_variants``, ``variant_components``)
are wired into the website exposure layer (`export_exposure_data.py`) and the
exploratory comparisons only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


#: Goalposts of the absolute term, in inhabitants within the distance band.
#: Round numbers on the log scale, in INFORM's style. Values outside saturate
#: rather than being discarded: on the 2022 census, one municipality reaches
#: the floor and five reach the ceiling, leaving 98 % on the continuous scale.
GOALPOST_MIN_INHABITANTS = 1.0e2
GOALPOST_MAX_INHABITANTS = 1.0e6

#: Weights applied to cumulative distance bands. The equivalent weights by
#: ring are 1.0, 0.6, 0.3 and 0.1 for 0--1, 1--2, 2--5 and 5--10 km.
EFFECTIVE_POPULATION_WEIGHTS = {
    "pop_1km": 0.4,
    "pop_2km": 0.3,
    "pop_5km": 0.2,
    "pop_10km": 0.1,
}


def effective_population(frame: pd.DataFrame) -> pd.Series:
    """Calculate ``pop_eff``, an effective/weighted, not literal, population.

    The inputs are cumulative and nested. Weighting their common numerator
    once is algebraically identical to weighting each municipal share.
    """
    missing = sorted(set(EFFECTIVE_POPULATION_WEIGHTS).difference(frame.columns))
    if missing:
        raise ValueError(f"Missing cumulative exposure bands: {', '.join(missing)}")
    bands = frame[list(EFFECTIVE_POPULATION_WEIGHTS)].apply(
        pd.to_numeric, errors="coerce"
    )
    if bands.isna().any().any():
        raise ValueError("Cumulative exposure bands contain missing values")
    nested = (
        (bands["pop_1km"] <= bands["pop_2km"])
        & (bands["pop_2km"] <= bands["pop_5km"])
        & (bands["pop_5km"] <= bands["pop_10km"])
    )
    if not nested.all():
        raise ValueError("Exposure bands are not cumulative/nested")
    result = sum(
        bands[field] * weight
        for field, weight in EFFECTIVE_POPULATION_WEIGHTS.items()
    )
    if (result > bands["pop_10km"] + 1e-9).any():
        raise ValueError("Effective population exceeds the 10 km band")
    return result


def _series(values: pd.Series | np.ndarray) -> pd.Series:
    return values if isinstance(values, pd.Series) else pd.Series(values)


def minmax(values: pd.Series) -> pd.Series:
    """Min--Max over the observed range. The scale is defined by the extremes."""
    values = _series(values).astype(float)
    finite = values[np.isfinite(values)]
    lower, upper = float(finite.min()), float(finite.max())
    if np.isclose(lower, upper):
        return pd.Series(0.0, index=values.index)
    return (values - lower) / (upper - lower)


def exposure_linear(population: pd.Series) -> pd.Series:
    """Min--Max of the raw count. Degenerate; retained for inspection only."""
    return minmax(_series(population).astype(float))


def exposure_log10(population: pd.Series) -> pd.Series:
    """Min--Max of log10(count + 1), with the scale taken from the data."""
    return minmax(np.log10(_series(population).astype(float) + 1.0))


def exposure_rank(population: pd.Series) -> pd.Series:
    """Percentile rank of the count, ties taking the average of their positions.

    Note that ``method='average'`` differs from the empirical percentile used in
    the compound-intensity component of this study, which is the ``<=`` ECDF and
    corresponds to ``method='max'``. On this dataset a single tied pair exists
    and the two differ by 0.002; if this variant is ever adopted, the
    definitions should be aligned.
    """
    return _series(population).astype(float).rank(pct=True)


def exposure_absolute(
    population: pd.Series,
    goalpost_min: float = GOALPOST_MIN_INHABITANTS,
    goalpost_max: float = GOALPOST_MAX_INHABITANTS,
) -> pd.Series:
    """Log-scaled count between fixed goalposts, saturating outside them.

    Unlike :func:`exposure_log10`, the scale does not depend on which units are
    present: removing the largest municipality leaves every other value
    untouched, and ``0.5`` always denotes the same population — the geometric
    mean of the two goalposts.
    """
    if not 0 < goalpost_min < goalpost_max:
        raise ValueError(
            f"Goalposts must satisfy 0 < min < max; got {goalpost_min}, {goalpost_max}"
        )
    counts = _series(population).astype(float).clip(lower=1.0)
    span = np.log10(goalpost_max) - np.log10(goalpost_min)
    return ((np.log10(counts) - np.log10(goalpost_min)) / span).clip(0.0, 1.0)


def exposure_relative(
    population: pd.Series,
    municipal_population: pd.Series,
) -> pd.Series:
    """Share of the municipal population inside the distance band.

    Bounded by construction. It measures coastal orientation rather than the
    number of people present, which is why it is half of a pair and never the
    whole exposure term: a village entirely on the shore and a city entirely on
    the shore both score 1.
    """
    total = _series(municipal_population).astype(float).replace(0.0, np.nan)
    share = _series(population).astype(float) / total
    return share.fillna(0.0).clip(0.0, 1.0)


def exposure_inform(
    population: pd.Series,
    municipal_population: pd.Series,
    goalpost_min: float = GOALPOST_MIN_INHABITANTS,
    goalpost_max: float = GOALPOST_MAX_INHABITANTS,
    combine: str = "geometric",
) -> pd.Series:
    """Absolute and relative exposure combined, in the INFORM manner."""
    absolute = exposure_absolute(population, goalpost_min, goalpost_max)
    relative = exposure_relative(population, municipal_population)
    if combine == "geometric":
        return (absolute * relative) ** 0.5
    if combine == "arithmetic":
        return (absolute + relative) / 2.0
    raise ValueError(f"combine must be 'geometric' or 'arithmetic'; got {combine!r}")


#: Candidate exposure terms, in the order they should be presented: the
#: recommended one first, then the two single-facet candidates, then the
#: degenerate control.
VARIANT_ORDER = ("E_inform", "E_log10", "E_rank", "E_linear")


def all_variants(
    population: pd.Series,
    municipal_population: pd.Series,
) -> dict[str, pd.Series]:
    """Every candidate exposure term, computed over one reference population."""
    return {
        "E_inform": exposure_inform(population, municipal_population),
        "E_log10": exposure_log10(population),
        "E_rank": exposure_rank(population),
        "E_linear": exposure_linear(population),
    }


def variant_components(
    population: pd.Series,
    municipal_population: pd.Series,
) -> dict[str, pd.Series]:
    """The two halves of the INFORM term, for display and audit."""
    return {
        "E_inform_absolute": exposure_absolute(population),
        "E_inform_relative": exposure_relative(population, municipal_population),
    }
