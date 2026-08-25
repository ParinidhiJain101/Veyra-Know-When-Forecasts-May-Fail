# SIH26079 — Complete End-to-End Engineering Roadmap (Detailed v2)

> **How to use this manual.** Read Sections 1–8 before writing code. Read Sections 9–18 while the repository and data contracts are being built. Read Sections 19–29 before training. Read Sections 30–41 while the product is integrated. Read Sections 42–62 before release. Every section begins with an execution card so a team member can identify the owner, inputs, outputs, files, commands, tests, failure path and gate without guessing.

**Source of truth.** This manual elaborates the approved SIH26079 research concept; it does not replace the research strategy. The platform is an issue-time-safe meta-forecast of future NWP forecast failure. The first validation is public-proxy-only using GEFS or WeatherBench 2 and ERA5/approved observations. NCMRWF operational validation is conditional on paired historical forecast data, verification data, metadata and permission.

**Engineering rule.** A feature, model, service or dashboard panel is not complete because it exists. It is complete only when its schema, provenance, test, failure behavior, reproducible command and acceptance evidence exist.

## Detailed navigation and release gates

| Gate | Required evidence | Blocking failures |
|---|---|---|
| G0 scope | Claim sheet, source/license manifest, approved variables and leads | Any hidden NCMRWF claim or unbounded data scope |
| G1 data | Raw checksums, QC report, aligned issue/valid keys, missingness report | Timestamp, unit, grid or member ambiguity |
| G2 labels | Versioned Bust Label Engine, q95 primary, q90/q97.5/q99 sensitivity, ambiguity policy | Thresholds fitted on validation/test or labels cannot be reproduced |
| G3 features | Feature schema, formula tests, availability timestamps, lineage report | Any feature source is later than issue time |
| G4 ML | E0–E4 baselines, blocked splits, calibration and uncertainty intervals | No comparison against spread-only or random row split |
| G5 safety | OOD/abstention coverage-risk, retained performance, missing-data fallback | UI displays confident probability after abstention |
| G6 product | API contract, database migration, replay fixture, frontend trust states | API and UI disagree on status/provenance |
| G7 release | clean-machine reproduction, Docker health, rollback pointer, demo runbook | Demo depends on live weather or undocumented manual step |

## Team operating rhythm

The ML/Data person owns the data and model contracts; the Backend person owns service and persistence contracts; the Frontend person owns the typed UI state machine; the Research person owns claim scope, evaluation, judge QA and release evidence. Every change to a schema requires a small migration note and an integration replay. Negative experimental results are preserved rather than deleted.

---


**Scope.** This blueprint turns the approved SIH26079 research concept into a buildable, reproducible and judge-friendly platform. It does not redesign the science. The platform predicts when a medium-range NWP forecast is likely to fail materially, using issue-time-safe inputs, a versioned Bust Label Engine, a calibrated tabular core, optional spatial/temporal modules, OOD detection, abstention, analog context, an API and a dashboard.


**Non-negotiable boundary.** The first implementation is a public-proxy prototype using GEFS or WeatherBench 2 with ERA5/approved observations. NCMRWF/NEPS is treated as a future operational-validation source only if a paired historical archive, metadata, verification source and permission are obtained. No code path or dashboard label may imply NCMRWF validation before that gate is passed. [VERIFIED EXTERNAL] [UNKNOWN]


**Recommended architecture in one sentence.** Use a local-first monorepo with a React/TypeScript frontend, a FastAPI API, a Python ML package, PostgreSQL for metadata and predictions, Zarr/NetCDF in local or S3-compatible object storage for fields, Parquet for feature/label tables, a filesystem model registry initially, Docker Compose for reproducibility, and cron or a simple scheduler for ingestion; add Redis, a worker and a vector index only when their experiments or latency requirements justify them.


## 1. Project in one page

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 1 operational rather than descriptive: Project in one page. |
| **Owner** | Product lead + research lead |
| **Inputs** | Approved research strategy, claim sheet, user stories |
| **Outputs** | Scope sheet, architecture ADR, one-page flow, risk register |
| **Files / folders** | `docs/01_PROJECT_OVERVIEW.md; configs/claim_scope.yaml` |
| **Command** | `make scope-check` |
| **Test** | Scope review: every input/output and non-goal is named |
| **Failure and fallback** | Stop if current NCMRWF validation or live truth is implied |
| **Definition of done** | G0 scope accepted. The evidence is committed or stored with a checksum and linked from the phase report. |


| Question | Answer |

|---|---|

| What are we building? | Forecast-Bust Sentinel: an advisory system that predicts future forecast failure risk for Day 1–Day 10, then shows where, when and how severe the failure may be. |

| Who uses it? | Meteorological analysts, emergency planners, researchers, students and judges evaluating the scientific workflow. |

| Input | Forecast cycles and ensemble members, issue/valid timestamps, variables, region masks, static geography, historical verification and optional multi-model/analog data. |

| AI role | Learn a meta-forecast of the probability that the forecast error will exceed a documented threshold; it does not generate the weather forecast. |

| Backend role | Validate requests, load approved artifacts, orchestrate features/inference/calibration/OOD, store prediction metadata and expose stable REST responses. |

| Database role | Store metadata, forecast-run records, predictions, risk-object summaries, model versions, provenance, jobs, feedback and audit records; never store massive multidimensional fields. |

| Frontend role | Let a user select region/variable/lead, display risk, severity, map, trajectory, analogs, provenance and trust state, and make abstention impossible to miss. |

| Training location | Local workstation or low-cost compute using a frozen public-proxy manifest; optional GPU only for experimental deep models. |

| Model location | Versioned artifact bundle in object storage or local `artifacts/models/`, referenced by a registry record. |

| NCMRWF claim | Not made until paired historical NCMRWF data is actually available and evaluated. |



Complete flow:


```text
DATA SOURCE
  ↓
INGESTION SERVICE
  ↓
RAW OBJECT STORAGE + MANIFEST
  ↓
VALIDATION / ALIGNMENT
  ↓
LABEL ENGINE + FEATURE PIPELINE
  ↓
PARQUET FEATURE STORE
  ↓
TRAINED MODEL + CALIBRATION + OOD ARTIFACTS
  ↓
PREDICTION
  ↓
POST-CALIBRATION / OOD / ABSTENTION
  ↓
RISK MAP + TRAJECTORY + ANALOG CONTEXT
  ↓
POSTGRES METADATA + OBJECT STORAGE PRODUCTS
  ↓
FASTAPI
  ↓
REACT DASHBOARD
  ↓
USER
```


## 2. Complete system architecture

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 2 operational rather than descriptive: Complete system architecture. |
| **Owner** | Lead architect |
| **Inputs** | Scope sheet and system constraints |
| **Outputs** | Component diagram, service boundaries, dependency table |
| **Files / folders** | `docs/03_ARCHITECTURE.md; docs/adr/ADR-001-modular-monolith.md` |
| **Command** | `make architecture-check` |
| **Test** | Review import boundaries and service ownership |
| **Failure and fallback** | Remove unnecessary service or queue |
| **Definition of done** | No component lacks owner, input or fallback. The evidence is committed or stored with a checksum and linked from the phase report. |


The system is divided into six planes so that training, serving and data movement are not accidentally mixed. The **data plane** ingests and validates fields; the **science plane** aligns forecasts, generates labels and features, trains and evaluates; the **serving plane** performs inference; the **safety plane** calibrates, detects OOD and can abstain; the **product plane** exposes API and UI; the **evidence plane** preserves provenance, metrics, audit and replay artifacts.


```text
┌──────────────────────────────────┐
                         │  Public forecast / truth sources │
                         │ GEFS | WeatherBench 2 | ERA5    │
                         └────────────────┬─────────────────┘
                                          │
                         ┌────────────────▼─────────────────┐
                         │ Ingestion + QC + manifest service │
                         └────────────────┬─────────────────┘
                                          │
              ┌───────────────────────────▼─────────────────────────┐
              │ Object storage: raw → validated → processed fields  │
              │ Zarr/NetCDF fields; Parquet tables; checksums       │
              └───────────────────────────┬─────────────────────────┘
                                          │
              ┌───────────────────────────▼─────────────────────────┐
              │ Alignment + Bust Label Engine + Feature Pipeline    │
              └───────────────────────────┬─────────────────────────┘
                                          │
              ┌───────────────────────────▼─────────────────────────┐
              │ ML training/evaluation: baselines → GBM → safety    │
              │ model registry + calibration + OOD + ablations      │
              └───────────────────────────┬─────────────────────────┘
                                          │ approved artifact bundle
                         ┌────────────────▼─────────────────┐
                         │ FastAPI service                  │
                         │ validation → data access         │
                         │ inference → calibration → OOD    │
                         │ risk objects → provenance        │
                         └─────┬───────────────┬────────────┘
                               │               │
                  ┌────────────▼───────┐ ┌───▼───────────────────┐
                  │ PostgreSQL          │ │ Object storage/cache  │
                  │ metadata/predictions│ │ maps/analogs/reports │
                  └────────────┬───────┘ └────────────┬───────────┘
                               └───────────────┬───────┘
                                               ▼
                                   React/TypeScript dashboard
```


| Component | MVP implementation | Evolution trigger |

|---|---|---|

| Frontend | React + TypeScript + Vite; Leaflet or MapLibre; ECharts/Recharts | Move to Next.js only if routing/SSR/auth needs it. |

| API server | FastAPI in one backend container | Split ML service only when model load or concurrency requires isolation. |

| ML inference | Python module loaded by API process; immutable artifacts | Separate inference worker/service after measured latency or memory pressure. |

| Ingestion | Python CLI + cron/GitHub Actions/cloud scheduler | Queue worker after retries or source count exceeds one process. |

| Database | PostgreSQL for structured metadata and products | Managed Postgres for multi-user deployment. |

| Cache | File/object cache first; Redis optional | Redis when repeated map/trajectory requests cause measurable latency. |

| Vector search | FAISS/Lance local index optional | Managed vector service only if archive size and concurrency require it. |

| Monitoring | Structured logs + health endpoints + JSON metrics | Prometheus/Grafana or hosted monitoring after deployment scale. |



## 3. Data source → user complete flow

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 3 operational rather than descriptive: Data source → user complete flow. |
| **Owner** | Data engineer |
| **Inputs** | Raw source manifests and forecast/truth products |
| **Outputs** | Lineage record from source to UI |
| **Files / folders** | `metadata/lineage_schema.json; docs/05_DATA_PIPELINE.md` |
| **Command** | `make trace-replay CASE_ID=...` |
| **Test** | Replay one case and compare checksums |
| **Failure and fallback** | Use last-successful replay; mark current data delayed |
| **Definition of done** | Every output has lineage. The evidence is committed or stored with a checksum and linked from the phase report. |


| Step | Exact operation | Synchronous? |

|---|---|---|

| 1. Detect | A scheduled job checks whether a new forecast cycle or replay case exists. |

| 2. Acquire | The downloader retrieves only declared files, stores the source URL and retrieval timestamp, and never executes downloaded content. |

| 3. Validate | The validator checks checksum, file type, dimensions, timestamps, units, grid, member count and duplicate status. |

| 4. Store raw | The immutable file goes under `raw/{source}/{model_version}/{issue_date}/{cycle}/`; a `data_object` manifest records status. |

| 5. Align | The alignment job joins issue time, valid time and lead, regrids only with a declared method, and makes accumulation windows comparable. |

| 6. Verify | Historical truth is fetched or read from cache for valid times. Verification is never made available to the live feature function. |

| 7. Label | The versioned label engine computes normalized errors, spatial/object handling, severity, ambiguity and label confidence. |

| 8. Feature | The feature job computes only issue-time predictors and writes a versioned Parquet table with availability timestamps. |

| 9. Train | A research-triggered command loads a frozen split manifest, fits baselines/core/safety layers and writes an evidence bundle. |

| 10. Register | A model registry records data version, feature schema, label version, split, code commit, metrics and artifact checksums. |

| 11. Live/replay request | The API identifies the forecast run, obtains cached fields and computes any missing issue-time features. |

| 12. Infer | The model returns raw score; calibration maps it to a probability; OOD computes a status; abstention may suppress the probability. |

| 13. Enrich | The risk engine builds region/grid products, the trajectory service builds leadwise risk, and the analog service retrieves eligible history. |

| 14. Persist/respond | Prediction metadata goes to Postgres and large products to object storage. FastAPI returns a schema with provenance, trust state and claim scope. |

| 15. Render | The frontend renders map, trajectory, analogs, evidence, errors and trust state; it never invents a value missing from the response. |



## 4. Data sources

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 4 operational rather than descriptive: Data sources. |
| **Owner** | Research/data lead |
| **Inputs** | Dataset candidates, source terms, pilot constraints |
| **Outputs** | Frozen source registry and dataset decision tree |
| **Files / folders** | `configs/data_sources.yaml; metadata/licenses/` |
| **Command** | `python scripts/check_sources.py` |
| **Test** | Verify source, access, variables, cycles, lead and truth compatibility |
| **Failure and fallback** | Switch to another approved proxy; never invent NCMRWF data |
| **Definition of done** | Manifest is approved. The evidence is committed or stored with a checksum and linked from the phase report. |


The research source of truth is public-proxy-first. Dataset availability and exact configuration must be frozen in `configs/data_sources.yaml` and the corresponding manifest. Approximate sizes below are planning estimates, not acquisition guarantees; the first pilot must measure actual bytes.


| Dataset | Purpose / type | Resolution and variables | Cycles / range | Training | Inference | Verification | Limitations / fallback |

|---|---|---|---|---|---|---|---|

| GEFS | Primary public ensemble forecast proxy; gridded forecast fields. [1] | Use bounded India domain; start with Z500 and T2m; add precipitation only after accumulation alignment. | Use documented public cycles and available archive/reforecast period; freeze exact range in manifest. | Yes | Yes for replay/live if current files accessible | No; verify against ERA5/observations | Archive/configuration and licensing must be checked. Fallback to WB2/IFS subset. |

| ERA5 | Historical reanalysis verification proxy. [2] | Hourly or aggregated fields depending on product; variables must match forecast. | Historical; exact subset requested from CDS and cached. | No as predictor for future target; yes as historical truth | No in live issue-time feature path | Yes, with representativeness caveat | Not a perfect observation; precipitation sensitivity required. |

| WeatherBench 2 | Benchmark/curated forecast and truth data. [3] | Documented benchmark variables/resolutions; use only supported paired products. | Frozen benchmark snapshots. | Yes | Replay only | Yes where paired | Benchmark conventions may not match NCMRWF operations. |

| NCMRWF/NEPS | Target operational partner validation, not assumed public. [4] | Use only after paired archive and metadata are granted. | Unknown until partner agreement. | Conditional | Conditional | Conditional | Hard gate; no historical-validation claim before access. |

| IMD | Potential India observations/grids for localized verification. | Exact product, resolution and license require confirmation. | Unknown. | Conditional | No unless live access is authorized | Potentially yes | Treat as UNKNOWN until access and terms are documented; fallback ERA5/satellite sensitivity. |

| GFS | Optional deterministic or multi-system comparator. [5] | Common grid/variables required; collocate before disagreement. | Public cycles subject to archive. | Optional | Optional | No | Do not use a later run as a predictor of an earlier issue. |

| IFS/AIFS open data | Optional comparator where terms and variables permit. [6] | Use only public/open subset and matching grid. | Rolling/open archive limits may apply. | Optional | Optional | No | Do not overstate archive depth; fallback to single-system features. |

| Satellite products | Optional precipitation/cloud verification sensitivity. | Variable-specific swath/grid and latency. | Historical/live access depends on product. | Optional | Optional | Potentially | Different errors and missingness; use sensitivity study, not silent substitution. |

| Static geography | Topography, land/sea mask, coordinates. | Static grid/region features. | Immutable. | Yes | Yes | No | Version static raster and regridding. |



## 5. Data acquisition architecture

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 5 operational rather than descriptive: Data acquisition architecture. |
| **Owner** | Data engineer |
| **Inputs** | Source registry and downloader rules |
| **Outputs** | Downloader, retry policy, folder layout, job state |
| **Files / folders** | `ingestion/; scripts/ingest.py; metadata/ingest_runs/` |
| **Command** | `python -m ingestion.cli run --source ge_fs --date YYYY-MM-DD` |
| **Test** | Run twice and prove idempotency |
| **Failure and fallback** | Retry then quarantine; show delayed status |
| **Definition of done** | No duplicate object and checksum recorded. The evidence is committed or stored with a checksum and linked from the phase report. |


| Method | How it works | Use for SIH | Risk |

|---|---|---|---|

| A — manual | Researcher downloads pilot files and records manifest. | First 1–2 days only. | Not reproducible at scale; human omissions. |

| B — Python downloader | CLI reads YAML, downloads, retries, checksums and writes manifest. | Recommended default. | Source API changes; require tests. |

| C — API | Use CDS or public API credentials with environment variables. | Use where official API is available. | Credentials/quotas; never commit keys. |

| D — scheduled ingestion | cron/GitHub Actions/cloud scheduler runs downloader. | Use for replay/live demonstration. | Scheduler failure; show last-success time. |

| E — cloud object storage | Store immutable source-derived artifacts in S3/GCS/Azure/MinIO. | Use after local pilot or for team sharing. | Cost and permissions. |

| F — local storage | Filesystem stores pilot fields and artifacts. | Best for zero-cost prototype. | Disk capacity and backup. |

| G — hybrid | Local code + object storage + managed Postgres when needed. | Recommended evolution path. | Data movement and credentials. |



**Recommended acquisition path.** Start with Method B plus local storage. Add a scheduler only after the manual pilot passes QC. Use cloud object storage only when local disk or collaboration becomes the bottleneck. Do not build a distributed ingestion platform for one forecast source.


```text
data/
├── raw/{source}/{model_version}/{issue_date}/{cycle}/
├── validated/{source}/{date}/
├── processed/fields/{source}/{year}/
├── features/{feature_schema_version}/{split}/
├── labels/{label_version}/{truth_source}/
├── splits/{split_manifest_version}/
├── predictions/{model_version}/{issue_date}/
├── embeddings/{embedding_version}/
├── models/{model_version}/
├── evaluations/{run_id}/
└── metadata/{manifests,licenses,schemas}/
```


## 6. Why Zarr / NetCDF / Parquet / database?

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 6 operational rather than descriptive: Why Zarr / NetCDF / Parquet / database?. |
| **Owner** | Data engineer |
| **Inputs** | Pilot fields, access patterns and sizes |
| **Outputs** | Storage decision, chunk plan and migration rules |
| **Files / folders** | `docs/06_DATA_SCHEMA.md; configs/chunks.yaml` |
| **Command** | `python scripts/storage_roundtrip.py` |
| **Test** | Round-trip a field, feature table and model artifact |
| **Failure and fallback** | Use NetCDF/local disk fallback |
| **Definition of done** | Read/write/checksum round-trip passes. The evidence is committed or stored with a checksum and linked from the phase report. |


| Technology | Put here | Do not put here | Reason |

|---|---|---|---|

| NetCDF | Portable single-file scientific exchange, source snapshots and final case products. | High-frequency feature tables or database rows. | Excellent metadata/interoperability; less convenient for many small cloud reads. |

| Zarr | Chunked multidimensional forecast/truth fields and spatial products. | Users, run metadata or arbitrary relational joins. | Efficient region/lead/chunk reads and object-storage layout. [7] |

| Parquet | Feature rows, labels, metrics, split manifests and tabular exports. | Large gridded fields. | Columnar, typed, efficient for ML and analytics. |

| CSV | Small inspection exports and human-readable tables. | Primary dataset or spatial field archive. | Easy but lossy/slow/weakly typed. |

| PostgreSQL | Metadata, users if required, forecast runs, predictions, registry, audit and job status. | Raw multidimensional weather arrays or embeddings at scale. | Relational integrity and indexed queries. |

| Object storage | Raw/validated/processed fields, model bundles, maps, reports and backups. | Hot transactional joins. | Cheap immutable artifact storage. |

| Vector index | Eligible analog embeddings and metadata pointer. | Truth fields or unfiltered event history. | Similarity search; must enforce event/time exclusion. |



## 7. Local vs cloud vs hybrid

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 7 operational rather than descriptive: Local vs cloud vs hybrid. |
| **Owner** | Tech lead + data lead |
| **Inputs** | Local/cloud options and security limits |
| **Outputs** | Chosen deployment topology, cost ceiling and rollback |
| **Files / folders** | `docs/17_DEPLOYMENT.md; docs/adr/ADR-002-deployment.md` |
| **Command** | `make deployment-plan` |
| **Test** | Threat/cost/recovery review |
| **Failure and fallback** | Use local replay until cloud is justified |
| **Definition of done** | Topology fits student budget and skills. The evidence is committed or stored with a checksum and linked from the phase report. |


| Option | Architecture | Cost | Difficulty | Performance / reliability | SIH suitability |

|---|---|---|---|---|---|

| 1. Everything local | Browser + API + Postgres Docker + local fields + local models. | ₹0 beyond hardware/disk. | Low. | Good for pilot; weak sharing/backup. | Best starting point. |

| 2. Local dev + cloud deployment | Local research; container API and frontend hosted. | Low. | Medium. | Good demo access; data egress must be managed. | Recommended SIH path. |

| 3. Cloud ML + cloud backend | Cloud storage/training/DB/API. | Moderate/high. | High. | Scalable but cost and credentials. | Only with funding/partner. |

| 4. Local training + cloud inference | Train locally; upload approved artifacts; cloud API. | Low/moderate. | Medium. | Good if model is small; data movement limited. | Strong final demo path. |

| 5. Hybrid | Local fields + cloud API or shared object storage. | Low/moderate. | Medium. | Flexible but synchronization risk. | Use only with manifest discipline. |

| 6. GPU cloud training + CPU backend | GPU for optional deep experiment; CPU GBM serving. | Moderate. | Medium/high. | Appropriate for one experiment. | Optional. |

| 7. Containerized | Docker images for API/frontend/db. | Low. | Medium. | Reproducible. | Recommended. |

| 8. Serverless frontend + managed backend | Static frontend + hosted container/Postgres. | Low/moderate. | Medium. | Simple public demo; cold starts possible. | Good deployment evolution. |



**Recommendations.** Best for development: local-first Docker Compose. Best for training: local CPU for GBM, optional temporary GPU only for a pre-registered deep experiment. Best for demo: hosted frontend plus one containerized API with a deterministic replay dataset. Best for production pilot: container API + managed Postgres + object storage + scheduler. Best overall: Option 2/4 with a single FastAPI backend and an explicit fallback path.


## 8. Recommended development environment

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 8 operational rather than descriptive: Recommended development environment. |
| **Owner** | All leads |
| **Inputs** | OS, Python, Node, Docker and repository policy |
| **Outputs** | Pinned environments and setup script |
| **Files / folders** | `pyproject.toml; package.json; requirements*.txt; .env.example` |
| **Command** | `make bootstrap && make test` |
| **Test** | Fresh-machine setup with no undocumented dependency |
| **Failure and fallback** | Pin/remove problematic dependency |
| **Definition of done** | Clean bootstrap passes. The evidence is committed or stored with a checksum and linked from the phase report. |


| Item | Recommendation | Why |

|---|---|---|

| OS | Ubuntu 22.04/24.04 or WSL2; macOS acceptable for frontend. | Matches Python/data tooling. |

| Python | 3.11.x pinned in `.python-version`. | Stable scientific ecosystem. |

| Node | 22.x pinned for frontend. | Matches current web tooling. |

| Package managers | uv or pip/venv; pnpm for frontend. | Fast, reproducible environments. |

| Source control | Git + GitHub with protected main branch. | Review and reproducibility. |

| Containers | Docker + Compose. | Same local service topology. |

| Editors | VS Code; Jupyter only for exploration. | Team familiarity. |

| Environment | `.env.example`; secrets in local `.env` ignored by Git. | Avoid credential leakage. |

| Testing | pytest, Ruff/Black, mypy or pyright where useful, Vitest/Playwright optional. | Catches data and UI regressions. |



```text
mkdir sih26079 && cd sih26079
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pnpm install --dir frontend
cp .env.example .env
make test
make run-local
```


## 9. Complete repository structure

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 9 operational rather than descriptive: Complete repository structure. |
| **Owner** | Tech lead |
| **Inputs** | Architecture and team boundaries |
| **Outputs** | Monorepo with ownership/readme per folder |
| **Files / folders** | `CODEOWNERS; repo folders; docs/README_MAP.md` |
| **Command** | `make repo-check` |
| **Test** | Check every import and folder has purpose |
| **Failure and fallback** | Delete empty/duplicate layers |
| **Definition of done** | Owner/readme/test exists for every active folder. The evidence is committed or stored with a checksum and linked from the phase report. |


```text
sih26079/
├── frontend/                 # React/TypeScript dashboard
│   ├── src/api/              # typed API client
│   ├── src/components/       # map, cards, charts, trust states
│   ├── src/pages/            # dashboard, replay, metrics, provenance
│   └── src/types/            # response schemas
├── backend/                  # FastAPI application, not training code
│   ├── app/main.py
│   ├── api/routes/
│   ├── services/             # inference, risk, analog, provenance
│   ├── repositories/         # database/object-store access
│   └── schemas/              # Pydantic request/response models
├── ingestion/                # source adapters, retries, manifests
├── data_pipeline/            # QC, alignment, regridding, accumulation
├── labels/                   # versioned Bust Label Engine
├── features/                 # issue-safe feature transforms
├── ml/                       # model wrappers and common interfaces
├── training/                 # train/evaluate commands
├── calibration/              # Platt/isotonic/conformal experiments
├── ood/                      # distance, drift and abstention policy
├── analog/                   # embedding/index/retrieval with exclusions
├── spatial/                  # objects, maps and spatial metrics
├── temporal/                 # lead trajectories and hazard model
├── evaluation/               # metrics, bootstrap, reports
├── configs/                  # YAML configs and split manifests
├── db/                       # migrations and SQL schema
├── scripts/                  # thin reproducible CLI entry points
├── notebooks/                # exploratory only; no production logic
├── tests/                    # unit, data, leakage, API, integration
├── artifacts/                # ignored or externalized outputs
├── docs/                     # project documentation set
├── docker/                   # Dockerfiles and Compose fragments
├── infrastructure/          # optional cloud IaC after MVP
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── Makefile
├── .env.example
├── docker-compose.yml
└── README.md
```


**Folder rule.** Training code may import the ML package; backend may import the inference contract but not notebooks or training-time truth loaders. Ingestion may write manifests and raw objects but cannot write predictions. Frontend may call only typed API clients, never read the database or object storage credentials.


## 10. Backend architecture

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 10 operational rather than descriptive: Backend architecture. |
| **Owner** | Backend lead |
| **Inputs** | API requirements and model contract |
| **Outputs** | Service interfaces and repository interfaces |
| **Files / folders** | `backend/app/services/; backend/app/repositories/` |
| **Command** | `pytest tests/backend/test_boundaries.py` |
| **Test** | Mock repository and model in unit test |
| **Failure and fallback** | Keep training out of API process |
| **Definition of done** | Boundary tests pass. The evidence is committed or stored with a checksum and linked from the phase report. |


The backend is an API application plus a set of services. It is not the training script. The API server validates HTTP and authentication, the service layer orchestrates business operations, repositories read/write data, the inference module loads an approved artifact, and scheduled jobs invoke ingestion/verification/training commands outside the request path.


| Layer | Responsibilities | Not responsible for |

|---|---|---|

| API server | Routes, Pydantic validation, status codes, CORS, request IDs, rate limits. | Computing labels or training models. |

| Model inference | Load artifact by registry ID, transform safe features, return raw score. | Fetching future truth or choosing unregistered models. |

| Data access | Read forecast metadata, cached features, products and provenance. | Bypassing versioned access rules. |

| Background jobs | Ingestion, retries, delayed verification, materialized risk products, retraining proposals. | Unreviewed production model replacement. |

| ML pipeline | Alignment, labels, feature tables, train/evaluate/calibrate. | Serving user HTTP requests. |

| Storage | Postgres for structured data; object store for arrays/artifacts. | Massive arrays in relational tables. |



## 11. Backend architecture options

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 11 operational rather than descriptive: Backend architecture options. |
| **Owner** | Tech lead |
| **Inputs** | Backend options, latency and team size |
| **Outputs** | ADR choosing modular monolith |
| **Files / folders** | `docs/adr/ADR-003-backend.md` |
| **Command** | `make adr-check` |
| **Test** | Compare request flow and failure isolation |
| **Failure and fallback** | Do not split services without measurement |
| **Definition of done** | Decision includes evolution trigger. The evidence is committed or stored with a checksum and linked from the phase report. |


| Option | Request flow | Advantages | Disadvantages | Use |

|---|---|---|---|---|

| A monolith | Browser → FastAPI → in-process services → Postgres/files. | Simplest, low latency, easy local demo. | Training/inference process coupling. | MVP. |

| B FastAPI + ML module | FastAPI → typed inference module → artifact bundle. | Separates contract without network complexity. | Memory duplicated only if multiple workers. | Recommended. |

| C + worker queue | API enqueues long tasks to worker/Redis. | Ingestion/maps can be asynchronous. | Operational complexity. | Add when needed. |

| D separate ML service | API → internal HTTP/gRPC ML service. | Independent scaling and runtime. | More deployment, version and failure modes. | Later. |

| E microservices | Many independently deployed services. | Organizational scalability. | Technology soup for a student team. | Reject for MVP. |

| F cloud-native | Managed queues, containers, DB, object store. | Reliable at scale. | Cost and cloud-specific complexity. | Production evolution. |

| G hybrid | Local pipeline + hosted API or vice versa. | Flexible data movement. | Requires manifests/credentials. | Demo/partner path. |



**Chosen architecture.** Option B in a modular monolith. Separate Python packages and interfaces, one FastAPI process, optional worker introduced only for ingestion or precomputation. The API always calls an `InferenceFacade` whose inputs and outputs are stable even if the model later moves to another service.


## 12. Backend request lifecycle

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 12 operational rather than descriptive: Backend request lifecycle. |
| **Owner** | Backend lead |
| **Inputs** | HTTP request and service states |
| **Outputs** | Sequence diagram and timing budget |
| **Files / folders** | `docs/13_REQUEST_LIFECYCLE.md` |
| **Command** | `pytest tests/api/test_lifecycle.py` |
| **Test** | Mock slow DB/model and verify timeout/fallback |
| **Failure and fallback** | Return typed degraded state |
| **Definition of done** | All states are explicit. The evidence is committed or stored with a checksum and linked from the phase report. |


```text
Browser
  → HTTPS request with correlation ID
  → reverse proxy / API server
  → FastAPI route
  → Pydantic validation
  → optional auth/rate limit
  → service layer
  → repository loads forecast/product metadata
  → feature cache or issue-safe feature computation
  → model inference
  → calibration
  → OOD + abstention
  → risk/map/analog enrichment
  → provenance assembly
  → JSON response
  → frontend render
```


| Operation | Timing | Notes |

|---|---|---|

| Request validation, metadata lookup | Milliseconds | No weather-field scan if product is cached. |

| Feature computation | Milliseconds to seconds | Precompute for normal cycles; compute only missing chunks. |

| GBM inference/calibration/OOD | Milliseconds to low seconds | Load model once at process startup; use explicit artifact ID. |

| Spatial map generation | Precomputed preferred | Return object-storage URL or compact GeoJSON, not giant JSON grids. |

| Analog search | Milliseconds to seconds | Precompute embeddings/index; exclude ineligible records. |

| Ingestion | Asynchronous | Runs after new cycle detection; writes status. |

| Training/label generation | Research/offline | Never occurs in a user request. |

| Verification update | Delayed after valid time | May update retrospective status without changing issue-time prediction. |



## 13. API design

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 13 operational rather than descriptive: API design. |
| **Owner** | Backend lead |
| **Inputs** | Endpoint list and schemas |
| **Outputs** | OpenAPI contract, examples and errors |
| **Files / folders** | `backend/app/schemas/; docs/14_API.md` |
| **Command** | `make api-contract-test` |
| **Test** | Validate request/response JSON and status codes |
| **Failure and fallback** | Version endpoint or add backward-compatible field |
| **Definition of done** | Contract snapshot passes. The evidence is committed or stored with a checksum and linked from the phase report. |


All endpoints are versioned under `/v1`. Every prediction response carries `issue_time`, `valid_time`, `lead_hours`, `region_id`, `variable`, `forecast_run_id`, `model_version`, `data_version`, `feature_schema_version`, `label_version`, `training_period`, `claim_scope`, `ood`, `abstain`, and `generated_at`. A probability is `null` when the policy abstains; the UI must not substitute a confident number.


| Method/path | Purpose | Request | Response core | Errors |

|---|---|---|---|---|

| GET /health | Liveness/readiness. | None. | status, version, dependencies. | 503 if model/DB unavailable. |

| GET /models | List approved/available artifacts. | status, variable, lead optional. | model IDs, metrics, training period, approval. | 400 invalid filter. |

| GET /forecasts | List runs/replay cases. | source, issue range, region. | run IDs, cycles, availability. | 404 no run. |

| GET /forecast/{id} | Forecast metadata. | Path run ID. | source, grid, members, issue/valid coverage. | 404. |

| POST /predict | Compute risk for one selection. | Issue/valid/region/variable/lead/model optional. | Prediction envelope. | 400 schema; 409 unavailable; 503 fallback. |

| GET /risk-map | Retrieve spatial product. | run, lead, variable, region, format. | GeoJSON or signed object URL + metadata. | 404 product missing. |

| GET /risk-trajectory | Return leadwise risk. | issue, region, variable. | lead records, interval, trust state. | 422 invalid lead. |

| GET /analogs | Retrieve eligible similar cases. | query ID, k, exclusion policy. | cards with similarity/outcome/provenance. | 404 none is normal. |

| GET /explanation | Evidence, not causal story. | prediction ID. | feature contributions, analogs, reason codes. | 404. |

| GET /metrics | Research metrics. | model, split, metric optional. | metric table with CI and scope. | 403 if private. |

| GET /regions | Region catalog. | None. | IDs, names, bbox, masks. | 500 registry issue. |

| GET /variables | Supported variables. | None. | variable IDs, units, capabilities. | None. |

| GET /metadata | Data/model/claim scope. | None. | versions, licenses, periods, caveats. | None. |

| GET /model-version | Current serving model. | None. | registry record + checksum. | 503 if none. |

| GET /data-provenance | Lineage for a result. | prediction ID or run ID. | source URLs/checksums/transforms. | 404. |

| GET /calibration | Calibration artifact summary. | model/variable/lead. | method, window, validation block, diagnostics. | 404. |

| GET /ood-status | Safety status. | prediction ID. | score, class, threshold, abstain rule. | 404. |

| GET /export | Export product. | prediction/filter, format=csv\|parquet\|geojson\|netcdf. | download URL + checksum. | 400/404. |



```text
POST /v1/predict
{
  "issue_time": "2025-07-01T00:00:00Z",
  "valid_time": "2025-07-07T00:00:00Z",
  "region_id": "INDIA_CORE",
  "variable": "z500",
  "lead_hours": 144,
  "mode": "historical_replay",
  "model_version": "approved"
}

200
{
  "prediction_id": "pred_01J...",
  "bust_probability": 0.68,
  "probability_interval": [0.54, 0.79],
  "severity": {"value": 2.1, "class": "severe", "definition": "normalized_error_q95"},
  "spatial_extent": {"fraction": 0.22, "object_count": 2},
  "trajectory": [{"lead_hours": 96, "p": 0.12}, {"lead_hours": 120, "p": 0.29}, {"lead_hours": 144, "p": 0.68}],
  "ood": {"score": 0.31, "status": "UNUSUAL"},
  "abstain": false,
  "decision": "REVIEW_RECOMMENDED",
  "reason_codes": ["REVISION_ACCELERATION_HIGH", "ENSEMBLE_DISAGREEMENT_MODERATE"],
  "analog_ids": ["analog_123", "analog_456"],
  "risk_map": {"format": "geojson", "uri": "/v1/risk-map?..."},
  "model_version": "gbm-traject-v3",
  "data_version": "gefs_pilot_2025_01",
  "feature_schema_version": "features_v4",
  "label_version": "labels_v3",
  "training_period": ["2018-01-01", "2023-12-31"],
  "claim_scope": "PUBLIC_PROXY_GEFS_ERA5_REPLAY_ONLY",
  "generated_at": "2026-08-23T12:00:00Z"
}
```


**Status semantics.** `NORMAL` means supported and no alert; `UNUSUAL` means supported but far from training distribution; `OOD` means unsupported by the detector; `ABSTAIN` means the product intentionally withholds an actionable probability. `HTTP 200` may still contain `abstain=true`; this is a valid scientific result, not an API failure.


## 14. Database design

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 14 operational rather than descriptive: Database design. |
| **Owner** | Backend/data lead |
| **Inputs** | Structured entities and relationships |
| **Outputs** | Migration files, indexes, seed data and ERD |
| **Files / folders** | `db/migrations/; db/schema.sql; docs/15_DATABASE.md` |
| **Command** | `make db-reset && make db-test` |
| **Test** | Insert replay prediction and retrieve lineage |
| **Failure and fallback** | Restore dev DB from migration |
| **Definition of done** | Migration and FK tests pass. The evidence is committed or stored with a checksum and linked from the phase report. |


| Table | Important columns | Keys/indexes | Purpose |

|---|---|---|---|

| users | id UUID, email, role, created_at | PK id; unique email | Optional for private demo; anonymous read-only can be used. |

| regions | id, name, bbox, geometry_uri, version | PK id; spatial/name index | Region catalog; geometry remains in object store if large. |

| variables | id, unit, level, accumulation_window | PK id | Variable contract. |

| forecast_runs | id, source, model_version, issue_time, cycle, grid_hash, member_count, status | PK id; index source/issue_time/valid coverage | Run identity. |

| forecast_artifacts | id, run_id, uri, checksum, format, size_bytes, qc_status | PK id; FK run; unique checksum | Field pointers. |

| data_versions | id, source, manifest_uri, commit, license_uri, created_at | PK id | Immutable data snapshot. |

| predictions | id, run_id, region_id, variable_id, lead_hours, model_version, p_bust, severity, ood_status, abstain, generated_at | PK id; unique run/region/variable/lead/model; index generated_at | Served result and safety state. |

| risk_trajectories | prediction_group_id, lead_hours, p_bust, lower, upper, status | Composite key/index group | Leadwise products. |

| risk_maps | id, prediction_group_id, uri, format, checksum, object_count, area_fraction | PK id; FK group | Map metadata; large map in object storage. |

| analogs | id, prediction_group_id, source_event_id, similarity, outcome_uri, eligible_policy | PK id; index group/similarity | Auditable analog cards. |

| model_versions | id, registry_uri, feature_schema, label_version, train_period, metrics_uri, approval_state, checksum | PK id; unique checksum | Registry mirror. |

| calibration_versions | id, model_id, method, calibration_period, artifact_uri, diagnostics_uri | PK id; FK model | Calibration provenance. |

| experiments | id, run_name, config_uri, split_id, status, started_at, ended_at | PK id; index status | Experiment tracking. |

| evaluation_results | id, experiment_id, split, metric, value, lower, upper, unit | PK id; index experiment/metric | Evidence table. |

| jobs | id, type, status, idempotency_key, attempts, error, started_at, ended_at | Unique idempotency key | Ingestion/inference products. |

| audit_logs | id, actor, action, resource, request_id, created_at | PK id; index resource/time | Traceability. |



**What does not go in PostgreSQL?** Raw GRIB/NetCDF/Zarr arrays, large feature matrices, model binaries, embeddings at scale, GeoTIFF/NetCDF risk fields and reports. Store a URI, checksum, content type and schema in Postgres instead.


**Relationships.** One `data_version` has many `forecast_runs`; one run has many artifacts and predictions; each prediction belongs to one model/region/variable; a prediction group has one trajectory and zero-or-one map/analogs; model versions reference feature, label and calibration artifacts.


```text
users ───────< audit_logs
regions ──────< predictions >──── model_versions
variables ────< predictions >──── forecast_runs >──── data_versions
forecast_runs ───< forecast_artifacts
predictions ───< risk_trajectories
predictions ───< risk_maps
predictions ───< analogs
model_versions ───< calibration_versions
experiments ───< evaluation_results
```


## 15. Weather data storage

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 15 operational rather than descriptive: Weather data storage. |
| **Owner** | Data engineer |
| **Inputs** | Field sizes and retention |
| **Outputs** | Object-store prefixes, lifecycle and checksum policy |
| **Files / folders** | `configs/storage.yaml; docs/06_DATA_SCHEMA.md` |
| **Command** | `python scripts/storage_audit.py` |
| **Test** | Read region/lead chunk and export product |
| **Failure and fallback** | Use local NetCDF for tiny fixture |
| **Definition of done** | No array in Postgres. The evidence is committed or stored with a checksum and linked from the phase report. |


| Location | MVP | Cloud equivalent | Retention |

|---|---|---|---|

| local disk | `data/` on encrypted developer disk; raw immutable; derived rebuildable. | S3/GCS/Azure object prefix; server-side encryption. | Keep raw pilot and final evidence; prune rebuildable intermediates. |

| validated fields | Zarr/NetCDF with QC attributes. | Object prefix with versioned manifests. | Retain source snapshot and checksum. |

| features/labels | Parquet partitioned by source/year/lead/variable/region. | Object storage + query engine if needed. | Retain training/test tables used in paper. |

| models | Artifact directory with manifest. | Object storage + registry metadata. | Retain all promoted models and rollback candidate. |

| predictions | Postgres metadata; map arrays in object store. | Managed Postgres + object store. | Keep demo/research window; archive by policy. |



Storage alternatives: local disk is zero-cost but fragile; S3/GCS/Azure are durable but introduce credentials and egress; MinIO provides an S3-compatible local layer but adds a container. For SIH, local disk plus an optional MinIO profile is enough. Move to managed object storage only after a sharing or deployment need is demonstrated.


## 16. Feature engineering pipeline

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 16 operational rather than descriptive: Feature engineering pipeline. |
| **Owner** | ML/data lead |
| **Inputs** | Raw field and metadata schema |
| **Outputs** | Feature pipeline modules and feature registry |
| **Files / folders** | `features/registry.yaml; features/build.py` |
| **Command** | `python -m features.build --run-id RUN` |
| **Test** | Compare formula output with hand-calculated fixture |
| **Failure and fallback** | Drop feature block if availability uncertain |
| **Definition of done** | Feature table schema passes. The evidence is committed or stored with a checksum and linked from the phase report. |


The feature pipeline has one hard interface: `build_features(issue_time, run_id, target, feature_schema_version)` must be callable without any verifying-time data. The label pipeline has a different interface and is allowed to read future truth only offline. The feature builder writes `availability_time` for every value and fails if it is later than `issue_time`.


| Feature block | Formula / implementation | Input | Issue-time availability | Leakage risk |

|---|---|---|---|---|

| Ensemble mean | μ = mean(x₁…xₙ) | Members at same issue/valid/lead | Yes | Missing members must be explicit. |

| Spread | s = sample std(x₁…xₙ) | Members | Yes | Do not compute from verifying truth. |

| Quantiles | q10, q25, median, q75, q90 | Members | Yes | Stable only with enough members. |

| Skew/range | third standardized moment; max−min | Members | Yes | Sensitive to outliers; winsorize only by train rule. |

| Revision | Δₖ = μ(I)−μ(I−k) for same valid target | Current and earlier archived runs | Yes if earlier run exists | Later cycles are forbidden. |

| Acceleration | a = Δ₆h−(Δ₁₂h−Δ₆h) | Earlier cycle revisions | Yes | Archive gaps must be recorded. |

| Member consistency | fraction within κ of μ | Members | Yes | κ fixed in config. |

| Regime | phase/flags/probabilities derived from issue-time history | Historical-safe regime inputs | Yes | No future index updates. |

| Analog | top-k similarity, distance, eligible bust rate | Prior archive only | Yes | Same event/time exclusion mandatory. |

| Disagreement | \|μ_systemA−μ_systemB\| after common grid | Simultaneous systems | Yes | No later run; optional. |

| Static geography | orography, coast fraction, coordinates | Versioned static grid | Yes | Regridding versioned. |

| Lead/season | lead hours, month/season cyclic encoding | Timestamp | Yes | No target season statistics. |

| OOD input | robust distance/drift/missingness score | Feature vector + train reference | Yes | Threshold fit only on train/validation. |



**Spatial examples versus regional examples.** A regional example aggregates members over a fixed region mask and predicts one label per variable/lead. A spatial example retains a patch/grid index and predicts a local label; it must use spatial or neighborhood metrics and event-aware grouping. Start regionally for the MVP, then add spatial objects when labels and compute are stable.


## 17. Bust Label Engine

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 17 operational rather than descriptive: Bust Label Engine. |
| **Owner** | Research/data lead |
| **Inputs** | Aligned forecast/truth and label policy |
| **Outputs** | Label engine, schema, sensitivity report |
| **Files / folders** | `labels/engine.py; labels/config.yaml; docs/07_LABELING_PROTOCOL.md` |
| **Command** | `python -m labels.build --version labels_v1` |
| **Test** | Re-run labels from checksums and compare |
| **Failure and fallback** | Quarantine ambiguous labels; do not force binary |
| **Definition of done** | Hash and threshold provenance match. The evidence is committed or stored with a checksum and linked from the phase report. |


The label engine is a first-class versioned component. It is an offline process: forecast + future verification → error → training-only normalization → displacement handling → severity/ambiguity → label. It must produce both binary/ordinal outputs and the continuous normalized error so that the team can test whether a binary threshold is hiding useful information.


```text
forecast(I,V,r,v) + truth(V,r,v)
        ↓
variable-aware error E
        ↓
training-only median/IQR or standard scale by region × season × lead
        ↓
optional regime conditioning and shrinkage
        ↓
neighborhood/object displacement check
        ↓
severity + label confidence + ambiguity
        ↓
q90/q95/q97.5/q99 sensitivity
        ↓
label_versioned output
```


| Choice | Definition | Use | Risk |

|---|---|---|---|

| Fixed threshold | Absolute error > domain threshold. | Interpretability sanity check. | Unfair across lead/region/season. |

| Global percentile | Error above overall q95. | Quick baseline. | Mixes regimes and leads. |

| Normalized q95 | Error normalized by training-only region/season/lead scale, then above q95. | Primary recommendation. | Sparse strata require pooling. |

| Regime-conditioned q95 | Threshold conditional on regime when sample size allows. | Sensitivity/conditional product. | Regime estimation uncertainty. |

| Object/neighborhood | Mismatch after allowing displacement radius or object matching. | Spatial precipitation/cyclone extension. | More parameters and label ambiguity. |

| Continuous severity | Predict normalized error; derive thresholds later. | Low-data/sensitivity fallback. | Harder operational message. |



**Primary protocol.** Start with Z500 and T2m, India domain tiles, 24-hour leads through Day 10, and all archived cycles for a common valid time. Verify against ERA5/approved observations. Use absolute error for scalar fields; use an object/neighborhood metric for precipitation. Normalize by training-only region × season × lead robust scale; use q95 as the primary threshold, q90/q97.5/q99 as sensitivity. Mark values near the threshold as `AMBIGUOUS`; retain them for sensitivity and calibration but exclude them from the primary binary training set. Record `label_confidence` based on truth source, missingness and distance/representativeness sensitivity.


**Outputs.** `bust_label`, `severity`, `normalized_error`, `spatial_extent`, `first_failure_lead`, `label_confidence`, `ambiguity_flag`, `truth_source`, `threshold_parameters`, `label_version`, and input checksums. Store the exact training window used to estimate every threshold. Never fit a q95 threshold using validation/test truth.


## 18. Leakage prevention

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 18 operational rather than descriptive: Leakage prevention. |
| **Owner** | ML/data lead |
| **Inputs** | Feature lineage and split manifest |
| **Outputs** | Leakage assertions and CI tests |
| **Files / folders** | `tests/leakage/; metadata/feature_lineage.json` |
| **Command** | `pytest tests/leakage -q` |
| **Test** | Inject future source and ensure build fails |
| **Failure and fallback** | Block promotion |
| **Definition of done** | Zero leakage failures. The evidence is committed or stored with a checksum and linked from the phase report. |


Leakage is a hard engineering gate. A build cannot produce a promoted model if any leakage test fails. The feature table must include timestamps for source availability, and the split manifest must be immutable before model tuning.


| Leakage type | Prevention | Automated test |

|---|---|---|

| Future observation | Truth fields are available only in label job; feature builder accepts no truth path. | Inject a truth file and assert feature output is byte-identical. |

| Future forecast run | Revision features only query cycles strictly earlier than current issue. | For each row assert all source_issue_time ≤ issue_time. |

| Target leakage | No normalized error, label, severity or post-valid-time field in predictors. | Schema denylist + feature lineage test. |

| Calibration leakage | Calibration fit on a later calibration block, not training/test. | Artifact records calibration rows; overlap test fails. |

| Analog leakage | Exclude same event, same valid-time neighborhood and same issue lineage. | Synthetic same-event exclusion test must return no hit. |

| Split leakage | Group all rows from coherent event and buffers together. | Assert event IDs do not cross splits. |

| Model-version leakage | Version is explicit; post-upgrade block is held out. | Assert version/time holdout matches manifest. |

| Preprocessing leakage | Scalers/thresholds fitted on training only. | Compare fit row IDs against validation/test. |

| Spatial leakage | Neighboring grid cells from same event grouped where appropriate. | Spatial event grouping test. |



```text
def assert_issue_safe(row):
    assert row.feature_availability_time <= row.issue_time
    assert row.max_source_issue_time <= row.issue_time
    assert row.truth_source_used_for_features is None
    assert row.calibration_fit_id not in row.train_fit_ids
    assert row.analog_event_id not in row.excluded_event_ids
```


## 19. Training dataset generation

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 19 operational rather than descriptive: Training dataset generation. |
| **Owner** | ML/data lead |
| **Inputs** | Raw/aligned/label/feature contracts |
| **Outputs** | Versioned dataset builder and manifest |
| **Files / folders** | `data_pipeline/dataset.py; configs/splits/` |
| **Command** | `python -m data_pipeline.make_dataset --version DS_V1` |
| **Test** | Key uniqueness, missingness and row-count audit |
| **Failure and fallback** | Quarantine invalid rows and record reason |
| **Definition of done** | Dataset reproduces. The evidence is committed or stored with a checksum and linked from the phase report. |


One row is one forecast issue for one valid time, lead, region/patch, variable and model version. The target is created only after the forecast’s valid time, then joined back to the issue-time features by a stable key.


```text
row_key = (source, model_version, issue_time, valid_time, lead_hours, region_id, variable)

identifiers = {issue_time, valid_time, lead_hours, region_id, variable, cycle, model_version}
features = {ensemble_stats, revisions, regime, optional_analog, optional_disagreement, static}
targets = {bust_label, severity, spatial_extent, first_failure_lead, label_confidence}
provenance = {data_version, feature_schema_version, label_version, source_uri, checksums, availability_times}
```


For a regional row, ensemble members are aggregated over a fixed region mask and the label is regional. For a spatial row, the same issue/valid/lead may produce multiple patch rows; the split unit remains the event or forecast run, not an arbitrary patch. For a multi-lead trajectory, either use one row per lead with a shared model plus lead input or one grouped sequence object; do not mix future lead outcomes into a current lead’s features.


## 20. Train / validation / test

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 20 operational rather than descriptive: Train / validation / test. |
| **Owner** | Research lead |
| **Inputs** | Dataset version and events |
| **Outputs** | Split files for train/validation/test/event/region/OOD/version |
| **Files / folders** | `configs/splits/split_manifest_v1.json` |
| **Command** | `python scripts/validate_splits.py` |
| **Test** | Check no event/time/version overlap |
| **Failure and fallback** | Change grouping or narrow claims |
| **Definition of done** | Split audit passes. The evidence is committed or stored with a checksum and linked from the phase report. |


| Split | Definition | Use |

|---|---|---|

| TRAIN | Earliest contiguous issue-time block; fit thresholds, preprocessing, model and reference distribution. | Model fitting only. |

| VALIDATION | Later contiguous block; tune small search, select thresholds, fit calibration/OOD policy. | Model decisions; not final reporting. |

| TEST | Final untouched issue-time block. | Primary score and CI. |

| EVENT HOLDOUT | Entire cyclone/monsoon/extreme event groups held out. | Generalization to unseen coherent episodes. |

| REGION HOLDOUT | One or more regions excluded from training. | Geographic transfer. |

| OOD HOLDOUT | Rare regimes/tails or deliberately shifted feature support. | Safety behavior. |

| MODEL-VERSION HOLDOUT | Post-upgrade or later version block. | Drift robustness. |



Never use a naive random row split. A single event can create many rows across lead, region and cycle; random splitting leaks synoptic structure. Use block-level or event-level bootstrap, not independent-cell bootstrap, for uncertainty.


## 21. ML training pipeline

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 21 operational rather than descriptive: ML training pipeline. |
| **Owner** | ML lead |
| **Inputs** | Frozen feature table and registry |
| **Outputs** | Training runner with stages and artifacts |
| **Files / folders** | `training/run.py; configs/train/` |
| **Command** | `python -m training.run --config configs/train/gbm.yaml` |
| **Test** | Run dry-run on fixture and full pilot |
| **Failure and fallback** | Stop before deployment on failed stage |
| **Definition of done** | Stage artifacts exist. The evidence is committed or stored with a checksum and linked from the phase report. |


| Step | What happens | Artifact |

|---|---|---|

| 1 load | Read frozen dataset version and manifest. | Run config. |

| 2 validate schema | Check dtypes, units, key uniqueness and missingness. | Validation report. |

| 3 remove invalid | Drop or quarantine rows according to declared policy. | Quarantine table. |

| 4 verify leakage | Run all timestamp, split, analog and target tests. | Pass/fail report. |

| 5 split | Apply frozen temporal/event/version manifest. | Split IDs. |

| 6 baseline | Compute climatology, persistence and spread-only. | Baseline metrics. |

| 7 logistic | Fit regularized logistic regression. | Model + metrics. |

| 8 GBM | Fit LightGBM/XGBoost with class weighting. | Core model. |

| 9 tune | Small pre-registered validation search. | Config + validation table. |

| 10 calibrate | Fit Platt/isotonic on later calibration subset. | Calibration artifact. |

| 11 evaluate | Run test only after freeze. | CI metric report. |

| 12 OOD | Fit detector/reference and stress-test. | OOD artifact. |

| 13 abstention | Choose coverage-risk operating point. | Policy artifact. |

| 14 analog | Build/query eligible index and test value. | Index + cards. |

| 15 advanced | One optional model matched to data/compute. | Experimental artifact. |

| 16 ablation | Remove one block at a time. | Ablation matrix. |

| 17 final selection | Apply selection gates. | Approval decision. |

| 18 save | Write complete artifact bundle. | Model directory. |

| 19 register | Create registry record and checksum. | Registry entry. |

| 20 deploy | Load only approved version. | Serving health check. |



## 22. Baseline models

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 22 operational rather than descriptive: Baseline models. |
| **Owner** | ML lead |
| **Inputs** | Safe features and split manifest |
| **Outputs** | E0–E4 baseline table |
| **Files / folders** | `training/baselines.py; reports/baselines/` |
| **Command** | `python -m evaluation.baselines --split test` |
| **Test** | Compare all baselines with block CIs |
| **Failure and fallback** | Report negative result |
| **Definition of done** | Spread-only comparison exists. The evidence is committed or stored with a checksum and linked from the phase report. |


| Baseline | Implementation | Why necessary |

|---|---|---|

| Climatology | Training-period bust rate by region/season/lead. | Measures whether model learns more than prevalence. |

| Persistence | Previous-issue risk or previous-run score with only earlier data. | Tests temporal persistence. |

| Spread-only | Thresholded spread or logistic score using only spread/statistics. | Direct ensemble baseline; central novelty test. |

| Logistic | Regularized linear probability model over safe features. | Interpretable nonlinear-free comparator. |

| GBM | LightGBM/XGBoost over tabular blocks. | Practical nonlinear core. |

| Final model | GBM plus only feature/safety blocks that survive ablation. | Research contribution must be incremental. |



## 23. Model training technologies

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 23 operational rather than descriptive: Model training technologies. |
| **Owner** | ML lead |
| **Inputs** | Baseline results and safe features |
| **Outputs** | Core model comparison and tuning record |
| **Files / folders** | `configs/models/; training/gbm.py` |
| **Command** | `python -m training.fit_gbm --config ...` |
| **Test** | Small pre-registered search only |
| **Failure and fallback** | Ship simpler baseline |
| **Definition of done** | No test tuning. The evidence is committed or stored with a checksum and linked from the phase report. |


| Candidate | Decision | Reason / rejection rule |

|---|---|---|

| LightGBM/XGBoost | Primary core. | Strong tabular interactions, CPU-friendly, fast; retain only if it beats baselines. |

| CatBoost | Secondary check only if categorical handling is useful. | Avoid duplicate tuning burden. |

| Random Forest | Sanity comparator, not final default. | Robust but often less sharp/calibratable for this task. |

| Neural network | Optional small MLP/temporal encoder. | Use only if data volume supports it and GBM ceiling is reached. |

| Transformer | Future/optional trajectory model. | High data/compute and leakage complexity. |

| GNN | Optional spatial model. | Use only if graph definition and spatial labels are defensible. |

| Foundation embedding | Optional representation/OOD/analog input. | Prior art exists; must prove transfer value. |

| Advanced weather model | Not required. | Forecast replacement is outside target and overengineers the MVP. |



## 24. Model artifacts

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 24 operational rather than descriptive: Model artifacts. |
| **Owner** | MLOps lead |
| **Inputs** | Approved model and calibration/OOD artifacts |
| **Outputs** | Artifact bundle schema/checksums |
| **Files / folders** | `models/{version}/; metadata/artifacts/` |
| **Command** | `python scripts/validate_artifact.py models/V` |
| **Test** | Load/reload and reproduce prediction |
| **Failure and fallback** | Rollback pointer |
| **Definition of done** | Artifact evidence complete. The evidence is committed or stored with a checksum and linked from the phase report. |


```text
artifacts/models/{model_version}/
├── model.txt or model.pkl
├── model_schema.json
├── feature_schema.json
├── label_schema.json
├── calibration.pkl
├── ood_reference.pkl
├── abstention_policy.json
├── config.yaml
├── metrics.json
├── split_manifest.json
├── training_metadata.json
├── source_manifest.json
├── environment.lock
└── checksums.sha256
```


The metadata must include model version, data version, training period, issue/valid coverage, features, transformations, hyperparameters, random seed, metrics with confidence intervals, calibration window, OOD thresholds, approval state, code commit and claim scope. A model without this bundle cannot be served.


## 25. Model registry / MLOps

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 25 operational rather than descriptive: Model registry / MLOps. |
| **Owner** | MLOps/research lead |
| **Inputs** | Runs, configs and evidence |
| **Outputs** | Registry, promotion and rollback workflow |
| **Files / folders** | `registry/registry.json; docs/18_MLOPS.md` |
| **Command** | `python scripts/promote_model.py --candidate V` |
| **Test** | Require all gates and approval |
| **Failure and fallback** | Reject/retain current model |
| **Definition of done** | Promotion is auditable. The evidence is committed or stored with a checksum and linked from the phase report. |


| Option | Advantages | Disadvantages | Decision |

|---|---|---|---|

| Filesystem registry | Zero cost, transparent, works with Git manifests. | Manual promotion. | MVP default. |

| MLflow | Tracks runs, params, artifacts and stages. | Extra service/DB if fully deployed. | Optional after first reproducible run. |

| Cloud registry | Managed access/rollback. | Cost/vendor lock-in. | Production evolution. |

| Git-based artifacts | Reviewable config/checksums. | Large binaries unsuitable. | Use for metadata, not all arrays/models. |



Use a filesystem registry with a `registry.json` and immutable artifact directories. Promote via a pull request or explicit `promote_model.py` command after all gates pass. Rollback means changing one approved pointer to a previously validated bundle; it never deletes the old bundle.


## 26. Inference pipeline

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 26 operational rather than descriptive: Inference pipeline. |
| **Owner** | Backend/ML lead |
| **Inputs** | Approved artifact and cached features |
| **Outputs** | Inference facade and prediction envelope |
| **Files / folders** | `backend/app/services/inference.py; backend/app/schemas/prediction.py` |
| **Command** | `pytest tests/inference -q` |
| **Test** | Replay known case with exact versions |
| **Failure and fallback** | Spread-only/unavailable fallback |
| **Definition of done** | Deterministic response. The evidence is committed or stored with a checksum and linked from the phase report. |


For “Show me India Day-6 bust risk,” the API first resolves a forecast run and target valid time, then loads cached issue-time features. If features are missing, the request returns `DATA_DELAYED` or triggers a bounded asynchronous materialization; it does not load future truth. The inference facade loads the approved model, produces a raw score, applies the calibration artifact, computes OOD, applies abstention, builds risk objects and trajectory, retrieves eligible analogs, stores a prediction record and returns the typed response.


| Operation | Precomputed/cached/realtime/asynchronous |

|---|---|

| Forecast field download | Asynchronous; cached immutable. |

| Feature table for known replay/cycle | Precomputed; cached. |

| Model load | Process startup/cached in memory. |

| GBM score/calibration/OOD | Realtime. |

| Risk trajectory | Precomputed or realtime from leadwise scores. |

| Spatial object extraction | Precomputed for large grids; realtime only for small products. |

| Analog index | Precomputed; query realtime. |

| Verification | Asynchronous after valid time; never used in issue-time score. |

| Frontend map render | Realtime network request + client cache. |



## 27. OOD + abstention service

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 27 operational rather than descriptive: OOD + abstention service. |
| **Owner** | ML safety lead |
| **Inputs** | Feature vector, training reference and policy |
| **Outputs** | OOD/abstention module and policy JSON |
| **Files / folders** | `ood/; configs/safety.yaml` |
| **Command** | `python -m ood.evaluate --split ood` |
| **Test** | Coverage-risk and retained risk report |
| **Failure and fallback** | Caution/abstain; no false confidence |
| **Definition of done** | Safety state reaches UI. The evidence is committed or stored with a checksum and linked from the phase report. |


The OOD service sits after feature construction and before the user-facing decision. It returns a numeric score, a status and an abstention decision. Start with robust feature distance, training-support density, missingness, regime novelty, model-version status and analog distance. Deep embedding OOD is optional.


| State | Meaning | Backend response | Frontend treatment |

|---|---|---|---|

| NORMAL | Supported state; ordinary prediction. | ood=false, abstain=false. | Show probability with normal confidence. |

| UNUSUAL | Supported but far from central training support. | ood=true/status=UNUSUAL, abstain may be false. | Show caution banner and evidence. |

| OOD | Outside declared support or post-upgrade unsupported. | status=OOD, threshold, reason codes. | Show OOD prominently; disable causal language. |

| ABSTAIN | Safety policy withholds actionable probability. | p_bust=null, abstain=true, fallback/reason. | Show “I don’t know” and review/fallback path. |



Measure coverage–risk, retained-case Brier/PR-AUC, abstention rate, high-confidence error rate and subgroup behavior. Do not call conformal guarantees universal under arbitrary atmospheric shift; report empirical calibration/coverage and assumptions.


## 28. Analog retrieval service

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 28 operational rather than descriptive: Analog retrieval service. |
| **Owner** | ML/data lead |
| **Inputs** | Eligible historical archive and exclusion policy |
| **Outputs** | Index, metadata filters and analog cards |
| **Files / folders** | `analog/; artifacts/index/; docs/12_ANALOG_SYSTEM.md` |
| **Command** | `python -m analog.build_index --version A1` |
| **Test** | Same-event/time exclusion test |
| **Failure and fallback** | Explanation-only/no analog |
| **Definition of done** | No leakage and reproducible hits. The evidence is committed or stored with a checksum and linked from the phase report. |


Generate an embedding or PCA summary from the issue-time forecast state, index only historical records whose outcomes are already known, and attach an eligibility policy. The service returns similarity, date, region, lead, forecast characteristics, verified outcome and source pointers. Same-event/time exclusion is enforced before the vector query or by post-filtering with enough candidates.


```text
forecast state → normalized summary/embedding → FAISS/Lance index
     → filter: earlier event/time, same variables, same lead, eligible source
     → top-k similarity
     → join historical label/outcome
     → analog card + analog_bust_rate
     → prediction response
```


Run two experiments: (1) analog as a predictive feature versus no analog on an event-held-out test, and (2) analog as explanation-only with no effect on score. If predictive gain is not stable, keep the explanation panel and remove it from the model.


## 29. Spatial risk map pipeline

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 29 operational rather than descriptive: Spatial risk map pipeline. |
| **Owner** | ML/backend lead |
| **Inputs** | Grid/patch products and object rules |
| **Outputs** | Risk-map writer, object extractor and endpoint |
| **Files / folders** | `spatial/; object-store maps/` |
| **Command** | `python -m spatial.build_map --prediction P` |
| **Test** | GeoJSON/field round-trip and metrics |
| **Failure and fallback** | Regional risk fallback |
| **Definition of done** | Map lineage complete. The evidence is committed or stored with a checksum and linked from the phase report. |


Use regional risk as the MVP contract and add grid/patch risk only when spatial labels are reliable. The spatial pipeline aggregates or scores patches, applies fixed train-selected smoothing, extracts contiguous risk objects, computes area fraction/centroid/first-failure location and writes a compact GeoJSON summary plus a Zarr/NetCDF field.


| Product | Storage | API representation |

|---|---|---|

| Regional risk | Postgres prediction row. | JSON scalar. |

| Grid risk field | Zarr/NetCDF in object storage. | Signed URL or server-side tile/GeoJSON summary. |

| Risk objects | Postgres summary + GeoJSON object file. | Object list, bbox, centroid, area fraction. |

| Research export | Parquet/NetCDF with provenance. | `/v1/export` URL and checksum. |



Do not send a full high-resolution grid as a giant JSON array in every response. For SIH, a GeoJSON risk-object layer plus a small downsampled grid is sufficient; a tile service is future work.


## 30. Frontend architecture

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 30 operational rather than descriptive: Frontend architecture. |
| **Owner** | Frontend lead |
| **Inputs** | API schema and UX requirements |
| **Outputs** | Typed app, component library and pages |
| **Files / folders** | `frontend/src/` |
| **Command** | `pnpm --dir frontend test` |
| **Test** | Render fixture response including abstain |
| **Failure and fallback** | No unsafe display |
| **Definition of done** | UI state tests pass. The evidence is committed or stored with a checksum and linked from the phase report. |


| Choice | Decision | Why |

|---|---|---|

| React + TypeScript + Vite | Choose. | Fast student setup, typed API client, static deployment. |

| Next.js | Optional evolution. | Useful for routing/SSR but unnecessary for the MVP. |

| MapLibre or Leaflet | Choose one; Leaflet is simplest. | Maps with open tiles and GeoJSON layers. |

| ECharts/Recharts | Choose ECharts for trajectory/reliability. | Interactive charts with clear tooltips. |

| State | React Query or a small typed query layer. | Caching/loading/error state without global complexity. |



Pages: Dashboard; Forecast View; Risk Map; Risk Trajectory; Analog Explorer; Explanation; Research Metrics; Data Provenance; About/Research. The judge-facing default is Dashboard with a selected replay case, a trust badge, map, trajectory, “Why?” evidence panel and model comparison.


## 31. Frontend → API flow

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 31 operational rather than descriptive: Frontend → API flow. |
| **Owner** | Frontend/backend lead |
| **Inputs** | PredictionEnvelope and map endpoints |
| **Outputs** | Query client, cache keys and state machine |
| **Files / folders** | `frontend/src/api/; frontend/src/state/` |
| **Command** | `pnpm --dir frontend test:e2e` |
| **Test** | Replay selection from click to render |
| **Failure and fallback** | Retry/error/empty state |
| **Definition of done** | No stale current display. The evidence is committed or stored with a checksum and linked from the phase report. |


```text
User selects: region=INDIA_CORE, variable=Z500, lead=144h
  → frontend validates selection and builds GET/POST request
  → POST /v1/predict
  → backend returns typed PredictionEnvelope
  → store response in query cache keyed by issue/valid/region/variable/lead/model
  → render probability/severity/trust
  → request /v1/risk-map and /v1/explanation
  → render GeoJSON map, trajectory and analog cards
  → show provenance drawer and claim scope
```


| UI state | Display rule |

|---|---|

| Loading | Skeleton map/card; do not show zero or stale risk as current. |

| No data | State exact missing source and next retry time. |

| Data delayed | Show last successful cycle with timestamp and a delayed badge. |

| Model unavailable | Show spread-only or unavailable fallback explicitly. |

| OOD | Orange/high-visibility caution; show score/status and evidence. |

| Abstention | No probability number; show “I don’t know—human review required.” |

| High risk | Show probability, severity and reasons with claim scope. |

| Verification pending | Do not reveal outcome; show “verification pending” in live mode. |

| API error | Retain no stale response unless user explicitly opens a prior replay. |



## 32. Frontend error / trust states

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 32 operational rather than descriptive: Frontend error / trust states. |
| **Owner** | Frontend/research lead |
| **Inputs** | Safety states and claim scope |
| **Outputs** | Trust banner, error panels and accessibility text |
| **Files / folders** | `frontend/src/components/trust/` |
| **Command** | `pnpm --dir frontend test -- trust` |
| **Test** | Fixture NORMAL/OOD/ABSTAIN/PENDING |
| **Failure and fallback** | Show “I don’t know” for abstention |
| **Definition of done** | States are unambiguous. The evidence is committed or stored with a checksum and linked from the phase report. |


The frontend must treat safety state as data, not decoration. The response schema controls which components render. No component may calculate its own probability, interpolate an abstained value, or label a correlational explanation as a cause. A global `TrustBanner` appears above the map and remains visible while scrolling.


## 33. Live data vs historical demo

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 33 operational rather than descriptive: Live data vs historical demo. |
| **Owner** | Demo/research lead |
| **Inputs** | Frozen replay fixture and live-mode boundary |
| **Outputs** | Case manifest and stepwise reveal controller |
| **Files / folders** | `demo/cases/; docs/22_DEMO.md` |
| **Command** | `python -m demo.validate CASE_ID` |
| **Test** | Run without network and hide future truth until reveal |
| **Failure and fallback** | Use static bundle |
| **Definition of done** | Repeatable timed replay. The evidence is committed or stored with a checksum and linked from the phase report. |


The SIH demo must use deterministic historical replay. A replay case includes issue time, forecast cycle, available features, the model decision and a verification-reveal step that is disabled until the narrative reaches the outcome. Live mode is a separate feature flag with data-delay/verification-pending states. This separation prevents a demo from depending on the current day or accidentally showing future truth in a live view.


## 34. Backend jobs / scheduling

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 34 operational rather than descriptive: Backend jobs / scheduling. |
| **Owner** | Backend/data lead |
| **Inputs** | Job types and source schedules |
| **Outputs** | Idempotent job commands and scheduler config |
| **Files / folders** | `jobs/; configs/schedules.yaml` |
| **Command** | `python -m jobs.run --job ingest --dry-run` |
| **Test** | Retry/idempotency/error states |
| **Failure and fallback** | Last-successful product |
| **Definition of done** | Job audit exists. The evidence is committed or stored with a checksum and linked from the phase report. |


| Schedule | Job | Failure handling |

|---|---|---|

| Every forecast cycle | Detect/download → checksum → QC → manifest. | Retry with capped backoff; mark delayed. |

| After ingestion | Alignment → features → inference products. | Idempotency key by source/run/version. |

| After valid time | Verification → labels → retrospective metrics. | Never mutate issue-time prediction; append outcome. |

| Research trigger | Training/evaluation command. | Manual approval; no automatic production replacement. |

| Periodic | Drift summary and registry report. | Alert only; do not silently retrain. |

| Demo preparation | Precompute replay products. | Build fails if any expected artifact is missing. |



Use cron for local; GitHub Actions or a cloud scheduler for a low-cost deployment. Do not add Celery/Redis until a job is too long for a scheduled command or retries need durable queues. If a worker is added, use Redis/RQ or Celery only for ingestion/materialization, not for the core scientific definitions.


## 35. Cloud architecture

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 35 operational rather than descriptive: Cloud architecture. |
| **Owner** | Tech lead |
| **Inputs** | Chosen cloud/local topology |
| **Outputs** | Deployment manifests, env map and cost sheet |
| **Files / folders** | `docker/; deploy/; docs/17_DEPLOYMENT.md` |
| **Command** | `make deploy-smoke` |
| **Test** | Health/rollback/secret checks |
| **Failure and fallback** | Local replay fallback |
| **Definition of done** | Low-cost path works. The evidence is committed or stored with a checksum and linked from the phase report. |


Low-cost hosted version: static frontend on a static host; one Dockerized FastAPI container on a low-cost container/VM; managed PostgreSQL only when team sharing requires it; object storage for Zarr/model bundles; scheduled job for ingestion; local training and uploaded approved artifacts. GPU is not required for the GBM core.


| Tier | Frontend | API | DB/storage | Training | Use |

|---|---|---|---|---|---|

| ₹0/local | localhost Vite | localhost FastAPI | Docker Postgres + local disk | Local CPU | Development and offline demo |

| Low-cost | Static host | Single small container/VM | Small managed Postgres or SQLite for private demo + object store | Local CPU | Public SIH demo |

| Moderate | Static/CDN | Managed container with HTTPS | Managed Postgres + S3-compatible store | Optional temporary GPU | Team/staging |

| Production pilot | CDN/static + WAF | Autoscaled container/VM | Managed Postgres, versioned object store, backups | Scheduled reproducible training | Partner/operational trial |



## 36. Local development architecture

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 36 operational rather than descriptive: Local development architecture. |
| **Owner** | ML/data lead |
| **Inputs** | Local fixture and Compose topology |
| **Outputs** | Local startup script and sample data |
| **Files / folders** | `docker-compose.yml; scripts/start_local.sh` |
| **Command** | `make run-local` |
| **Test** | Fresh machine start + replay |
| **Failure and fallback** | Use no Redis/MinIO by default |
| **Definition of done** | One-command local run. The evidence is committed or stored with a checksum and linked from the phase report. |


```text
Browser
  → Vite frontend :5173
  → FastAPI :8000
  → PostgreSQL :5432 (Docker)
  → local data/ and artifacts/
  → optional MinIO :9000 for object-store parity
  → optional Redis only for worker profile
```


Startup order: (1) copy `.env.example`; (2) start Postgres; (3) apply migrations; (4) validate local data manifest; (5) load approved model; (6) start FastAPI; (7) start frontend; (8) run health check; (9) open a deterministic replay case. The app should work without MinIO/Redis in the default profile.


## 37. Docker architecture

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 37 operational rather than descriptive: Docker architecture. |
| **Owner** | DevOps lead |
| **Inputs** | API/frontend/DB topology |
| **Outputs** | Dockerfiles, profiles and health checks |
| **Files / folders** | `docker/; docker-compose.yml` |
| **Command** | `docker compose config && make smoke` |
| **Test** | Restart each service and verify readiness |
| **Failure and fallback** | Reduce containers |
| **Definition of done** | Clean Compose pass. The evidence is committed or stored with a checksum and linked from the phase report. |


```text
services:
  db:
    image: postgres:16
  api:
    build: ./docker/api.Dockerfile
    depends_on: [db]
  frontend:
    build: ./docker/frontend.Dockerfile
    depends_on: [api]
  # optional profiles, not default:
  # minio: object storage parity
  # redis: worker/cache
  # worker: scheduled materialization
```


The default Compose file should contain only `db`, `api` and `frontend`; adding a worker, Redis or MinIO must be a profile with documented value. Training remains a CLI job because it needs different resource and data access policies.


## 38. Security

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 38 operational rather than descriptive: Security. |
| **Owner** | Security lead |
| **Inputs** | API, DB, upload and secrets rules |
| **Outputs** | Security headers, CORS, validation, rate controls and redaction |
| **Files / folders** | `backend/app/security.py; docs/21_SECURITY.md` |
| **Command** | `pytest tests/security -q` |
| **Test** | Bad input, CORS, secret-redaction tests |
| **Failure and fallback** | Reject request/quarantine |
| **Definition of done** | No high-risk finding. The evidence is committed or stored with a checksum and linked from the phase report. |


| Control | Implementation |

|---|---|

| API security | HTTPS at deployment; request size/timeouts; Pydantic validation; correlation IDs; rate limit public endpoints. |

| CORS | Allow only deployed frontend origin; localhost origins in development only. |

| Secrets | `.env` ignored; environment variables or secret manager; never log tokens. |

| Database | Private network/localhost; least-privilege app user; migrations separate from runtime user. |

| Uploads | Do not accept arbitrary scientific files in MVP; if enabled, whitelist extension/content type, size, checksum and quarantine path. |

| Authentication | Read-only public demo can be anonymous; protect training/admin/metrics exports with a simple role or deployment gateway. |

| Logging | Redact query credentials and personal data; store request IDs and model/data versions. |

| Backups | Versioned object artifacts and scheduled Postgres backups in hosted deployment. |



## 39. Observability

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 39 operational rather than descriptive: Observability. |
| **Owner** | SRE/Backend lead |
| **Inputs** | Logs, metrics and failure codes |
| **Outputs** | Structured logging and health/metrics endpoints |
| **Files / folders** | `backend/app/observability/; docs/18_MLOPS.md` |
| **Command** | `python scripts/observability_smoke.py` |
| **Test** | Trace request through API/model/storage |
| **Failure and fallback** | Degraded status/alert |
| **Definition of done** | Request ID appears end-to-end. The evidence is committed or stored with a checksum and linked from the phase report. |


| Signal | Fields / alert |

|---|---|

| Logs | timestamp, level, request_id, job_id, route, latency_ms, status, model_version, data_version, error_code. |

| Ingestion | source, cycle, checksum, bytes, QC status, retry count, delay minutes. |

| Inference | feature latency, model latency, calibration latency, map/analog latency, total latency. |

| Safety | OOD frequency, abstention frequency, missing-feature frequency, reason-code counts. |

| Data drift | feature PSI/quantile shifts, missingness, member count, version change. |

| Performance | When truth arrives: Brier/ECE/PR-AUC by lead/region/version; descriptive until enough data. |

| Database | connection health, slow queries, storage size, migration version. |

| Frontend | API error rate, load time, rendering error, stale-data banner count. |



## 40. Model / data drift

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 40 operational rather than descriptive: Model / data drift. |
| **Owner** | ML/SRE lead |
| **Inputs** | Version metadata and rolling diagnostics |
| **Outputs** | Drift report and upgrade hold policy |
| **Files / folders** | `drift/; configs/drift.yaml` |
| **Command** | `python -m drift.report --period ...` |
| **Test** | Synthetic distribution/version shift |
| **Failure and fallback** | Abstain/hold/recalibrate |
| **Definition of done** | Drift decision recorded. The evidence is committed or stored with a checksum and linked from the phase report. |


NWP model changes can change ensemble spread, bias, resolution and member behavior. Track `source`, `model_version`, `cycle`, `grid_hash`, `member_count`, feature distributions, OOD rate, abstention rate and delayed verification metrics. A model-version change automatically enters a holdout/review state; it is not merely a feature value.


| Drift type | Detection | Action |

|---|---|---|

| Schema/grid | Grid hash, dimensions, units, variable checks. | Block ingestion until adapter is updated. |

| Distribution | Quantile/PSI/KS summaries by lead/region. | Flag unusual; do not auto-retrain. |

| Calibration | Rolling reliability/Brier after truth. | Recalibrate or suspend model. |

| Performance | Event/block metrics with uncertainty. | Compare against spread-only and prior model. |

| Version | Explicit model version and upgrade timestamp. | Use model-version holdout; abstain if unsupported. |



## 41. Retraining pipeline

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 41 operational rather than descriptive: Retraining pipeline. |
| **Owner** | MLOps lead |
| **Inputs** | New verified history and current model |
| **Outputs** | Retrain candidate pipeline and approval report |
| **Files / folders** | `training/retrain.py; registry/` |
| **Command** | `python -m training.retrain --candidate ...` |
| **Test** | Compare against production bundle |
| **Failure and fallback** | Keep production model |
| **Definition of done** | No automatic replacement. The evidence is committed or stored with a checksum and linked from the phase report. |


```text
new verified history
  ↓
new immutable labels
  ↓
dataset version + split manifest
  ↓
QC + leakage tests
  ↓
train baselines/core/safety
  ↓
calibrate and evaluate
  ↓
compare against production model
  ↓
human approval + evidence bundle
  ↓
registry promotion
  ↓
canary/replay health check
  ↓
deployment
  ↓
monitoring
```


Never automatically replace a production model. The approval record must state whether the new model improves the primary metric, calibration, OOD safety and latency, and whether it changes claim scope. A failed retraining run leaves the current approved model untouched.


## 42. Complete testing strategy

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 42 operational rather than descriptive: Complete testing strategy. |
| **Owner** | QA lead |
| **Inputs** | All contracts and failure states |
| **Outputs** | Test plan, fixtures, CI checks and E2E suite |
| **Files / folders** | `tests/; .github/workflows/` |
| **Command** | `make test-all` |
| **Test** | Run unit/data/leakage/API/UI/deployment suites |
| **Failure and fallback** | Block release |
| **Definition of done** | Critical tests pass. The evidence is committed or stored with a checksum and linked from the phase report. |


| Test layer | Examples | Pass gate |

|---|---|---|

| Backend unit | Pydantic rejects invalid lead; service returns correct error code. | All critical route/service tests pass. |

| Frontend unit | Abstain response renders no probability; loading/error states. | Component tests pass. |

| API contract | OpenAPI/schema validation; request IDs; pagination/filter validation. | Contract snapshot unchanged or reviewed. |

| Data | Dimensions, units, grid, timestamp, member count, checksum. | No silent QC error. |

| ML | Feature formulas, deterministic inference, artifact reload. | Predictions reproduce within tolerance. |

| Leakage | Future timestamp, truth path, split overlap, analog same-event. | Any failure blocks promotion. |

| Integration | Ingest pilot → feature → API replay. | End-to-end case returns expected schema. |

| E2E | Browser selects case and renders map/trajectory/abstention. | Playwright/manual replay pass. |

| Deployment | Clean Docker startup, migration, health, rollback. | Fresh machine reproduces demo. |

| Security | CORS, size limits, redaction, unauthorized admin routes. | No high-risk finding. |



## 43. Reproducibility

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 43 operational rather than descriptive: Reproducibility. |
| **Owner** | Research/MLOps lead |
| **Inputs** | Manifests, seeds, commits and artifacts |
| **Outputs** | Reproduction command and evidence bundle |
| **Files / folders** | `docs/20_REPRODUCIBILITY.md; scripts/reproduce.py` |
| **Command** | `make reproduce-pilot` |
| **Test** | Clean environment and checksum comparison |
| **Failure and fallback** | Document environment/data issue |
| **Definition of done** | Reproduction matches. The evidence is committed or stored with a checksum and linked from the phase report. |


A researcher must be able to reproduce dataset, features, training, model and evaluation from a commit and manifest. Record seed, data version, code commit, model version, training period, hyperparameters, feature schema, label version, source checksums, environment lock and split manifest. Provide `make reproduce-pilot` and a small public fixture so the entire system can be smoke-tested without downloading the full archive.


## 44. Performance / scaling

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 44 operational rather than descriptive: Performance / scaling. |
| **Owner** | Tech lead |
| **Inputs** | Measured latency, volume and cost |
| **Outputs** | Load test and scaling decision |
| **Files / folders** | `tests/load/; reports/performance/` |
| **Command** | `python scripts/load_test.py --users 10,100` |
| **Test** | Measure p50/p95 and bottlenecks |
| **Failure and fallback** | Do not scale prematurely |
| **Definition of done** | Evidence supports topology. The evidence is committed or stored with a checksum and linked from the phase report. |


| Users | Expected architecture | Bottleneck / decision |

|---|---|---|

| 10 | Single API process, local/object cache, Postgres. | Data access and map generation dominate; precompute. |

| 100 | One container with 2–4 workers, cache, managed DB. | Model memory and concurrent map reads; keep fields in object store. |

| 1,000 | Multiple API replicas, CDN/static frontend, Redis or HTTP cache, managed DB. | Inference/product cache; separate worker if materialization competes. |

| 10,000 | Autoscaled API, queue, tiles/CDN, read replicas and object store. | Operational production; outside SIH MVP. |



Do not optimize prematurely. Measure p50/p95 API latency, feature-cache hit rate, map size, database query time and analog query time before adding infrastructure. The biggest likely bottleneck is moving large weather fields, not GBM inference.


## 45. Complete implementation phases

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 45 operational rather than descriptive: Complete implementation phases. |
| **Owner** | Project manager |
| **Inputs** | All phase cards and dependencies |
| **Outputs** | Execution board with milestone owners |
| **Files / folders** | `docs/roadmap/; project tracker` |
| **Command** | `make roadmap-check` |
| **Test** | Every phase has evidence/owner/gate |
| **Failure and fallback** | Re-sequence/stop optional work |
| **Definition of done** | No hidden dependency. The evidence is committed or stored with a checksum and linked from the phase report. |


### Phase 0 Project setup

| Field | Definition |

|---|---|

| OBJECTIVE | Create repo/env/Makefile/.env/Compose. |

| INPUT | Empty repo + toolchain. |

| PROCESS | Git, Python, Node, Docker. |

| OUTPUT | README, pyproject, package.json. |

| TOOLS | Scaffold commands and smoke test. |

| FILES CREATED | README, pyproject, package.json. |

| CODE TO WRITE | Git, Python, Node, Docker. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Pinned dependencies. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Imports/tests pass. |

| COMMON ERRORS | Broken environment. |

| NEXT PHASE | Fix before data. |



### Phase 1 Research freeze

| Field | Definition |

|---|---|

| OBJECTIVE | Freeze scope, claim sheet and source boundary. |

| INPUT | Research docs. |

| PROCESS | Write config/claim_scope. |

| OUTPUT | requirements.md, claim_scope.yaml. |

| TOOLS | Copy approved specs. |

| FILES CREATED | requirements.md, claim_scope.yaml. |

| CODE TO WRITE | Write config/claim_scope. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Approved strategy. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Team signs scope. |

| COMMON ERRORS | Scope drift. |

| NEXT PHASE | Review gate. |



### Phase 2 Data acquisition

| Field | Definition |

|---|---|

| OBJECTIVE | Obtain legal pilot. |

| INPUT | Source URLs/access. |

| PROCESS | Download bounded files. |

| OUTPUT | raw + manifest. |

| TOOLS | Downloader/retry/checksum. |

| FILES CREATED | raw + manifest. |

| CODE TO WRITE | Download bounded files. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | License and storage. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Pilot complete. |

| COMMON ERRORS | Unavailable source. |

| NEXT PHASE | Switch proxy. |



### Phase 3 Data storage

| Field | Definition |

|---|---|

| OBJECTIVE | Create raw/validated/processed layout. |

| INPUT | Pilot files. |

| PROCESS | Write storage adapters. |

| OUTPUT | Versioned directories. |

| TOOLS | Zarr/NetCDF/Parquet writer. |

| FILES CREATED | Versioned directories. |

| CODE TO WRITE | Write storage adapters. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Disk/object store. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Round-trip reads. |

| COMMON ERRORS | Corrupt/oversized. |

| NEXT PHASE | Reduce pilot. |



### Phase 4 Data ingestion

| Field | Definition |

|---|---|

| OBJECTIVE | Automate detection/QC. |

| INPUT | Manifest. |

| PROCESS | Idempotent ingest job. |

| OUTPUT | ingest report. |

| TOOLS | CLI + logs. |

| FILES CREATED | ingest report. |

| CODE TO WRITE | Idempotent ingest job. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Checksum metadata. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Second run creates no duplicate. |

| COMMON ERRORS | Duplicate/missing. |

| NEXT PHASE | Quarantine. |



### Phase 5 Forecast alignment

| Field | Definition |

|---|---|

| OBJECTIVE | Join issue/valid/lead. |

| INPUT | Forecast/truth grids. |

| PROCESS | Normalize time/grid/units. |

| OUTPUT | aligned table/fields. |

| TOOLS | xarray alignment tests. |

| FILES CREATED | aligned table/fields. |

| CODE TO WRITE | Normalize time/grid/units. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Tolerance config. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | All joins pass. |

| COMMON ERRORS | Ambiguous join. |

| NEXT PHASE | Drop/repair. |



### Phase 6 Bust labels

| Field | Definition |

|---|---|

| OBJECTIVE | Implement versioned protocol. |

| INPUT | Aligned data. |

| PROCESS | Error/normalization/ambiguity/spatial. |

| OUTPUT | labels + provenance. |

| TOOLS | label engine CLI. |

| FILES CREATED | labels + provenance. |

| CODE TO WRITE | Error/normalization/ambiguity/spatial. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Train-only thresholds. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Sensitivity report. |

| COMMON ERRORS | No events. |

| NEXT PHASE | Coarsen/continuous. |



### Phase 7 Feature engineering

| Field | Definition |

|---|---|

| OBJECTIVE | Build issue-safe predictors. |

| INPUT | Runs/labels metadata. |

| PROCESS | Ensemble/revision/regime. |

| OUTPUT | feature Parquet. |

| TOOLS | feature builders/tests. |

| FILES CREATED | feature Parquet. |

| CODE TO WRITE | Ensemble/revision/regime. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Earlier cycles only. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Timestamp tests pass. |

| COMMON ERRORS | Leakage. |

| NEXT PHASE | Remove feature. |



### Phase 8 Dataset creation

| Field | Definition |

|---|---|

| OBJECTIVE | Freeze row-level table/splits. |

| INPUT | Features/labels. |

| PROCESS | Key validation and split manifest. |

| OUTPUT | dataset version. |

| TOOLS | dataset CLI. |

| FILES CREATED | dataset version. |

| CODE TO WRITE | Key validation and split manifest. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Event IDs. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Reproducible rows. |

| COMMON ERRORS | Overlap. |

| NEXT PHASE | Fix grouping. |



### Phase 9 Baselines

| Field | Definition |

|---|---|

| OBJECTIVE | Run E0–E3. |

| INPUT | Frozen dataset. |

| PROCESS | Train and score. |

| OUTPUT | baseline report. |

| TOOLS | sklearn. |

| FILES CREATED | baseline report. |

| CODE TO WRITE | Train and score. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Blocked evaluation. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | CIs/report. |

| COMMON ERRORS | No signal. |

| NEXT PHASE | Publish negative. |



### Phase 10 GBM

| Field | Definition |

|---|---|

| OBJECTIVE | Train practical core. |

| INPUT | Safe blocks. |

| PROCESS | Fit/tune/score. |

| OUTPUT | model artifact. |

| TOOLS | LightGBM/XGBoost. |

| FILES CREATED | model artifact. |

| CODE TO WRITE | Fit/tune/score. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Validation block. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Beats baseline or fallback. |

| COMMON ERRORS | Overfit. |

| NEXT PHASE | Simplify. |



### Phase 11 Calibration

| Field | Definition |

|---|---|

| OBJECTIVE | Make probabilities useful. |

| INPUT | Scores/calibration block. |

| PROCESS | Platt/isotonic. |

| OUTPUT | calibration artifact. |

| TOOLS | sklearn calibration. |

| FILES CREATED | calibration artifact. |

| CODE TO WRITE | Platt/isotonic. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Reliability. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Improved Brier/ECE. |

| COMMON ERRORS | Sparse. |

| NEXT PHASE | Pooled method. |



### Phase 12 OOD

| Field | Definition |

|---|---|

| OBJECTIVE | Detect unsupported states. |

| INPUT | Train reference + OOD split. |

| PROCESS | Distance/drift/regime. |

| OUTPUT | OOD artifact. |

| TOOLS | sklearn/scipy. |

| FILES CREATED | OOD artifact. |

| CODE TO WRITE | Distance/drift/regime. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Coverage-risk. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Separates stress cases. |

| COMMON ERRORS | No separation. |

| NEXT PHASE | Warning-only. |



### Phase 13 Abstention

| Field | Definition |

|---|---|

| OBJECTIVE | Implement safe withholding. |

| INPUT | Scores/OOD/validation. |

| PROCESS | Choose coverage-risk point. |

| OUTPUT | policy. |

| TOOLS | policy module/tests. |

| FILES CREATED | policy. |

| CODE TO WRITE | Choose coverage-risk point. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Retained risk. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Risk improves. |

| COMMON ERRORS | Always/never abstains. |

| NEXT PHASE | Human-review flag. |



### Phase 14 Analog retrieval

| Field | Definition |

|---|---|

| OBJECTIVE | Add memory only if safe. |

| INPUT | Eligible archive. |

| PROCESS | Index/query/filter. |

| OUTPUT | cards/index. |

| TOOLS | FAISS/Lance optional. |

| FILES CREATED | cards/index. |

| CODE TO WRITE | Index/query/filter. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Same-event exclusion. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Gain or explanation value. |

| COMMON ERRORS | Leakage/no gain. |

| NEXT PHASE | Explanation-only. |



### Phase 15 Spatial risk

| Field | Definition |

|---|---|

| OBJECTIVE | Produce region/objects/maps. |

| INPUT | Grid/patch features. |

| PROCESS | Score, smooth, objects. |

| OUTPUT | GeoJSON/Zarr. |

| TOOLS | xarray/scipy. |

| FILES CREATED | GeoJSON/Zarr. |

| CODE TO WRITE | Score, smooth, objects. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | FSS/object metrics. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Noisy but interpretable. |

| COMMON ERRORS | Cellwise inflation. |

| NEXT PHASE | Regional fallback. |



### Phase 16 Temporal risk

| Field | Definition |

|---|---|

| OBJECTIVE | Produce lead trajectory. |

| INPUT | Multi-lead scores. |

| PROCESS | Leadwise/hazard. |

| OUTPUT | trajectory. |

| TOOLS | sklearn/statsmodels optional. |

| FILES CREATED | trajectory. |

| CODE TO WRITE | Leadwise/hazard. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Timing/calibration. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Adds warning value. |

| COMMON ERRORS | Incoherent. |

| NEXT PHASE | Independent leads. |



### Phase 17 Advanced model

| Field | Definition |

|---|---|

| OBJECTIVE | Test one deep option. |

| INPUT | Frozen data/budget. |

| PROCESS | Matched experiment. |

| OUTPUT | checkpoint/report. |

| TOOLS | PyTorch optional. |

| FILES CREATED | checkpoint/report. |

| CODE TO WRITE | Matched experiment. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Strict holdout. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Beats GBM. |

| COMMON ERRORS | No gain/cost. |

| NEXT PHASE | Discard. |



### Phase 18 Evaluation

| Field | Definition |

|---|---|

| OBJECTIVE | Freeze evidence. |

| INPUT | All artifacts. |

| PROCESS | Run final metrics/CIs. |

| OUTPUT | evidence bundle. |

| TOOLS | evaluation CLI. |

| FILES CREATED | evidence bundle. |

| CODE TO WRITE | Run final metrics/CIs. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Pre-specified metrics. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | All gates pass. |

| COMMON ERRORS | Any fail. |

| NEXT PHASE | Report/fallback. |



### Phase 19 Backend

| Field | Definition |

|---|---|

| OBJECTIVE | Implement service boundaries. |

| INPUT | Artifact + schemas. |

| PROCESS | FastAPI/repositories/services. |

| OUTPUT | API server. |

| TOOLS | FastAPI/Pydantic. |

| FILES CREATED | API server. |

| CODE TO WRITE | FastAPI/repositories/services. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Contract tests. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Health/predict works. |

| COMMON ERRORS | Coupling. |

| NEXT PHASE | Refactor. |



### Phase 20 Database

| Field | Definition |

|---|---|

| OBJECTIVE | Implement metadata schema. |

| INPUT | Migration design. |

| PROCESS | Migrate/seeds/indexes. |

| OUTPUT | Postgres. |

| TOOLS | Alembic/SQL. |

| FILES CREATED | Postgres. |

| CODE TO WRITE | Migrate/seeds/indexes. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | FK/unique tests. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Replay stored. |

| COMMON ERRORS | Migration failure. |

| NEXT PHASE | Reset dev DB. |



### Phase 21 API

| Field | Definition |

|---|---|

| OBJECTIVE | Expose typed endpoints. |

| INPUT | Services/DB. |

| PROCESS | Routes/errors/provenance. |

| OUTPUT | OpenAPI. |

| TOOLS | FastAPI. |

| FILES CREATED | OpenAPI. |

| CODE TO WRITE | Routes/errors/provenance. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Contract tests. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Schemas stable. |

| COMMON ERRORS | Ambiguous states. |

| NEXT PHASE | Fix types. |



### Phase 22 Frontend

| Field | Definition |

|---|---|

| OBJECTIVE | Build judge dashboard. |

| INPUT | API schema. |

| PROCESS | Views/map/charts/trust. |

| OUTPUT | React UI. |

| TOOLS | TS/Leaflet/ECharts. |

| FILES CREATED | React UI. |

| CODE TO WRITE | Views/map/charts/trust. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Replay/browser test. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | No unsafe render. |

| COMMON ERRORS | Stale/false confidence. |

| NEXT PHASE | Fix state model. |



### Phase 23 Integration

| Field | Definition |

|---|---|

| OBJECTIVE | Connect data→API→UI. |

| INPUT | All pieces. |

| PROCESS | Seed/replay/observability. |

| OUTPUT | working system. |

| TOOLS | Compose/scripts. |

| FILES CREATED | working system. |

| CODE TO WRITE | Seed/replay/observability. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | E2E. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Fresh startup passes. |

| COMMON ERRORS | Missing artifact. |

| NEXT PHASE | Add fixture. |



### Phase 24 Docker

| Field | Definition |

|---|---|

| OBJECTIVE | Containerize reproducibly. |

| INPUT | App/DB. |

| PROCESS | Dockerfiles/Compose. |

| OUTPUT | images. |

| TOOLS | Docker. |

| FILES CREATED | images. |

| CODE TO WRITE | Dockerfiles/Compose. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Clean machine. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | One-command run. |

| COMMON ERRORS | Env mismatch. |

| NEXT PHASE | Pin. |



### Phase 25 Deployment

| Field | Definition |

|---|---|

| OBJECTIVE | Publish low-cost demo. |

| INPUT | Images/artifacts. |

| PROCESS | HTTPS/env/health. |

| OUTPUT | staging/prod. |

| TOOLS | Container host/static host. |

| FILES CREATED | staging/prod. |

| CODE TO WRITE | HTTPS/env/health. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Smoke/rollback. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | URL works. |

| COMMON ERRORS | Quota/down. |

| NEXT PHASE | Local replay fallback. |



### Phase 26 Historical replay

| Field | Definition |

|---|---|

| OBJECTIVE | Script deterministic story. |

| INPUT | Chosen event. |

| PROCESS | Stepwise risk/verification reveal. |

| OUTPUT | replay case. |

| TOOLS | seeded fixture. |

| FILES CREATED | replay case. |

| CODE TO WRITE | Stepwise risk/verification reveal. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Narrative test. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Repeatable. |

| COMMON ERRORS | Data missing. |

| NEXT PHASE | Bundle fixture. |



### Phase 27 Judge demo

| Field | Definition |

|---|---|

| OBJECTIVE | Rehearse scientific story. |

| INPUT | Replay + metrics. |

| PROCESS | Script and operator controls. |

| OUTPUT | 3–5 min demo. |

| TOOLS | Browser + runbook. |

| FILES CREATED | 3–5 min demo. |

| CODE TO WRITE | Script and operator controls. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Timed dry run. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Shows difference. |

| COMMON ERRORS | Dashboard tour only. |

| NEXT PHASE | Cut features. |



### Phase 28 Testing

| Field | Definition |

|---|---|

| OBJECTIVE | Run all suites. |

| INPUT | Code/artifacts. |

| PROCESS | Unit/integration/leakage/E2E. |

| OUTPUT | test report. |

| TOOLS | pytest/Vitest/Playwright. |

| FILES CREATED | test report. |

| CODE TO WRITE | Unit/integration/leakage/E2E. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Clean env. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | No critical fail. |

| COMMON ERRORS | Flaky. |

| NEXT PHASE | Quarantine/fix. |



### Phase 29 Documentation

| Field | Definition |

|---|---|

| OBJECTIVE | Package evidence and claims. |

| INPUT | All reports. |

| PROCESS | Write docs/runbooks. |

| OUTPUT | release bundle. |

| TOOLS | Markdown/checklists. |

| FILES CREATED | release bundle. |

| CODE TO WRITE | Write docs/runbooks. |

| COMMANDS | Run the phase-specific CLI/scripts, then `make test` and record the artifact manifest. |

| DEPENDENCIES | Review links. |

| TEST | Execute the phase smoke/integration test and verify the output artifact is readable and versioned. |

| PASS CONDITION | Team can rebuild. |

| COMMON ERRORS | Unknown claim. |

| NEXT PHASE | Mark unknown. |



## 46. Exact team work distribution

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 46 operational rather than descriptive: Exact team work distribution. |
| **Owner** | Project manager |
| **Inputs** | Team roles and interface contracts |
| **Outputs** | RACI matrix and integration calendar |
| **Files / folders** | `docs/TEAM.md; CODEOWNERS` |
| **Command** | `make ownership-check` |
| **Test** | Review handoffs and blockers |
| **Failure and fallback** | Reassign work |
| **Definition of done** | Every artifact has owner. The evidence is committed or stored with a checksum and linked from the phase report. |


| Role | Owns | Parallel work | Integration point |

|---|---|---|---|

| ML/Data person | Data adapters, alignment, labels, features, baselines, GBM, calibration, OOD. | Runs research pipeline while API/UI scaffold. | Publishes feature/schema/model contracts and replay fixtures. |

| Backend person | FastAPI, services, Postgres, object-store access, jobs, provenance. | Builds against mocked schemas before model is final. | Loads approved artifact through InferenceFacade. |

| Frontend person | Typed client, dashboard, maps, charts, trust/error states, replay controls. | Uses fixture JSON before live API. | Integrates after API contract snapshot. |

| Research/documentation person | Literature/claims, split/metric registry, judge QA, demo narrative, evidence package. | Reviews each phase and records negative results. | Approves claim scope and final demo. |



Weekly integration points: freeze the data contract; freeze the API response; run the full replay; review metrics and failure states. No person should silently change a schema used by another role.


## 47. What must be built first

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 47 operational rather than descriptive: What must be built first. |
| **Owner** | All leads |
| **Inputs** | Research gates and delivery date |
| **Outputs** | Prioritized backlog and cut line |
| **Files / folders** | `docs/PRIORITIES.md` |
| **Command** | `make priority-check` |
| **Test** | Remove optional tech from critical path |
| **Failure and fallback** | Cut analog/deep model |
| **Definition of done** | MVP remains complete. The evidence is committed or stored with a checksum and linked from the phase report. |


| Priority | Items |

|---|---|

| MUST BUILD | Public pilot acquisition/QC; alignment; versioned q95 label engine; issue-safe features; E0–E4 baselines; calibration; leakage tests; OOD/abstention; Postgres metadata; FastAPI `/predict`; deterministic replay dashboard; provenance and claim banner. |

| SHOULD BUILD | Revision trajectory, spatial risk objects, lead trajectory, analog explanation, model comparison and export. |

| NICE TO HAVE | Multi-model disagreement, richer observations, tile maps, user feedback, MLflow. |

| EXPERIMENTAL | Self-supervised embeddings, GNN/transformer, conformal risk control, hazard model if data supports. |

| FUTURE RESEARCH | NCMRWF operational validation, continual learning, partner-grade uptime, multilingual impact products. |



## 48. MVP

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 48 operational rather than descriptive: MVP. |
| **Owner** | Product/research lead |
| **Inputs** | Core data/features/model/API/UI |
| **Outputs** | MVP release definition and fixture |
| **Files / folders** | `docs/MVP.md; demo/cases/` |
| **Command** | `make mvp-check` |
| **Test** | Run core replay and metrics |
| **Failure and fallback** | Return to data/labels |
| **Definition of done** | MVP proves research. The evidence is committed or stored with a checksum and linked from the phase report. |


| Version | Smallest proven system |

|---|---|

| MVP v1 | GEFS/ERA5 pilot → aligned features → q95 labels → spread baseline → logistic/GBM → calibration → strict test → API → dashboard replay. |

| MVP v2 | Revision features → lead trajectory → OOD/abstention → spatial regional map → analog explanation → provenance export. |

| Advanced version | Multi-model disagreement, object-based precipitation, optional learned representation and one advanced sequence/spatial model. |

| Final SIH version | Only modules with blocked ablation value, deterministic replay, honest claim scope, clean demo and complete evidence bundle. |



## 49. Final winning version

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 49 operational rather than descriptive: Final winning version. |
| **Owner** | Tech/research lead |
| **Inputs** | Passed optional-module ablations |
| **Outputs** | Final SIH release bundle |
| **Files / folders** | `release/; docs/RELEASE.md` |
| **Command** | `make release-candidate` |
| **Test** | Judge replay and claim audit |
| **Failure and fallback** | Use simpler final system |
| **Definition of done** | Only surviving modules included. The evidence is committed or stored with a checksum and linked from the phase report. |


The winning version is a **calibrated forecast-failure advisory**, not a weather-generation model. It displays bust probability, severity, spatial extent, Day 1–10 trajectory, revision intelligence, regime context, analog memory, OOD status, abstention, empirical uncertainty, explanation, replay, model comparison and provenance. Every advanced module is conditional on a surviving experiment; otherwise the system visibly falls back to a calibrated spread-only product.


## 50. Final data → frontend trace: one worked example

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 50 operational rather than descriptive: Final data → frontend trace: one worked example. |
| **Owner** | Demo operator |
| **Inputs** | One frozen GEFS/ERA5 replay case |
| **Outputs** | Detailed trace log and screenshots/exports |
| **Files / folders** | `demo/runbook.md; demo/cases/` |
| **Command** | `python -m demo.run CASE_ID --step-by-step` |
| **Test** | Compare stored IDs and output checksums |
| **Failure and fallback** | Fallback static replay |
| **Definition of done** | Judge sees full path. The evidence is committed or stored with a checksum and linked from the phase report. |


Assume a replay case with a GEFS cycle issued at `2025-07-01T00:00Z`, target `2025-07-07T00:00Z`, Z500, India region and lead 144 hours. The example is intentionally a replay: the verification is hidden until the reveal step.


