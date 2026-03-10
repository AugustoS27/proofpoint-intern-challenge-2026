# Analizador de Frecuencia de Palabras

Programa que lee un archivo de texto y muestra las 10 palabras más frecuentes, ignorando mayúsculas, puntuación y caracteres especiales.

---

## Requisitos

- Python 3.10 o superior
- Sin dependencias externas

---

## Cómo ejecutarlo

```bash
python word_frequency_analyzer.py
```

El programa pedirá la ruta al archivo de texto:

```
Ingrese la ruta del archivo de texto a analizar: mi_texto.txt
```

---

## Ejemplo

Dado un archivo `ejemplo.txt`:

```
El éxito es la suma de pequeños esfuerzos, repetidos día tras día
```

Salida:

```
Palabra         | Frecuencia
------------------------------
día             | 2
el              | 1
éxito           | 1
es              | 1
la              | 1
suma            | 1
de              | 1
pequeños        | 1
esfuerzos       | 1
repetidos       | 1
```

---

## Decisiones de implementación

Las palabras se extraen con la regex `[a-záéíóúüñ]+`, que:

- Convierte todo el texto a minúsculas antes de procesar
- Extrae solo secuencias de letras, descartando puntuación, números y cualquier carácter especial (`—`, `…`, `¡`, etc.)
- Soporta caracteres del español de forma nativa

Este enfoque es más robusto que eliminar caracteres de `string.punctuation`, ya que ese set no cubre símbolos tipográficos ni puntuación no ASCII.
