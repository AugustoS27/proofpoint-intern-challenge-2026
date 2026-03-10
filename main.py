import csv
import re
import os
from datetime import datetime
from pathlib import Path

class Episode:
    def __init__(self, series_name, season_number, episode_number, episode_title, air_date):
        self.series_name    = series_name
        self.season_number  = season_number
        self.episode_number = episode_number
        self.episode_title  = episode_title
        self.air_date       = air_date
        self.quality        = 0

def parse_episode(row: list[str]) -> Episode:
    padded = (row + [""] * 5)[:5]
    return Episode(*padded)

def normalize_series_name(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()

def normalize_episode_title(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        return "untitled episode"
    return cleaned.lower()

def normalize_numbers(number_str: str) -> int:
    match = re.fullmatch(r"[+]?(\d+)", number_str.strip())
    if match:
        value = int(match.group(1))
        return value if value > 0 else 0
    return 0

def normalize_date(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        if dt.year == 0:
            return "unknown"
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return "unknown"


def normalize_episode(episode: Episode) -> tuple:
    flag_discard = False
    flag_corrected = False

    episode.series_name = normalize_series_name(episode.series_name)
    if not episode.series_name:
        return episode, True, False

    original = (episode.season_number, episode.episode_number,
                episode.episode_title, episode.air_date)

    episode.episode_title  = normalize_episode_title(episode.episode_title)
    episode.season_number  = normalize_numbers(episode.season_number)
    episode.episode_number = normalize_numbers(episode.episode_number)
    episode.air_date       = normalize_date(episode.air_date)

    corrected = (str(episode.season_number), str(episode.episode_number), episode.episode_title, episode.air_date)

    if corrected != original:
        flag_corrected = True

    calidad_acumulada = 0
    if episode.air_date       != "unknown":          calidad_acumulada += 100
    if episode.episode_title  != "untitled episode": calidad_acumulada += 10
    if episode.episode_number  > 0:                  calidad_acumulada += 1
    episode.quality = calidad_acumulada

    if (episode.episode_number == 0 and
        episode.episode_title  == "untitled episode" and
        episode.air_date       == "unknown"):
        flag_discard = True

    return episode, flag_discard, flag_corrected


def get_dedup_key(episode: Episode) -> tuple:
    sn = episode.series_name
    t  = episode.episode_title

    if episode.season_number == 0:
        return (sn, 0, episode.episode_number, t)

    if episode.episode_number == 0:
        return (sn, episode.season_number, 0, t)

    return (sn, episode.season_number, episode.episode_number)


def add_episode(seen: dict, new_episode: Episode) -> bool:
    key = get_dedup_key(new_episode)

    if key in seen:
        if new_episode.quality > seen[key].quality:
            seen[key] = new_episode
        return True

    seen[key] = new_episode
    return False


def generate_report(total, discarded, corrected, duplicates, output_path):
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

"""
    with open(output_path, mode='w', encoding='utf-8') as f:
        f.write(report)

def read_episodes_from_csv(file_path: str, path_file_output: str, path_report_output: str):
    seen       = {}
    total      = 0
    discarded  = 0
    corrected  = 0
    duplicates = 0
    
    EXPECTED_HEADERS = ["SeriesName","SeasonNumber","EpisodeNumber","EpisodeTitle","AirDate"]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found -> {file_path}")
        return

    if os.path.getsize(file_path) == 0:
        print("Error: CSV file is empty")
        return

    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.reader(file)

        try:
            headers = next(reader)
        except StopIteration:
            print("Error: CSV file has no content")
            return

        if headers != EXPECTED_HEADERS:
            print("Error: Invalid CSV headers")
            print(f"Expected: {EXPECTED_HEADERS}")
            print(f"Found: {headers}")
            return

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

def export_episodes_to_csv(episodes: list[Episode], output_path: str):
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


def main():
    # Ruta base del proyecto (directorio donde está el script)
    base_dir = Path(__file__).resolve().parent

    path_file_input    = base_dir / "input" / "input_episodes.csv"
    path_file_output   = base_dir / "output" / "episodes_clean.csv"
    path_report_output = base_dir / "output" / "report.md"

    read_episodes_from_csv(
        str(path_file_input),
        str(path_file_output),
        str(path_report_output)
    )

if __name__ == "__main__":
    main()