```text
1. DOWNLOAD
   ingestion/gefs.py requests the declared source object for the selected issue/cycle.
   It writes data/raw/gefs/gefs_vX/2025-07-01/00/field.grib2.

2. STORE + MANIFEST
   manifest.json records URL, retrieval time, bytes, SHA-256, grid hash, member count and license URI.

3. PARSE
   xarray/cfgrib adapter normalizes variable=z500, units, latitude order and longitude convention.

4. ALIGN
   valid_time = issue_time + 144 h; the alignment table records run_id, lead_hours and grid transform.

5. FEATURES
   build_features reads the current members and only earlier cycles for the same valid target.
   It writes mean, spread, q10/q90, skew, revision_24h, acceleration, regime flags, static geography and availability timestamps.

6. MODEL
   InferenceFacade loads approved model gbm-traject-v3 and selects the z500/144h schema.
   Raw output is a score, not yet a trusted probability.

7. CALIBRATION
   calibration.pkl maps score to p_bust and provides an empirical interval/diagnostic.

8. OOD
   ood_reference.pkl checks feature distance, missingness, regime novelty and model version.
   Status becomes NORMAL, UNUSUAL, OOD or ABSTAIN.

9. ANALOGS
   The analog index searches earlier eligible cases, excluding the same event/time window.
   It returns two cards with similarity, region, lead and verified historical outcome.

10. STORE
    Postgres stores prediction_id, p_bust, severity, trust state and all versions.
    GeoJSON risk objects go to object storage; URI/checksum go to risk_maps.

11. API
    POST /v1/predict returns the PredictionEnvelope.
    GET /v1/risk-map returns the GeoJSON URI/objects.
    GET /v1/explanation returns feature evidence and analog cards.

12. FRONTEND
    The typed client caches the response, renders probability/severity, map and Day-4→Day-6 trajectory,
    then displays the provenance drawer and public-proxy claim banner.

13. JUDGE
    The operator advances the replay: apparently normal → revision instability → risk rises → spatial object appears →
    analog evidence → OOD/abstention case → verification reveal → spread-only comparison → metric evidence.
```


## 51. Failure scenarios

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 51 operational rather than descriptive: Failure scenarios. |
| **Owner** | QA/ops lead |
| **Inputs** | Failure catalog and fallback contracts |
| **Outputs** | Incident runbook and user messages |
| **Files / folders** | `docs/FAILURES.md; backend/app/errors.py` |
| **Command** | `python scripts/failure_injection.py` |
| **Test** | Inject each failure and verify response |
| **Failure and fallback** | Degrade safely |
| **Definition of done** | No silent failure. The evidence is committed or stored with a checksum and linked from the phase report. |


| Failure | Detection | Fallback | User-facing behavior | Developer action |

|---|---|---|---|---|

| GEFS download fails | Job status/retry/checksum missing. | Last successful replay or alternate approved source. | Data delayed banner; no invented current risk. | Inspect source/status, retry, record incident. |

| ERA5 unavailable | Verification job cannot fetch valid time. | Training pauses; live/replay prediction remains without new label. | Verification pending. | Use cached truth or wait; never label with substitute silently. |

| Forecast incomplete | Member count/dimensions QC. | Quarantine run; use previous approved run only with timestamp. | Incomplete cycle warning. | Fix adapter/source; update manifest. |

| Missing member | QC count and missingness feature. | Preserve missingness or refuse if threshold exceeded. | Reduced confidence/abstention. | Never fill with truth or hidden mean. |

| Database down | Readiness/connection error. | Read-only cached product or static replay bundle. | Service degraded. | Restore DB; no lost audit event. |

| Model unavailable | Artifact checksum/load failure. | Calibrated spread-only or unavailable. | Model unavailable; fallback named. | Rollback approved artifact. |

| OOD detected | OOD score/status threshold. | ABSTAIN or conservative human review. | No confident number; explain why. | Inspect distribution/version and log. |

| No analog | Index returns zero eligible hits. | No analog field; keep model score. | “No eligible analog found.” | Review archive coverage; not an error. |

| Spatial data unavailable | Map product missing. | Regional probability and trajectory. | Map unavailable; scalar remains. | Rebuild product/cache. |

| API fails | HTTP/timeout. | Client retry/backoff and last replay only. | Error with timestamp; no stale current value. | Inspect logs/request ID. |

| Frontend fails | Browser error/asset failure. | API/export links and static replay page. | Fallback runbook. | Fix deployment/build. |

| Cloud down | Health check/uptime. | Local demo bundle. | Service unavailable; claim scope unchanged. | Rollback/redeploy. |

| Training fails | Nonzero exit/metric absence. | Keep prior approved model. | No model promotion. | Read failure report and fix. |

| New model worse | Gate comparison/CIs. | Reject promotion. | Current model stays active. | Investigate data/labels/drift. |

| Version changes distribution | Version/grid/PSI/OOD. | Hold/abstain until validation. | Post-upgrade caution. | Create version holdout and recalibrate. |



## 52. Documentation we need

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 52 operational rather than descriptive: Documentation we need. |
| **Owner** | Research lead |
| **Inputs** | All claims, APIs and operations |
| **Outputs** | Documentation index and update policy |
| **Files / folders** | `docs/README.md; docs/CHANGELOG.md` |
| **Command** | `make docs-check` |
| **Test** | Broken-link/schema/coverage scan |
| **Failure and fallback** | Mark unknown; stop release |
| **Definition of done** | Docs match code. The evidence is committed or stored with a checksum and linked from the phase report. |


| File | Contents |

|---|---|

| 01_PROJECT_OVERVIEW.md | Mission, users, scope, non-goals and claim boundary. |

| 02_RESEARCH.md | Literature, hypothesis, gaps and contributions. |

| 03_ARCHITECTURE.md | Planes, components and request/data flows. |

| 04_DATA_SOURCES.md | Access, variables, licenses, proxy/NCMRWF boundary. |

| 05_DATA_PIPELINE.md | Acquisition, QC, alignment and storage. |

| 06_DATA_SCHEMA.md | Raw/processed/feature/label schema and lineage. |

| 07_LABELING_PROTOCOL.md | Bust definitions, thresholds, ambiguity, versioning. |

| 08_FEATURE_ENGINEERING.md | Formulas and issue-time contracts. |

| 09_ML_TRAINING.md | Training ladder, tuning and artifacts. |

| 10_MODEL_EVALUATION.md | Metrics, splits, bootstrap and ablations. |

| 11_OOD_ABSTENTION.md | Safety states, thresholds and coverage-risk. |

| 12_ANALOG_SYSTEM.md | Index, filters, leakage rules and evaluation. |

| 13_BACKEND.md | Services, lifecycle, jobs and fallbacks. |

| 14_API.md | OpenAPI-style endpoints and examples. |

| 15_DATABASE.md | ER diagram, schema, indexes, backups and migrations. |

| 16_FRONTEND.md | Pages, components, state and trust UX. |

| 17_DEPLOYMENT.md | Local/staging/production and rollback. |

| 18_MLOPS.md | Registry, promotion, drift and retraining. |

| 19_TESTING.md | Unit, data, leakage, integration and E2E. |

| 20_REPRODUCIBILITY.md | Manifests, seeds, commits and replay. |

| 21_SECURITY.md | Secrets, CORS, input/rate controls and audit. |

| 22_DEMO.md | Operator script and deterministic replay case. |

| 23_JUDGE_QA.md | Evidence-based hostile questions and answers. |

| 24_LIMITATIONS.md | Proxy data, verification, calibration and OOD caveats. |



## 53. Complete API documentation concept

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 53 operational rather than descriptive: Complete API documentation concept. |
| **Owner** | Backend lead |
| **Inputs** | Endpoint schemas and examples |
| **Outputs** | OpenAPI export and endpoint reference |
| **Files / folders** | `docs/14_API.md; openapi.json` |
| **Command** | `make openapi-export` |
| **Test** | Validate examples against server |
| **Failure and fallback** | Version endpoint |
| **Definition of done** | Contract published. The evidence is committed or stored with a checksum and linked from the phase report. |


All endpoints use JSON unless the response is an export. Query validation is strict: `lead_hours` must be one of the supported leads; variable and region must exist in the registry; `valid_time − issue_time` must equal lead; historical replay must identify a known run. Errors use `{code, message, request_id, retryable, details}`. Admin/training endpoints are not public.


| Endpoint | Auth | Success | Important errors |

|---|---|---|---|

| GET /health | Public/readiness | 200 `{status, api_version, model_loaded, db_ok}` | 503 dependency unavailable. |

| GET /v1/predict | Public or API key | PredictionEnvelope with provenance | 400 invalid selection; 409 product not ready; 503 fallback. |

| GET /v1/risk-map | Public/read-only | GeoJSON/URL + checksum | 404 no spatial product; 410 expired URL. |

| GET /v1/risk-trajectory | Public/read-only | Leadwise envelope | 422 unsupported lead/variable. |

| GET /v1/analogs | Public/read-only | Eligible cards + policy | 200 empty list is valid. |

| GET /v1/explanation | Public/read-only | Evidence and reason codes | 404 unknown prediction. |

| GET /v1/metrics | Protected if unpublished | Metric table + CI/scope | 403 private; 404 not evaluated. |

| GET /v1/metadata | Public/read-only | Licenses/versions/claim scope | Never expose secrets. |

| GET /v1/export | Protected or signed URL | Export URI/checksum | 400 bad format; 429 too many exports. |



## 54. Complete database documentation

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 54 operational rather than descriptive: Complete database documentation. |
| **Owner** | DB lead |
| **Inputs** | Migrations and entities |
| **Outputs** | Schema/ERD/backup/migration guide |
| **Files / folders** | `docs/15_DATABASE.md; db/` |
| **Command** | `make db-docs-check` |
| **Test** | Restore backup to clean DB |
| **Failure and fallback** | Rollback migration |
| **Definition of done** | Restore tested. The evidence is committed or stored with a checksum and linked from the phase report. |


Use migrations, not ad-hoc table creation. Every table has `created_at`, where appropriate `updated_at`, and a source/model/data version. Use composite uniqueness for forecast-run identity and prediction identity. Index time queries, source/issue time, region/variable/lead and model version. Large files are referenced by URI/checksum.


| Concern | Policy |

|---|---|

| Retention | Keep all artifacts used in published evidence; prune rebuildable cache by age. |

| Backup | Daily Postgres backup in hosted tier; object storage versioning/checksums; test restore before claiming resilience. |

| Migration | Alembic/SQL migration reviewed in Git; backup before production migration; no destructive migration without export. |

| Privacy | Avoid personal data in public demo; users are optional and minimal. |

| Audit | Record promotion, rollback, data-version changes and administrative actions. |



## 55. Complete ML documentation

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 55 operational rather than descriptive: Complete ML documentation. |
| **Owner** | ML lead |
| **Inputs** | Feature/label/model/evaluation schemas |
| **Outputs** | ML contract documentation |
| **Files / folders** | `docs/08_FEATURE_ENGINEERING.md; docs/09_ML_TRAINING.md` |
| **Command** | `make ml-docs-check` |
| **Test** | Match docs to artifact JSON schemas |
| **Failure and fallback** | Mark unsupported field |
| **Definition of done** | Schemas agree. The evidence is committed or stored with a checksum and linked from the phase report. |


| Schema | Required contents |

|---|---|

| Training architecture | Data sources, splits, label engine, feature blocks, model, calibration, OOD, selection gates. |

| Feature schema | Name, dtype, unit, formula, source, availability timestamp, missingness, leakage status. |

| Label schema | Variable/region/lead, truth source, error, normalization, threshold, ambiguity, severity, version. |

| Model schema | Input feature order, output score/probability, supported leads/variables, artifact checksum. |

| Evaluation schema | Split ID, metric, estimate, interval, bootstrap unit, baseline, claim scope. |

| Artifact schema | Paths, versions, configs, seeds, commit, environment, registry state. |



## 56. Complete deployment documentation

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 56 operational rather than descriptive: Complete deployment documentation. |
| **Owner** | DevOps lead |
| **Inputs** | Environments and release path |
| **Outputs** | Deployment runbook and rollback procedure |
| **Files / folders** | `docs/17_DEPLOYMENT.md; deploy/` |
| **Command** | `make deploy-docs-check` |
| **Test** | Staging → production dry run |
| **Failure and fallback** | Remain local |
| **Definition of done** | Health/rollback documented. The evidence is committed or stored with a checksum and linked from the phase report. |


```text
Git branch / pull request
  → lint + unit + leakage tests
  → build frontend/API images
  → scan/config validation
  → deploy staging
  → health + replay smoke test
  → human approval
  → production deploy
  → health check + model checksum check
  → monitor / rollback pointer
```


| Environment | Data/model policy | Purpose |

|---|---|---|

| Development | Local data fixture; debug logging; no production secrets. | Build and tests. |

| Staging | Same image and schema; synthetic or public replay; protected credentials. | Integration and demo rehearsal. |

| Production/demo | Approved artifact only; read-only data; HTTPS; monitoring; rollback. | Public/partner access. |



## 57. Exact technology stack

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 57 operational rather than descriptive: Exact technology stack. |
| **Owner** | Tech lead |
| **Inputs** | All candidate technologies and constraints |
| **Outputs** | Final one-stack ADR |
| **Files / folders** | `docs/adr/ADR-STACK.md` |
| **Command** | `make stack-check` |
| **Test** | Remove unused dependencies |
| **Failure and fallback** | Choose simpler alternative |
| **Definition of done** | Stack is minimal. The evidence is committed or stored with a checksum and linked from the phase report. |


| Layer | Recommended stack | Why chosen / removal consequence |

|---|---|---|

| Frontend | React + TypeScript + Vite | Simple typed dashboard; removing it leaves API-only system. |

| Map | Leaflet + GeoJSON | Low setup; replace with MapLibre only for tile/style need. |

| Charts | ECharts or Recharts | Trajectory/reliability rendering; keep one library. |

| Backend | FastAPI + Pydantic | Typed REST and Python-native ML; remove only by replacing the service contract. |

| ML | Python + pandas/polars + xarray + scikit-learn + LightGBM/XGBoost | Matches tabular/array workflow; advanced PyTorch optional. |

| Data | Zarr/NetCDF + Parquet | Correct data structures for arrays versus tables. |

| Database | PostgreSQL | Metadata/predictions/registry; do not use for arrays. |

| Cache | Filesystem/object cache; Redis optional | Avoid infra until measured need. |

| Vector | FAISS or Lance optional | Local analog retrieval; remove if explanation-only index is unnecessary. |

| Tracking | Filesystem registry + JSON/CSV; MLflow optional | Zero-cost reproducibility. |

| Containers | Docker Compose | Local parity and portable demo. |

| Deployment | Static frontend + one container/VM API + managed DB/object store when needed | Low cost and simple rollback. |

| Git | GitHub | Review, CI and evidence history. |



## 58. Why this architecture?

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 58 operational rather than descriptive: Why this architecture?. |
| **Owner** | Tech/research lead |
| **Inputs** | Architecture decisions and tradeoffs |
| **Outputs** | Decision register with removal consequences |
| **Files / folders** | `docs/adr/` |
| **Command** | `make adr-check` |
| **Test** | Every major tech has why/why-not |
| **Failure and fallback** | Delete unjustified layer |
| **Definition of done** | No technology soup. The evidence is committed or stored with a checksum and linked from the phase report. |


| Technology | Why this? | Why not another? | Necessary? | If removed |

|---|---|---|---|---|

| FastAPI | Python-native, typed, fast enough for GBM. | Microservices add deployment burden. | Yes for product. | CLI/replay only; no shared UI service. |

| Postgres | Relational integrity for metadata/predictions. | SQLite is fine locally; NoSQL not needed. | Yes for multi-user/staging, optional for offline. | Use JSON/SQLite but lose query/audit robustness. |

| Zarr/NetCDF | Scientific arrays and chunked reads. | Postgres/CSV are structurally wrong. | Yes for fields. | Small pilot can use NetCDF files only. |

| Parquet | Typed tabular ML rows. | CSV is slow/lossy. | Yes for features. | Small CSV fixture only. |

| React | Interactive trust/map UI. | Plain HTML less maintainable. | Yes for judge UI. | API still works. |

| Docker | Reproducible environment. | Manual setup drifts. | Recommended. | Documented local setup remains possible. |

| Redis/worker | Async/retry under load. | Not needed for one scheduled job. | No MVP. | Cron/synchronous CLI. |

| Vector index | Fast analog retrieval. | Linear scan works for small archive. | Optional. | Explanation uses precomputed top cards/linear search. |



## 59. Cost analysis

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 59 operational rather than descriptive: Cost analysis. |
| **Owner** | Project manager |
| **Inputs** | Hardware, cloud and deadline |
| **Outputs** | Budget/capacity sheet with tiers |
| **Files / folders** | `docs/COSTS.md` |
| **Command** | `python scripts/cost_check.py` |
| **Test** | Review monthly/one-time costs |
| **Failure and fallback** | Use ₹0/local tier |
| **Definition of done** | MVP affordable. The evidence is committed or stored with a checksum and linked from the phase report. |


| Tier | Storage | Compute/GPU | DB/backend/frontend | Monitoring | Decision |

|---|---|---|---|---|---|

| ₹0 | Local disk; public pilot only. | CPU GBM; no GPU. | Docker Postgres + localhost React/FastAPI. | Logs/files. | MVP default. |

| Low-cost | Small object store or MinIO/local backup. | Local CPU; optional short cloud GPU. | Static frontend + small API/VM; small managed DB optional. | Hosted logs/basic uptime. | SIH public demo. |

| Moderate | Versioned object store + backup. | Scheduled CPU/GPU experiment. | Managed Postgres + container service. | Error/latency dashboards. | Team/staging. |

| Production | Durable object store + DB backups. | Autoscaled CPU; GPU only for research. | CDN/WAF + container replicas + scheduler/worker. | Drift/calibration/uptime. | Partner pilot, not required for SIH. |



