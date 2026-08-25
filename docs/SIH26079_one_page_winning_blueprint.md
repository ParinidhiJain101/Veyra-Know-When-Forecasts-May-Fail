# SIH26079 — One-Page Winning Blueprint

## Exact project concept

**Forecast-Bust Sentinel** is an issue-time-safe meta-forecasting system that predicts when an existing medium-range NWP forecast is likely to fail materially over an India-focused region. It does not replace NWP. It learns from forecast uncertainty, successive-run revisions, regime context and historical verification to produce a calibrated, lead-specific risk map, severity estimate, failure-timing signal and an explicit **ABSTAIN / human review** state.

## Exact novelty claim

The defensible claim is **not** “the first forecast-bust detector” and not “AI predicts weather better.” Uno et al. already demonstrated advance detection of regional solar-radiation forecast busts using multi-centre ensemble spread [1], while recent weather-UQ, conformal, representation and analog work establishes important adjacent precedents [2]. The proposed contribution is an **underexplored, rigorously leakage-controlled India/public-proxy application** that tests whether run-to-run forecast trajectory, regime conditioning, spatial/object labels, calibrated risk, analog evidence and OOD-aware abstention add measurable value beyond spread-only baselines.

## Research gaps → technology

| Gap | Technology | Proof |
|---|---|---|
| G1 India medium-range gap | GEFS/WeatherBench 2 + ERA5 public-proxy meta-forecast | Blocked India-domain evaluation versus spread-only |
| G2 ambiguous bust labels | Versioned robust q95 label engine with q90/q97.5/q99 sensitivity, gray band and displacement tolerance | Label-agreement and model-sensitivity study |
| G3 spatial displacement | Neighborhood/object labels, risk maps and FSS-style metrics | Gridpoint versus neighborhood comparison |
| G4 rare events | Event-aware blocking, class weighting and block bootstrap | Stable CIs and event-holdout performance |
| G5 spread is incomplete | GBM residual learning from revision, regime, disagreement and analog blocks | Incremental ablations above E2 spread |
| G6–G7 changing trajectory/regime | Run-to-run trend/acceleration and regime-conditioned calibration | Early warning lead and stratified reliability |
| G8–G9 overconfidence | OOD score, conformal experiment and selective abstention | Coverage–risk and retained-case Brier/PR-AUC |
| G10–G15 operations/trust | Spatial/time risk, analog cards, provenance API and conservative explanations | Replay demo, user workflow and audit package |

## Exact data

**Prototype:** a bounded India-domain slice of public GEFS or WeatherBench 2 forecast products [3] [4], paired to ERA5 or approved observations for verification [5]. Use Zarr for fields, Parquet for feature/label tables, and immutable manifests with checksums, issue/valid times, members, units, grid and model version. **NCMRWF operational validation is not claimed** until a paired historical NEPS archive, truth product, metadata and permission are provided.

## Exact ML

1. E0 climatology; E1 persistence; E2 ensemble-spread threshold/logistic; E3 logistic regression; E4 calibrated LightGBM/XGBoost.
2. E5 revision trajectory; E6 regime; E7 analog; E8 multi-model disagreement.
3. E9 isotonic/Platt calibration; E10 split/online conformal and conformal-risk-control experiments; E11 OOD; E12 abstention.
4. E13 spatial object output; E14 discrete-time failure hazard; E15 self-supervised representation; E16 one advanced model only if it beats the GBM under strict testing.

## Exact experiments and pass gates

The primary label is robust region/season/lead-normalized error above a training-only q95 threshold, with a gray ambiguity band and neighborhood/object handling for spatial fields. The primary metrics are PR-AUC, Brier, reliability/ECE, precision/recall/F1, false-alarm ratio, detection rate, warning lead time, review burden, spatial object/FSS-style scores, coverage–risk and retained-case metrics. Train/validation/test are chronological; cyclone/monsoon events, regions, OOD regimes and later NWP versions are held out. The final model must beat spread-only and logistic baselines without worsening calibration or creating unacceptable abstention. If not, ship the calibrated spread-only product.

## Exact demo

In 3–5 minutes: show an apparently normal forecast; replay successive issue cycles; reveal growing revision instability; show risk rising by lead; localize the emerging spatial risk object; open two historical analog cards; show top correlational evidence; trigger OOD/ABSTAIN on an unfamiliar case; reveal final verification; toggle spread-only versus full system; finish with Brier/PR-AUC/reliability/lead-time deltas and the explicit public-proxy versus NCMRWF scope banner.

## Why judges should care

The product answers an operational question that ordinary forecast dashboards do not: **“Should I trust this forecast, where is it likely to fail, and when should I review it?”** Its credibility comes from a reproducible label engine, honest baselines, calibrated uncertainty, event-level leakage controls and an engineered failure mode for unfamiliar weather—not from a fashionable model name.

## Biggest risk and mitigation

**Biggest risk:** no usable paired historical NCMRWF archive, or no incremental skill beyond ensemble spread. **Mitigation:** public-proxy validation with explicit claim scope; begin with Z500/T2m; use precipitation/cyclone modules as extensions; preserve a calibrated spread-only fallback; request NCMRWF partner data as the next validation phase.

## Final SIH pitch

> **“We do not replace the weather forecast—we predict when it is about to fail. Forecast-Bust Sentinel learns from ensemble uncertainty, forecast revision trajectories and historical atmospheric analogs, produces calibrated region-wise risk for Day 1–10, recognizes unfamiliar regimes, and says ‘I don’t know’ when it lacks evidence. Every claimed improvement is proved against spread-only under leakage-safe, event-held-out tests.”**

## References

[1]: https://www.sciencedirect.com/science/article/pii/S0038092X17311428
[2]: https://arxiv.org/abs/2606.19642
[3]: https://www.ncei.noaa.gov/products/weather-climate-models/global-ensemble-forecast
[4]: https://weatherbench2.readthedocs.io/en/latest/data-guide.html
[5]: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview
