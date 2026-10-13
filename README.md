# Unir PDFs por Acta

Script en Python que une la **primera página** de cientos de PDFs en un solo archivo, respetando exactamente el orden en que aparecen las cédulas en un Acta (PDF). Así se imprime todo de una sola vez y en el orden correcto.

## Problema que resuelve

Imprimir manualmente cientos de documentos nombrados por cédula, uno por uno y en el orden del Acta, es lento y propenso a errores. Este script automatiza el proceso completo.

## Qué hace

1. Lee el Acta en PDF y extrae las cédulas en el orden en que aparecen.
2. Busca el PDF de cada cédula en la carpeta de documentos principales.
3. Opcionalmente, agrega justo después la primera página del documento complementario de la misma cédula.
4. Genera `resultado_final.pdf` listo para imprimir.
5. Genera un **índice de páginas** (`indice_paginas.txt`) para ubicar cualquier cédula sin hojear el PDF.
6. Genera un **reporte de pendientes** (`reporte_hc_pendientes.txt`) con las cédulas que requieren documento complementario y aún no lo tienen.
7. Avisa qué cédulas no tienen PDF y qué PDFs sobran (no aparecen en el Acta).

## Tecnologías

- Python 3
- [pypdf](https://pypi.org/project/pypdf/): unión de páginas
- [pdfplumber](https://pypi.org/project/pdfplumber/): extracción de texto del Acta
- Expresiones regulares para detectar las cédulas

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python unir_por_acta.py
```

El script pregunta, en orden:

| Pregunta | Ejemplo |
|---|---|
| Ruta del Acta (PDF o carpeta que lo contiene) | `C:\acta\acta.pdf` |
| Carpeta con los PDFs principales | `C:\pdfs\principales` |
| Carpeta con PDFs complementarios (opcional) | `C:\pdfs\complementarios` |
| Archivo `.txt` con las cédulas que requieren documento complementario (opcional) | `C:\pdfs\requieren.txt` |

Los archivos deben estar nombrados por cédula: `1000001.pdf` o `1000001_extra.pdf`.

## Salidas

Se crean en la carpeta de PDFs principales:

- `resultado_final.pdf`: todas las primeras páginas en el orden del Acta.
- `indice_paginas.txt`: cédula → página dentro de `resultado_final.pdf`.
- `reporte_hc_pendientes.txt`: cédulas con documento complementario pendiente (solo si diste el `.txt`).

## Privacidad

Este repositorio **no incluye documentos reales**. Los PDFs de entrada contienen datos personales y no deben subirse a GitHub.

## Autor

Camilo — Ingeniero de Sistemas (UNAD)
