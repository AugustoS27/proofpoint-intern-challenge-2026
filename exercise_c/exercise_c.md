# Word Frequency Analyzer

Program that reads a text file and displays the 10 most frequent words, ignoring capital letters, punctuation, and special characters.

---

## Requirements

- Python 3.10 or higher
- No external dependencies

---

## How to run it

```bash
python word_frequency_analyzer.py
```

The program will ask for the path to the text file:

```
Ingrese la ruta del archivo de texto a analizar: mi_texto.txt
```

---

## Example

Given a file `ejemplo.txt`:

```
El éxito es la suma de pequeños esfuerzos, repetidos día tras día
```

output:

```
Word            | Frequency
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

## Implementation decisions

Words are extracted using the regex `[a-záéíóúüñ]+`, which:

- Converts all text to lowercase before processing
- Extracts only sequences of letters, discarding punctuation, numbers, and any special characters (`—`, `…`, `¡`, etc.)
- Supports Spanish characters
