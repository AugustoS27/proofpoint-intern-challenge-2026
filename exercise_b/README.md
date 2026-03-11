# Streaming Service Lost Episodes — Data Cleaning Tool

A command-line tool that reads a corrupted CSV catalog of TV episodes, cleans and normalises the data, removes duplicates, and produces a sanitised output file along with a data quality report.

---

## Problem Description

A streaming platform ingested its catalog of series, seasons, and episodes without applying any validation or uniqueness checks. The resulting CSV contains:

- Missing or empty fields
- Invalid formats (non-numeric season/episode numbers, impossible dates)
- Duplicate entries for the same episode, sometimes with inconsistent titles, dates, or numbering

This tool processes that CSV and produces a clean, de-duplicated catalog.

---

## Project Structure

```
proofpoint-intern-challenge-2026/
├── main.py
├── input/
│   └── input_episodes.csv      ← input file (must be provided)
└── output/
    ├── episodes_clean.csv       ← generated: cleaned catalog
    └── report.md                ← generated: data quality report
```

---

## Requirements

- Python 3.10 or higher
- No external dependencies — uses only the standard library

---

## How to Run

1. Place your input CSV in the `input/` folder with the name `input_episodes.csv`.
2. Make sure the `output/` folder exists.
3. Run from the project root:

```bash
python main.py
```

The tool will print a summary to the console and write the two output files automatically.

### Expected console output

```
Input records  : 100
Output records : 60
Discarded      : 10
Corrected      : 20
Duplicates     : 30
```

---

## Input Format

The input CSV must have **exactly** these 5 columns in this order:

```
SeriesName,SeasonNumber,EpisodeNumber,EpisodeTitle,AirDate
```

The tool will stop with an error if:

- The file does not exist or is empty
- The header does not match the expected columns exactly
- Any row has fewer or more than 5 columns

---

## Input / Output Examples

### Missing and invalid fields

| Input row                             | Issue                              | Result                          |
| ------------------------------------- | ---------------------------------- | ------------------------------- |
| `,1,2,Pilot,2020-01-01`               | Empty series name                  | Discarded                       |
| `Breaking Bad,one,2,Pilot,2020-01-01` | Non-numeric season                 | Season set to 0                 |
| `Breaking Bad,1,2,,2020-01-01`        | Empty title                        | Title set to "untitled episode" |
| `Breaking Bad,1,2,Pilot,not a date`   | Invalid date                       | Date set to "unknown"           |
| `Breaking Bad,1,2,Pilot,2022-40-99`   | Impossible date                    | Date set to "unknown"           |
| `Breaking Bad,1,0,,`                  | Episode + title + date all missing | Discarded                       |

### Duplicate detection

| Record A                         | Record B                         | Duplicate? | Reason                           |
| -------------------------------- | -------------------------------- | ---------- | -------------------------------- |
| `Breaking Bad, 1, 5, Ozymandias` | `Breaking Bad, 1, 5, Felina`     | ✅ Yes     | Same (series, season, episode)   |
| `Breaking Bad, 0, 3, Pilot`      | `Breaking Bad, 0, 3, Pilot`      | ✅ Yes     | Same (series, 0, episode, title) |
| `Breaking Bad, 2, 0, Grilled`    | `Breaking Bad, 2, 0, Grilled`    | ✅ Yes     | Same (series, season, 0, title)  |
| `Breaking Bad, 0, 3, Pilot`      | `Breaking Bad, 0, 3, Ozymandias` | ❌ No      | Different title                  |

When duplicates are found, the record with the most complete information is kept (valid date > known title > known episode number > first seen).

---

## Technical Design

### Normalization

All text fields are trimmed and lowercased for both storage and comparison. Season and episode numbers are parsed with a regex (`[+]?(\d+)`) to correctly handle inputs like `" 3"`, `"3.5"`, or `"--2"`. Dates are validated against the format `YYYY-MM-DD` and rejected if unparseable or logically impossible (e.g. year 0).

### Quality Score

Each episode is assigned a quality score during normalization:

| Condition                  | Points |
| -------------------------- | ------ |
| Valid air date             | +100   |
| Known episode title        | +10    |
| Known episode number (> 0) | +1     |

This score is used during deduplication to select the best record among duplicates.

### Deduplication Keys

Three composite keys are used depending on which fields are known:

1. `(series, season, episode)` — when both numbers are known (≠ 0)
2. `(series, 0, episode, title)` — when season is unknown; title disambiguates
3. `(series, season, 0, title)` — when episode number is unknown; title disambiguates

The title is excluded from key 1 intentionally — the same episode may appear with slightly different titles due to data entry errors, and the numeric key is sufficient to identify it.

Deduplication uses a dictionary (`seen: dict[tuple, Episode]`) for O(1) lookups. The final output is sorted by `(series, season, episode)`.
