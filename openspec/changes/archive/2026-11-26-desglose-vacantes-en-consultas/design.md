# Design

## Context

See `proposal.md` for the motivation and `specs/observabilidad-operativa/spec.md` for the required behavior. Each source query already stores one `OperationalRun` with `item_count`; `save_listing` already determines whether a vacancy was created and whether material fields changed. The observability view aggregates those runs and displays the existing result count.

The refresh path has both per-profile queries and shared queries that may serve more than one profile. Counts must describe one source query and its unique returned vacancies, not multiply the result by the number of profiles. Existing operational runs lack enough evidence to reconstruct the new breakdown.

## Goals / Non-Goals

**Goals:**

- Persist a trustworthy outcome breakdown on the same operational run as the source query.
- Keep metrics consistent across individual and shared refresh paths.
- Display per-run counts and period totals with labels that prevent confusing repeated sightings with distinct jobs.
- Preserve historical query rows while identifying their breakdown as unavailable.

**Non-Goals:**

- Backfill new/known counts for old runs from current vacancy data; current state cannot establish what existed at the time of those runs.
- Show profile identity, CV data, search phrases, locations, job titles, or descriptions in observability.
- Change how vacancy identity, profile discovery, matching, or source query results are deduplicated.

## Decisions

1. **Store counts on `OperationalRun`.** Add nullable counters for newly inserted vacancies, already-known vacancies, known vacancies with material updates, and known vacancies without material updates. `item_count` remains the total unique result count. Nullable fields distinguish old or unclassifiable runs from successful runs with a true count of zero. A separate metrics table or JSON payload was considered, but dedicated numeric columns are easier to validate, aggregate, and render.

2. **Count at persistence time using the existing save outcome.** The ingestion flow already receives a `created` result from saving each listing and a material-change flag for existing rows. Accumulate the counters from those outcomes as each result is saved, then persist them with the source query run. Avoid inferring counts later from timestamps, because concurrent searches or another profile can update the same vacancy during the query.

3. **Keep invariants explicit.** For a fully classified query, `item_count = new_count + known_count`, and `known_count = known_updated_count + known_unchanged_count`. A new catalog record remains new even if it is linked to several profiles by a shared query. A known record is never counted as new merely because another profile sees it.

4. **Summarize occurrences, not period-wide distinct jobs.** Per-source totals sum the classifications recorded by each query in the selected period. Repeated sightings in separate queries therefore appear repeatedly in these totals; the interface labels this clearly. Counts for shared queries are recorded once for that query.

5. **Do not reconstruct legacy values.** Migration leaves counters null for existing rows. The dashboard renders an unavailable marker for these rows and excludes null values from classified totals, while retaining their existing `item_count` in the general historical metrics.

## Risks / Trade-offs

- [A listing can be classified as known in a concurrent query after another query creates it] → Use the outcome returned by the transactional save operation as the source of truth; each query's counters describe the actual persistence outcome at its save time.
- [Material-change classification may evolve as structured fields change] → Reuse the existing material-change definition and document the label as the system's current material update check.
- [The source history table gains several columns] → Keep a compact display, grouping updated and unchanged under known results where the layout requires it, while preserving visible numeric counts.
- [Legacy runs cannot show the breakdown] → Render “No disponible” instead of zero and keep the start of metric coverage visible.

## Migration Plan

1. Add nullable counters to operational query runs without rewriting or deleting existing history.
2. Deploy ingestion instrumentation and observability rendering together so new queries populate and display the values.
3. If rollback is needed, revert the application code; nullable counters and stored values can remain unused without affecting existing behavior.

