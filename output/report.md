# Data Quality Report

## Summary

| Metric                  | Count |
|-------------------------|-------|
| Total input records     | 3 |
| Total output records    | 2 |
| Discarded entries       | 1 |
| Corrected entries       | 1 |
| Duplicates detected     | 0 |

## Discard Reasons

Records were permanently removed for the following reasons:

- **Missing series name**: a series name is required to associate an episode
  to a show. Without it the record is unidentifiable and is dropped.
- **Episode number + title + air date all missing**: when none of the three
  fields that differentiate episodes within a season are present, the record
  carries no useful information and is dropped.

## Field Correction Rules

When a field is present but invalid, it is corrected rather than discarded:

| Field          | Invalid condition                              | Correction applied        |
|----------------|------------------------------------------------|---------------------------|
| Season Number  | Empty, non-numeric, negative, or zero          | Set to 0                  |
| Episode Number | Empty, non-numeric, negative, or zero          | Set to 0                  |
| Episode Title  | Empty or whitespace only                       | Set to "untitled episode" |
| Air Date       | Empty, unparseable, or logically impossible    | Set to "unknown"          |

All text fields are also trimmed and normalized (collapsed whitespace, lowercased).

## Deduplication Strategy

Two episodes are considered duplicates when they share the same normalised
series name and at least one of the following composite keys:

1. **(series, season, episode)** — primary key used when both season and
   episode numbers are known (≠ 0). The title is intentionally excluded
   because the same episode may appear with slightly different titles due
   to data entry errors.

2. **(series, 0, episode, title)** — used when the season number is unknown.
   The title is included to avoid collapsing different episodes that share
   the same episode number but belong to different seasons.

3. **(series, season, 0, title)** — used when the episode number is unknown.
   The title is included to avoid collapsing different episodes that share
   the same season number.

When duplicates are found, the **best** record is kept following this priority:

1. Valid Air Date over "unknown"
2. Known Episode Title over "untitled episode"  
3. Known Episode Number (> 0)
4. First entry encountered in the file (tie-breaker)
