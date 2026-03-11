import re
from collections import Counter

def analizar_frecuencia(ruta_archivo):
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            contenido = archivo.read().lower()

            palabras = re.findall(r"[a-záéíóúüñ]+", contenido)

            conteo = Counter(palabras)

            top_10 = conteo.most_common(10)

            print(f"--- Análisis de: {ruta_archivo} ---")
            print(f"{'Palabra':<15} | {'Frecuencia':<10}")
            print("-" * 30)

            for palabra, frecuencia in top_10:
                print(f"{palabra:<15} | {frecuencia:<10}")

    except FileNotFoundError:
        print("Error: El archivo no fue encontrado.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")

if __name__ == "__main__":
    ruta = input("Ingrese la ruta del archivo de texto a analizar: ")
    analizar_frecuencia(ruta)