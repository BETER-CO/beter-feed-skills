# Catalog: scope, snapshot, refresh, detectors

The catalog is the set of values the feed can send: the type enumerations for each
discipline, the scoreboard stages, the incident types with their permitted parameter
keys, and the code lists that are the same for every discipline.

It is published as documentation tables. There is no endpoint that returns it and no
machine-readable form — the feed's HTTP API covers booking and recovery only. So the
catalog reaches the repository as a **snapshot**, taken through the `feed-docs` skill and
committed.

## Parts

Read this file first. Read each part when its phase starts, and not before.

| Part | Covers | Read when |
|---|---|---|
| `references/catalog/01-scope.md` | *Discipline scope*; *Bringing a discipline into scope, and deferring one*; *Bindings* | Declaring scope (mapping mode Step 1), or reading or writing `beter-feed/bindings.yaml` |
| `references/catalog/02-snapshot.md` | *Snapshot, not lookup* and its three files; *What a score parameter counts*; *Acquisition is one isolated step*, with *Extracting* and *Merging into the committed catalog* through `bin/merge-catalog.py`; *Refresh* | Taking, extending or refreshing the snapshot (Step 2), or refreshing a sport |
| `references/catalog/03-coverage.md` | *What each detector catches*; *Coverage is three measurements, not one failure*, its denominators, what is actionable, and the report | Reporting coverage (Step 5) |
