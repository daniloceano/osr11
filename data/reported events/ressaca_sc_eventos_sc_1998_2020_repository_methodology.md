# Documentary search and curation protocol for additional `ressaca` events on the coast of Santa Catarina (1998–2020)

## Purpose

This document describes the documentary search strategy, source-screening logic, and record-curation procedure used to assemble a supplementary table of coastal `ressaca` events for Santa Catarina, Brazil, covering the period from **1998-01-01** to **2020-12-31**.

The emphasis of this workflow was not simply to collect generic disaster reports, but to **systematically hunt for traceable evidence of marine-forced coastal impact** at municipality level, in a way that could support subsequent scientific use in event validation, historical auditing, and threshold-calibration workflows.

The associated dataset is:

- `ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv`

## Research rationale

Historical coastal-impact datasets in Brazil are often fragmented across heterogeneous documentary sources: local news archives, technical reports, academic theses and dissertations, institutional bulletins, and retrospective coastal-risk studies. Because of this fragmentation, assembling a usable event table required a **forensic-style documentary search**, similar to the workflow a doctoral researcher would use when reconstructing an incomplete hazard chronology from dispersed evidence.

Accordingly, the search strategy combined:

1. **broad exploratory searches**, to identify which institutions and archives recurrently reported storm-tide or `ressaca` impacts in Santa Catarina;
2. **targeted source chasing**, in which references discovered in one document were used to locate older or more detailed supporting material;
3. **event-by-event extraction**, retaining only municipality-date pairs supported by explicit textual evidence of coastal marine forcing.

## Event definition

For the purposes of this dataset, an event was considered eligible when the source provided evidence consistent with **marine-forced coastal disturbance**, including one or more of the following:

- `ressaca do mar`;
- strong-wave coastal impact;
- marine water intrusion into built-up coastal areas;
- storm-tide / positive sea-level coastal inundation;
- overtopping or shoreline erosion explicitly associated with wave action or elevated coastal water levels.

The following cases were excluded unless a coastal-marine component was explicitly documented:

- rainfall-only flooding;
- inland flash flooding or river flooding;
- wind damage without documented coastal inundation or wave action;
- generic civil-defence emergency reports lacking clear reference to marine processes.

## Search strategy

### 1. Source families pursued

The search prioritized source types that tend to preserve dated and location-specific evidence of coastal impacts:

- state and municipal civil-defence material;
- technical coastal-monitoring publications;
- university repositories containing theses, dissertations, and technical monographs;
- regional and state-level news archives;
- conference abstracts or technical proceedings when they contained explicit event references;
- institutional materials related to sea level, coastal inundation, or storm-wave impacts.

### 2. Search logic

Searches were conducted iteratively, moving from generic expressions to municipality- and year-specific combinations. In practice, the workflow resembled the following pattern:

- broad searches such as `ressaca Santa Catarina [year]`;
- municipality-focused searches such as `ressaca do mar Florianópolis 2010`, `avanço do mar Itapema`, `inundação costeira Balneário Camboriú`;
- thematic searches combining marine process language and impact language, such as `ondas fortes`, `maré positiva`, `água do mar invadiu`, `erosão costeira`, `casas atingidas pela ressaca`;
- archive chasing based on bibliographies, figures, tables, and narrative descriptions found in academic documents.

The search was intentionally **redundant and cross-referential**: the same episode was often sought through multiple phrasing combinations because coastal events are inconsistently described across documents.

### 3. Why academic repositories became central

During the search, university repositories proved especially valuable because they often aggregated years of otherwise ephemeral local reporting into structured tables, inventories, or narrated case reconstructions. These materials were particularly useful when they:

- provided municipality-specific event dates;
- made their inclusion criteria explicit;
- grouped consecutive days into single episodes, facilitating cleaner event logic;
- cited the journalistic or institutional sources originally used to reconstruct the chronology.

For this reason, repository-based academic documents became a major anchor for the curation process, complemented by technical and journalistic sources for additional confirmation or contextualization.

## Screening and inclusion procedure

Each candidate record passed through a staged screening process.

### Stage A — documentary relevance

A source was kept for detailed reading only if it appeared capable of providing at least one of the following:

- a dated event description;
- an identifiable affected coastal municipality;
- explicit mention of marine forcing or coastal inundation;
- a structured event inventory.

### Stage B — event-level evidence

