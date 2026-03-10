import csv
import os
from datetime import datetime

class Episode:
    def __init__(self, series_name, season_number, episode_number, episode_title, air_date):
        self.series_name = series_name
        self.season_number = season_number
        self.episode_number = episode_number
        self.episode_title = episode_title
        self.air_date = air_date
        self.quality = 0

def parse_episode(row: str, splitter=",") -> Episode:
    fields = row.strip().split(splitter)
    series_name = str(fields[0])
    season_number = str(fields[1])
    episode_number = str(fields[2])
    episode_title = str(fields[3])
    air_date = str(fields[4])
    return Episode(series_name, season_number, episode_number, episode_title, air_date)

def normalize_series_name(text: str) -> str:
    return text.strip().lower()

def normalize_episode_title(text: str) -> str:
    if not text:
        return "untitled episode"
    return text.strip().lower()

def normalize_numbers(number_str: str) -> int:
    if not (number_str.isdigit() and int(number_str) > 0):
        return 0
    return int(number_str)

def normalize_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        return "unknown"

def normalize_episode(episode: Episode) -> Episode:
    flag_discard = False
    
    if not episode.series_name:
        flag_discard = True
    
    episode.series_name = normalize_series_name(episode.series_name)
    episode.episode_title = normalize_episode_title(episode.episode_title)
    episode.season_number = normalize_numbers(episode.season_number)
    episode.episode_number = normalize_numbers(episode.episode_number)
    episode.air_date = normalize_date(episode.air_date)

    calidad_acumulada = 0
    
    if episode.air_date != "unknown":
        calidad_acumulada += 100
    
    if episode.episode_title != "untitled episode":
        calidad_acumulada += 10
        
    if episode.episode_number > 0:
        calidad_acumulada += 1

    episode.quality = calidad_acumulada

    if episode.episode_number == 0 and episode.episode_title == "untitled episode" and episode.air_date == "unknown":
        flag_discard = True

    return episode, flag_discard


def add_episode_in_order(v, nuevo_episodio):
    izq = 0
    der = len(v) - 1
    encontrado = False
    
    # Definimos el criterio de orden (Triple clave)
    # 1. Nombre -> 2. Temporada -> 3. Episodio
    criterio_nuevo = (nuevo_episodio.series_name, 
                      nuevo_episodio.season_number, 
                      nuevo_episodio.episode_number)

    while izq <= der:
        c = (izq + der) // 2
        criterio_actual = (v[c].series_name, 
                           v[c].season_number, 
                           v[c].episode_number)

        if criterio_actual == criterio_nuevo:
            encontrado = True
            # Lógica de Calidad: Reemplaza solo si el nuevo es estrictamente SUPERIOR
            # Al usar ">", si son iguales en calidad, se queda el original (el primero que apareció)
            if nuevo_episodio.quality > v[c].quality:
                v[c] = nuevo_episodio
            break
        
        if criterio_nuevo < criterio_actual:
            der = c - 1
        else:
            izq = c + 1

    if not encontrado:
        v.insert(izq, nuevo_episodio)
    
    return encontrado

def read_episodes_from_csv(file_path: str, path_file_output: str) -> list[Episode]:
    vector_final = []
    
    if not os.path.exists(file_path):
        return vector_final

    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)
        
        for row in reader:
            episode = parse_episode(",".join(row))
            episode, flag_discard = normalize_episode(episode)
            if not flag_discard:
                add_episode_in_order(vector_final, episode)
                
        export_episodes_to_csv(vector_final, path_file_output)      

def export_episodes_to_csv(episodes: list[Episode], output_path: str):
    with open(output_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Series Name", "Season Number", "Episode Number", "Episode Title", "Air Date"])
        for episode in episodes:
            writer.writerow([episode.series_name, episode.season_number, episode.episode_number, episode.episode_title, episode.air_date])


def main():
    path_file = r"C:\Users\augus\OneDrive\Escritorio\proofpoint\proofpoint-intern-challenge-2026\input\input_episodes.csv"
    path_file_output = r"C:\Users\augus\OneDrive\Escritorio\proofpoint\proofpoint-intern-challenge-2026\output\output_episodes.csv"
    read_episodes_from_csv(path_file, path_file_output)
    
if __name__ == "__main__":
    main()