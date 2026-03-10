import csv
import re
import os
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
#  Data model
# ─────────────────────────────────────────────

class Episode:
    """Represents a single episode record from the CSV."""
    def __init__(self, series_name, season_number, episode_number, episode_title, air_date):
        self.series_name    = series_name
        self.season_number  = season_number
        self.episode_number = episode_number
        self.episode_title  = episode_title
        self.air_date       = air_date
        # Score used during deduplication to keep the most complete record
        self.quality        = 0

# ─────────────────────────────────────────────
#  Parsing
# ─────────────────────────────────────────────

def parse_episode(row: list[str]) -> Episode:
    """Builds an Episode from a csv.reader row (already split into fields)."""
    padded = (row + [""] * 5)[:5]
    return Episode(*padded)

# ─────────────────────────────────────────────
#  Normalisation helpers
# ─────────────────────────────────────────────

def normalize_series_name(text: str) -> str:
    """Trims, collapses inner whitespace, and lowercases the series name."""
    return re.sub(r"\s+", " ", text.strip()).lower()

def normalize_episode_title(text: str) -> str:
    """Cleans the title; returns 'untitled episode' if empty."""
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        return "untitled episode"
    return cleaned.lower()

def normalize_numbers(number_str: str) -> int:
    """
    Converts a string to a positive integer.
    Returns 0 for empty, non-numeric, zero, or negative values.
    Uses regex to correctly reject inputs like '3.5', '--2', or 'one'.
    """
    match = re.fullmatch(r"[+]?(\d+)", number_str.strip())
    if match:
        value = int(match.group(1))
        return value if value > 0 else 0
    return 0

def normalize_date(date_str: str) -> str:
    """
    Validates and reformats a date string to YYYY-MM-DD.
    Returns 'unknown' if the date is missing, unparseable, or logically impossible.
    """
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        if dt.year == 0:
            return "unknown"
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return "unknown"

# ─────────────────────────────────────────────
#  Episode normalisation + discard logic
# ─────────────────────────────────────────────

def normalize_episode(episode: Episode) -> tuple:
    """
    Applies all field-level cleaning rules to an episode in place.

    Discard rules (returns flag_discard=True):
      - Series name is empty after cleaning
      - Episode number, title, and air date are all missing simultaneously

    Correction tracking:
      - flag_corrected=True if any field value changed during normalisation

    Quality score (used later for deduplication):
      - +100 for a valid air date
      - +10  for a known episode title
      - +1   for a known episode number
    """
    flag_discard   = False
    flag_corrected = False

    # Series name must be checked after stripping — "   " should also be discarded
    episode.series_name = normalize_series_name(episode.series_name)
    if not episode.series_name:
        return episode, True, False

    # Snapshot of raw values to detect corrections later
    original = (episode.season_number, episode.episode_number,
                episode.episode_title, episode.air_date)

    episode.episode_title  = normalize_episode_title(episode.episode_title)
    episode.season_number  = normalize_numbers(episode.season_number)
    episode.episode_number = normalize_numbers(episode.episode_number)
    episode.air_date       = normalize_date(episode.air_date)

    # Compare normalised values against original to flag corrections
    corrected = (str(episode.season_number), str(episode.episode_number),
                 episode.episode_title, episode.air_date)
    if corrected != original:
        flag_corrected = True

    # Calculate quality score
    calidad_acumulada = 0
    if episode.air_date       != "unknown":          calidad_acumulada += 100
    if episode.episode_title  != "untitled episode": calidad_acumulada += 10
    if episode.episode_number  > 0:                  calidad_acumulada += 1
    episode.quality = calidad_acumulada

    # Discard if the three identifying fields are all missing
    if (episode.episode_number == 0 and
        episode.episode_title  == "untitled episode" and
        episode.air_date       == "unknown"):
        flag_discard = True

    return episode, flag_discard, flag_corrected

# ─────────────────────────────────────────────
#  Deduplication
# ─────────────────────────────────────────────

def get_dedup_key(episode: Episode) -> tuple:
    """
    Returns the composite key used to identify duplicate episodes.

    Three key types depending on which fields are known:
      - (series, season, episode)        → both numbers known
      - (series, 0, episode, title)      → season unknown; title disambiguates
      - (series, season, 0, title)       → episode number unknown; title disambiguates

    The title is excluded from the primary key intentionally: the same episode
    may appear with slightly different titles due to data entry errors.
    """
    sn = episode.series_name
    t  = episode.episode_title

    if episode.season_number == 0:
        return (sn, 0, episode.episode_number, t)

    if episode.episode_number == 0:
        return (sn, episode.season_number, 0, t)

    return (sn, episode.season_number, episode.episode_number)


def add_episode(seen: dict, new_episode: Episode) -> bool:
    """
    Attempts to add an episode to the deduplicated catalog.

    If the key already exists, keeps the record with the higher quality score.
    Returns True if the episode was a duplicate, False if it was new.
    """
    key = get_dedup_key(new_episode)

    if key in seen:
        # Replace existing record only if the new one has better quality
        if new_episode.quality > seen[key].quality:
            seen[key] = new_episode
        return True  # duplicate

    seen[key] = new_episode
    return False  # new entry

# ─────────────────────────────────────────────
#  Output
# ─────────────────────────────────────────────

def export_episodes_to_csv(episodes: list[Episode], output_path: str):
    """Writes the cleaned and sorted episode list to a CSV file."""
    with open(output_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["SeriesName", "SeasonNumber", "EpisodeNumber", "EpisodeTitle", "AirDate"])
        for episode in episodes:
            writer.writerow([
                episode.series_name,
                episode.season_number,
                episode.episode_number,
                episode.episode_title,
                episode.air_date
            ])


def generate_report(total, discarded, corrected, duplicates, output_path):
    """Writes a Markdown report summarising the data quality metrics."""
    output_records = total - discarded - duplicates
    report = f"""# Data Quality Report

## Summary

| Metric                  | Count |
|-------------------------|-------|
| Total input records     | {total} |
| Total output records    | {output_records} |
| Discarded entries       | {discarded} |
| Corrected entries       | {corrected} |
| Duplicates detected     | {duplicates} |

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

All text fields are also trimmed and normalised (collapsed whitespace, lowercased).

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
"""
    with open(output_path, mode='w', encoding='utf-8') as f:
        f.write(report)

# ─────────────────────────────────────────────
#  Main pipeline
# ─────────────────────────────────────────────

def read_episodes_from_csv(file_path: str, path_file_output: str, path_report_output: str):
    """
    Full pipeline: reads the input CSV, normalises and deduplicates each record,
    then writes the clean catalog and quality report to the output paths.
    """
    seen       = {}   # key → best Episode seen so far
    total      = 0
    discarded  = 0
    corrected  = 0
    duplicates = 0

    EXPECTED_HEADERS = ["SeriesName", "SeasonNumber", "EpisodeNumber", "EpisodeTitle", "AirDate"]

    # ── File-level validation ────────────────────────────────────────────────
    if not os.path.exists(file_path):
        print(f"Error: File not found -> {file_path}")
        return

    if os.path.getsize(file_path) == 0:
        print("Error: CSV file is empty")
        return

    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.reader(file)

        # ── Header validation ────────────────────────────────────────────────
        try:
            headers = next(reader)
        except StopIteration:
            print("Error: CSV file has no content")
            return

        if headers != EXPECTED_HEADERS:
            print("Error: Invalid CSV headers")
            print(f"Expected: {EXPECTED_HEADERS}")
            print(f"Found:    {headers}")
            return

        # ── Row processing ───────────────────────────────────────────────────
        for row in reader:
            total += 1
            episode = parse_episode(row)
            episode, flag_discard, flag_corrected = normalize_episode(episode)

            if flag_discard:
                discarded += 1
                continue

            if flag_corrected:
                corrected += 1

            is_dup = add_episode(seen, episode)
            if is_dup:
                duplicates += 1

    # ── Sort and export ──────────────────────────────────────────────────────
    episodes_sorted = sorted(
        seen.values(),
        key=lambda e: (e.series_name, e.season_number, e.episode_number)
    )

    export_episodes_to_csv(episodes_sorted, path_file_output)
    generate_report(total, discarded, corrected, duplicates, path_report_output)

    print(f"Input records  : {total}")
    print(f"Output records : {total - discarded - duplicates}")
    print(f"Discarded      : {discarded}")
    print(f"Corrected      : {corrected}")
    print(f"Duplicates     : {duplicates}")


def main():
    # Resolve paths relative to the script location so the tool works
    # regardless of the directory it is run from
    base_dir = Path(__file__).resolve().parent

    path_file_input    = base_dir / "input"  / "input_episodes.csv"
    path_file_output   = base_dir / "output" / "episodes_clean.csv"
    path_report_output = base_dir / "output" / "report.md"

    read_episodes_from_csv(
        str(path_file_input),
        str(path_file_output),
        str(path_report_output)
    )

if __name__ == "__main__":
    main()