A candidate municipality-date pair was extracted only when the source text clearly supported the interpretation that a coastal `ressaca`-type episode had occurred. Preference was given to cases where the source stated, directly or in close paraphrase, that:

- the sea advanced onto streets, houses, or public space;
- wave action or elevated water levels affected the coastal margin;
- coastal flooding, seawater intrusion, or marine overtopping was observed;
- the event was part of a documented coastal-inundation episode.

### Stage C — municipality resolution

Whenever a source named several affected municipalities within the same episode, each municipality was retained as a **separate row**, preserving a one-row-per-municipality-per-date structure.

### Stage D — temporal resolution

Preference was given to the **date of occurrence**, not the publication date. When the source described a multi-day event window, the dataset generally records the **episode start date** as the representative date, with this interpretation preserved in the notes field.

## Data curation and standardization

Once event candidates were extracted, the following standardization steps were applied.

### Municipality names

Municipality names were harmonized to a single canonical form in Portuguese, avoiding spelling drift, formatting differences, or mixed naming conventions.

### Dates

Dates were converted to ISO format (`YYYY-MM-DD`).

When the source described a date range rather than a single day, a representative date was assigned according to the following logic:

1. use the explicit onset date when available;
2. if only an event window was provided, use the earliest day of the documented window;
3. document this decision in `notes`.

### Coastal sector attribution

The `coastal_sector` field follows a fixed sectoral taxonomy:

- `North`
- `Central-north`
- `Central`
- `Central-south`
- `South`

Sector attribution was assigned by municipality. When a municipality-sector match was not explicit in the underlying documentation, the sector was inferred from consistent regional coastal geography and flagged in the notes when appropriate.

## Deduplication logic

Because documentary sources often re-report the same episode in slightly different ways, deduplication was treated as a core research step rather than a final housekeeping task.

The primary event key was:

- **(`city`, `date`)**

In addition, a conservative episode-level review was applied to avoid double counting when:

- the same municipality appeared with dates differing by only one day;
- the source narrative clearly indicated the same continuous event;
- multiple documents used different publication dates for what was evidently the same marine episode.

For multi-day episodes, the objective was to represent **one municipality-level episode**, not one line per reporting day.

## Quality control philosophy

This was a **documentary evidence dataset**, not an instrumental detection product. Therefore, quality control focused on traceability and interpretability:

- every retained record is linked to a source title and URL;
- event-level notes were used to document date interpretation, representative-date choices, and any cautionary issues;
- ambiguous or weakly supported cases were excluded rather than retained speculatively.

This conservative approach favors **auditability over exhaustiveness**.

## Main limitations

### 1. Incomplete documentary universe

The historical record of `ressaca` events is not fully centralized. Many local reports are ephemeral, poorly indexed, or unavailable in searchable form. As a result, the dataset should be interpreted as a **curated supplement**, not a complete census of all coastal storm impacts in Santa Catarina.

### 2. Uneven temporal and spatial documentation

Some municipalities and coastal sectors are much better documented than others. This means the event density in the table partly reflects **source availability**, not only the true distribution of historical impacts.

### 3. Dependence on narrative reconstruction

A substantial share of the evidence comes from narrative or retrospective sources, especially academic documents that synthesize prior reporting. These sources are extremely useful for event hunting, but they may inherit the biases of the documentary material they compiled.

### 4. Representative dates for multi-day episodes

Reducing a multi-day event to one representative date is useful for deduplication and municipality-level analysis, but it simplifies event duration and may slightly shift timing relative to hydrodynamic maxima.

### 5. Documentary rather than instrumental validation

This table does not by itself verify the hydrodynamic magnitude of each event. It identifies documentary evidence of occurrence. Additional event-by-event validation with tide-gauge data, wave reanalyses, and synoptic diagnostics remains desirable for high-confidence physical interpretation.

## Recommended scientific use

This dataset is appropriate for:

- documentary auditing of historical coastal-impact episodes;
- validation support for coastal hazard detection frameworks;
- municipality-based cross-checking of modeled or detected compound events;
- construction of a historical evidence layer for threshold calibration and event screening.

It should be used with care in analyses that assume complete reporting through time or homogeneous detectability across municipalities.

## Output file

- `ressaca_sc_eventos_sc_1998_2020_consolidated_expandido.csv`

## Suggested next step

The strongest next step for scientific robustness is to pair this documentary archive with an **instrumental verification layer**, combining sea-level anomalies, wave conditions, timing uncertainty, and municipality-to-grid linkage metadata for each retained event.