Cost control: bound the India domain, begin with Z500/T2m, use downsampled fields, cache immutable products, avoid full global archives, and do not build a GPU-dependent system. The scientific contribution is the label/evaluation/safety design, not cloud size.


## 60. Complete learning roadmap

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 60 operational rather than descriptive: Complete learning roadmap. |
| **Owner** | Team lead |
| **Inputs** | Student skill gaps and project tasks |
| **Outputs** | Learning backlog linked to milestones |
| **Files / folders** | `docs/LEARNING.md` |
| **Command** | `make learning-check` |
| **Test** | Each topic has exercise and SIH connection |
| **Failure and fallback** | Pair mentor/replace tool |
| **Definition of done** | Team can explain system. The evidence is committed or stored with a checksum and linked from the phase report. |


| Order | Need to know | Do not need yet | Exercise | SIH connection |

|---|---|---|---|---|

| 1 Git/GitHub | Commit, branch, pull request, ignore files. | Advanced Git internals. | Create repo and revert a change. | Evidence and teamwork. |

| 2 Python | Functions, types, exceptions, packaging. | Metaprogramming. | Write a manifest/checksum CLI. | Ingestion. |

| 3 NumPy/Pandas/Xarray | Arrays, tables, labeled dimensions. | Every optimization. | Compute ensemble mean/spread. | Features. |

| 4 NetCDF/Zarr | Coordinates, chunks, attributes, lazy reads. | Storage internals. | Read one field by region/lead. | Weather storage. |

| 5 APIs | HTTP, JSON, status codes. | Distributed systems theory. | Call a public endpoint and validate JSON. | Backend contract. |

| 6 FastAPI | Routes, Pydantic, dependency injection. | All ASGI internals. | Build `/health` and `/predict` mock. | Serving. |

| 7 PostgreSQL | Tables, keys, indexes, migrations. | DB administration. | Store a prediction/provenance row. | Audit. |

| 8 Docker | Images, Compose, env vars. | Kubernetes. | Run API+DB locally. | Reproducibility. |

| 9 ML training | Splits, features, baselines, metrics. | Deep learning first. | Train climatology/logistic/GBM on fixture. | Scientific proof. |

| 10 LightGBM/XGBoost | Trees, weighting, validation. | Every hyperparameter. | Compare spread-only versus GBM. | Core model. |

| 11 Calibration | Reliability, Brier, Platt/isotonic. | Unproved guarantees. | Plot reliability by lead. | Trust. |

| 12 OOD | Distance, drift, coverage-risk. | All UQ literature. | Hold out one regime and flag it. | Safety. |

| 13 Vector databases | Embeddings, filters, leakage exclusion. | Distributed vector ops. | Retrieve earlier analogs. | Memory. |

| 14 React/TypeScript | Components, types, query states. | Framework internals. | Render fixture PredictionEnvelope. | Dashboard. |

| 15 Maps | GeoJSON, layers, legends. | GIS production. | Render risk objects. | Spatial product. |

| 16 Cloud | Containers, env, storage, HTTPS. | Cloud certifications. | Deploy a static/API toy. | Demo. |

| 17 Deployment | Health, logs, rollback. | Multi-region operations. | Restart and recover local service. | Reliability. |

| 18 MLOps | Registry, lineage, drift, promotion. | Enterprise platforms. | Promote only a passing model. | Research claims. |



## 61. If you are confused, follow this

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 61 operational rather than descriptive: If you are confused, follow this. |
| **Owner** | Project manager |
| **Inputs** | Roadmap and current blocker |
| **Outputs** | Daily/weekly execution checklist |
| **Files / folders** | `docs/EXECUTION_CHECKLIST.md` |
| **Command** | `make status` |
| **Test** | Run next unchecked step only |
| **Failure and fallback** | Escalate blocker with evidence |
| **Definition of done** | No guessing. The evidence is committed or stored with a checksum and linked from the phase report. |


**STEP 1:** Create the repository and pin Python/Node dependencies.


**STEP 2:** Freeze the research claim sheet: public proxy now; NCMRWF validation only with paired archive.


**STEP 3:** Acquire a small GEFS/WeatherBench 2 + ERA5 pilot and write the manifest/checksums.


**STEP 4:** Validate dimensions, units, grid, timestamps and member completeness.


**STEP 5:** Align issue time, valid time and lead with deterministic tests.


**STEP 6:** Implement the q95 normalized Bust Label Engine plus q90/q97.5/q99 sensitivity and ambiguity.


**STEP 7:** Build issue-safe ensemble and revision features with availability timestamps.


**STEP 8:** Freeze temporal/event/region/version splits and run leakage tests.


**STEP 9:** Run climatology, persistence, spread-only and logistic baselines.


**STEP 10:** Train the GBM and keep it only if it adds value under blocked testing.


**STEP 11:** Calibrate on a later block and report reliability/Brier/ECE.


**STEP 12:** Add OOD and abstention; verify retained-case risk and coverage.


**STEP 13:** Build spatial/trajectory/analog modules one at a time and ablate each.


**STEP 14:** Package the approved model, calibration, OOD policy and provenance.


**STEP 15:** Implement FastAPI contracts and seed deterministic replay data.


**STEP 16:** Build the dashboard with trust/error/abstention states.


**STEP 17:** Run Docker Compose, integration, leakage and browser tests from a clean environment.


**STEP 18:** Deploy the low-cost demo and verify health/rollback.


**STEP 19:** Rehearse the 3–5 minute replay story.


**STEP 20:** Publish only claims supported by the final evidence bundle.


## 62. Final master checklist

### Execution card

| Field | Implementation specification |
|---|---|
| **Purpose** | Make Section 62 operational rather than descriptive: Final master checklist. |
| **Owner** | All leads |
| **Inputs** | Release criteria and artifacts |
| **Outputs** | Signed master checklist and claim sheet |
| **Files / folders** | `docs/RELEASE_CHECKLIST.md` |
| **Command** | `make release-check` |
| **Test** | Every checkbox links to evidence |
| **Failure and fallback** | Do not release |
| **Definition of done** | Release evidence complete. The evidence is committed or stored with a checksum and linked from the phase report. |


| Area | Done when |

|---|---|

| RESEARCH | [ ] Claim sheet, literature map, limitations and references reviewed. |

| DATA | [ ] Source/access/license/manifest/QC complete. |

| LABELS | [ ] Versioned q95 protocol plus sensitivity/ambiguity report. |

| FEATURES | [ ] Formula/availability/leakage schema and tests. |

| ML | [ ] Baselines/core/selection gates recorded. |

| CALIBRATION | [ ] Later-block reliability/Brier/ECE report. |

| OOD | [ ] Stress split, coverage-risk and status policy. |

| ANALOG | [ ] Exclusion tests and gain-or-explanation decision. |

| SPATIAL | [ ] Regional/grid product and suitable metrics. |

| BACKEND | [ ] Services, fallbacks, health and logs. |

| DATABASE | [ ] Migrations, indexes, backups and provenance. |

| API | [ ] OpenAPI/schema tests and version metadata. |

| FRONTEND | [ ] Map/trajectory/explanation/trust states. |

| INTEGRATION | [ ] Data→model→API→UI replay works. |

| TESTING | [ ] Leakage, unit, integration, E2E and deployment tests. |

| DEPLOYMENT | [ ] Clean startup, health, HTTPS/config and rollback. |

| DEMO | [ ] 3–5 minute deterministic story rehearsed. |

| PAPER | [ ] Gap→technology→experiment→result→contribution trace. |

| PRESENTATION | [ ] No-BS novelty, NCMRWF boundary, fallback and metrics ready. |



## Final recommended architecture

Build **Option B: a modular monolith**. The frontend is React/TypeScript and calls FastAPI. FastAPI validates requests and invokes an `InferenceFacade`. The facade reads forecast metadata and issue-safe feature products, loads an approved GBM/calibration/OOD bundle, returns either a calibrated risk or an explicit abstention, and enriches the result with spatial objects, lead trajectory and eligible analogs. PostgreSQL stores structured metadata and prediction records; Zarr/NetCDF and Parquet live in local or object storage; a filesystem registry tracks evidence; cron schedules ingestion; Docker Compose reproduces the system. The architecture evolves to a worker/separate ML service only after measurement shows a need.


This design is research-grade because every result has lineage, split/label versions, calibration/OOD state and claim scope. It is buildable because the MVP has three core services and no required GPU. It is deployable because the API/model bundle is containerized. It is explainable because evidence is numerical/analog-based rather than fabricated causal prose. It is judge-friendly because historical replay shows the entire chain: data arrives, forecast revisions change, risk rises, the system localizes the risk, confidence can fall to abstention, verification is revealed, and the result is compared with spread-only.



## Detailed Appendix A — Environment and configuration contract

### Required environment variables

| Variable | Required? | Used by | Example / rule |
|---|---:|---|---|
| `APP_ENV` | Yes | API/jobs | `local`, `staging` or `production`; never infer from hostname. |
| `DATABASE_URL` | Local/staging | API/migrations | Secret; never logged. |
| `OBJECT_STORE_URI` | Recommended | field/model/map repositories | Local path or S3-compatible URI. |
| `MODEL_REGISTRY_URI` | Yes | inference | Versioned directory/pointer, checksum verified at startup. |
| `DATA_MANIFEST_URI` | Yes | ingestion/inference | Immutable manifest; source/license/checksum included. |
| `CORS_ORIGINS` | Yes | API | Comma-separated allowlist; no wildcard in hosted mode. |
| `API_KEY` | Optional | protected endpoints | Store in secret manager/local `.env`, never Git. |
| `REDIS_URL` | Optional | worker/cache | Only when optional worker profile is enabled. |
| `LOG_LEVEL` | Yes | all services | `INFO` in staging/production; `DEBUG` only local. |

### Configuration rules

Configurations are YAML or JSON, validated at startup and copied into each run artifact. No notebook may contain a hidden path, threshold, seed or source URL. The model’s feature order is read from `feature_schema.json`, never reconstructed from alphabetical column order. A missing required setting stops startup with a typed error.

## Detailed Appendix B — Exact data and feature contracts

### Raw forecast object

```json
{
  "source": "gefs",
  "model_version": "gefs_vX",
  "issue_time": "2025-07-01T00:00:00Z",
  "valid_time_start": "2025-07-01T00:00:00Z",
  "valid_time_end": "2025-07-11T00:00:00Z",
  "cycle": "00",
  "variables": ["z500", "t2m"],
  "member_ids": ["c00", "p01"],
  "grid_hash": "sha256:...",
  "units": {"z500": "m", "t2m": "K"},
  "uri": "raw/gefs/gefs_vX/2025-07-01/00/field.grib2",
  "sha256": "...",
  "retrieved_at": "2026-08-23T12:00:00Z",
  "qc_status": "PASS"
}
```

### One regional training row

```json
{
  "row_key": "gefs|gefs_vX|2025-07-01T00:00Z|2025-07-07T00:00Z|144|INDIA_CORE|z500",
  "issue_time": "2025-07-01T00:00:00Z",
  "valid_time": "2025-07-07T00:00:00Z",
  "lead_hours": 144,
  "region_id": "INDIA_CORE",
  "variable": "z500",
  "cycle": "00",
  "model_version": "gefs_vX",
  "features": {
    "ensemble_mean": 5531.2,
    "ensemble_std": 42.8,
    "q10": 5478.1,
    "q90": 5584.9,
    "revision_24h": -31.4,
    "revision_acceleration": -12.7,
    "regime_probability": 0.71,
    "ood_score": 0.18
  },
  "target": {
    "bust_label": 0,
    "severity": 0.83,
    "ambiguity_flag": false,
    "label_confidence": "HIGH"
  },
  "availability": {
    "max_feature_availability_time": "2025-07-01T00:00:00Z",
    "truth_used_for_features": false
  },
  "versions": {
    "data_version": "gefs_pilot_v1",
    "feature_schema_version": "features_v4",
    "label_version": "labels_v3"
  }
}
```

Targets are present only in offline training/evaluation tables. The live feature table has the same key and feature fields but no target fields. The API never accepts a client-supplied target.

## Detailed Appendix C — API and error contract

### Prediction envelope rules

1. `valid_time − issue_time` must equal `lead_hours`.
2. `bust_probability` is a number only when `abstain=false` and `status` is supported.
3. `bust_probability` is `null` when `abstain=true`; the frontend must not replace it with zero, the raw score or a stale cached value.
4. Every response includes model, data, feature, label and claim-scope versions.
5. `truth_status=VERIFICATION_PENDING` is allowed in live/replay-before-reveal mode and never exposes future truth.
6. Maps are references to versioned GeoJSON/Zarr/NetCDF products, not unbounded arrays in JSON.

### Standard error shape

```json
{
  "error": {
    "code": "DATA_DELAYED",
    "message": "The requested issue cycle has not passed quality control.",
    "request_id": "req_01J...",
    "retryable": true,
    "details": {"last_successful_cycle": "2025-07-01T00:00:00Z"}
  }
}
```

Use stable codes: `INVALID_SELECTION`, `FORECAST_NOT_FOUND`, `DATA_DELAYED`, `FEATURE_UNAVAILABLE`, `MODEL_UNAVAILABLE`, `OOD_ABSTAIN`, `MAP_NOT_READY`, `NO_ANALOG`, `RATE_LIMITED`, `INTERNAL_ERROR`. A normal absence of analogs is not a server error.

## Detailed Appendix D — State machines

### Data lifecycle

`DISCOVERED → DOWNLOADING → DOWNLOADED → CHECKSUMMED → QC_PASS → ALIGNED → FEATURES_READY → INFERENCE_READY → PUBLISHED`. Failure transitions to `RETRYABLE_FAILURE` or `QUARANTINED`; only an operator or a corrected job can leave quarantine. Each transition writes a timestamp, job ID, error code and artifact checksum.

### Prediction lifecycle

`REQUESTED → RESOLVED → FEATURED → SCORED → CALIBRATED → SAFETY_CHECKED → ENRICHED → STORED → RETURNED`. If the safety check abstains, the terminal product is `ABSTAINED`, not `PUBLISHED_WITH_CONFIDENCE`. If only the map or analog is missing, the scalar prediction may return with a partial-product status.

### Model lifecycle

`CANDIDATE → VALIDATED → CALIBRATED → STRESS_TESTED → APPROVED → SERVING → RETIRED`. A model cannot jump from `CANDIDATE` to `SERVING`. Rollback moves the serving pointer to a previous `APPROVED` artifact and records the reason.

## Detailed Appendix E — CI/CD gates

| Pipeline stage | Checks | Blocks release? |
|---|---|---:|
| Formatting/static | Ruff/Black/type checks; frontend lint/type checks | Yes |
| Unit | Label, feature, API, OOD, repository and UI unit tests | Yes |
| Data contract | Fixture dimensions, units, keys, checksums and missingness | Yes |
| Leakage | Future timestamps, target fields, split/event/analog overlap | Yes |
| Model smoke | Train tiny fixture, reload artifact, deterministic prediction | Yes |
| API contract | OpenAPI examples and status/error schema | Yes |
| Integration | Ingest fixture → feature → model → API → Postgres | Yes |
| Browser E2E | Replay selection, map, trajectory, OOD and abstention states | Yes |
| Container | Compose startup, migrations, health and clean shutdown | Yes |
| Security | CORS, input limits, secret redaction and protected routes | Yes |
| Documentation | Links, version metadata, claim scope and runbook | Yes |

### Minimal GitHub Actions shape

```yaml
jobs:
  quality:
    steps:
      - checkout
      - install-pinned-environment
      - run: make lint
      - run: make test
      - run: make leakage-test
      - run: make api-contract-test
      - run: make build-images
      - run: make smoke
```

The exact action syntax may vary; the gate sequence must not. No deployment job promotes a model or code artifact if the leakage suite fails.

## Detailed Appendix F — Observability and incident response

Every request receives `request_id`; every scheduled job receives `job_id`; every prediction logs `prediction_id`, `model_version`, `data_version`, `feature_schema_version`, `ood_status`, `abstain`, latency and result status. Do not log raw credentials, personal data or full weather fields.

When an incident occurs, record: detection timestamp; affected source/run/model; user-visible behavior; last known good artifact; fallback activated; operator; root cause; repair; replay test; and whether claim scope changed. The fallback hierarchy is: approved cached product → calibrated spread-only product → static historical replay → explicit unavailable response. Never silently substitute a different truth source or later forecast cycle.

## Detailed Appendix G — Release evidence bundle

A release directory must contain `release_manifest.json`, source/data/license manifest, split manifest, feature and label schemas, model/calibration/OOD artifacts, metrics with block/event bootstrap intervals, ablation table, leakage-test log, API OpenAPI export, database migration version, Docker image digests, replay case manifest, screenshots/exports, known limitations and claim sheet. The judge demo is a view over this bundle, not an independent source of truth.


## References

[1]: https://www.ncei.noaa.gov/products/weather-climate-models/global-ensemble-forecast — NOAA Global Ensemble Forecast System (GEFS)

[2]: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview — Copernicus ERA5 single-level reanalysis dataset

[3]: https://weatherbench2.readthedocs.io/en/latest/data-guide.html — WeatherBench 2 data guide

[4]: https://rmets.onlinelibrary.wiley.com/doi/10.1002/met.1867 — NCMRWF NEPS description and validation paper

[5]: https://www.ncei.noaa.gov/products/weather-climate-models/global-forecast-system — NOAA Global Forecast System (GFS)

[6]: https://www.ecmwf.int/en/forecasts/datasets/open-data — ECMWF Open Data

[7]: https://zarr.dev/ — Zarr documentation

[8]: https://fastapi.tiangolo.com/ — FastAPI documentation

[9]: https://react.dev/ — React documentation

[10]: https://www.postgresql.org/docs/ — PostgreSQL documentation

The local SIH26079 research corpus and approved research strategy remain the primary scientific evidence base. Claims about NCMRWF historical validation, operational performance, calibration guarantees under arbitrary shift or model superiority must remain conditional unless directly supported by the final paired-data experiments.
