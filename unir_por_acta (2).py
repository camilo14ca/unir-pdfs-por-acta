"""
unir_por_acta.py
--------------------------------
Une la primera página de cada PDF en UN SOLO archivo, respetando
EXACTAMENTE el orden en que aparecen las cédulas en un "Acta" (PDF).

Organización de carpetas esperada:
    - Una carpeta (o el archivo directo) con el Acta en PDF.
    - Una carpeta con los PDFs principales, nombrados por cédula
      (ej: 1000001.pdf).
    - Opcionalmente, OTRA carpeta con documentos complementarios,
      también nombrados por cédula (ej: 1000001.pdf o 1000001_extra.pdf).

Si das la carpeta de documentos complementarios, por cada cédula el
resultado incluye:
  1) la primera página del PDF principal (si existe)
  2) justo después, la primera página del PDF complementario de esa
     misma cédula (si existe)

USO:
    1. Instala las dependencias (una sola vez):
         pip install -r requirements.txt

    2. Ejecuta:
         python unir_por_acta.py

    3. El script pregunta:
       a) Ruta del Acta (PDF exacto o carpeta que lo contiene).
       b) Ruta de la carpeta con los PDFs principales.
       c) Ruta de la carpeta con los PDFs complementarios (opcional).
       d) Archivo .txt con las cédulas que requieren documento
          complementario, una por línea (opcional).

    4. Se crea "resultado_final.pdf" dentro de la carpeta de PDFs
       principales. Ese es el único archivo que se imprime.

    5. También se generan dos archivos de texto:
       - indice_paginas.txt: cada cédula con la página exacta donde
         quedó en resultado_final.pdf.
       - reporte_hc_pendientes.txt: cédulas que requieren documento
         complementario y aún no lo tienen, con la página donde va su
         hoja principal.
"""

import os
import re
import sys

try:
    import pdfplumber
except ImportError:
    print("\n[ERROR] Falta instalar pdfplumber. Ejecuta:")
    print("        pip install pdfplumber")
    sys.exit(1)

from pypdf import PdfReader, PdfWriter


def resolver_pdf(ruta):
    """Si 'ruta' es un PDF, la devuelve tal cual. Si es una carpeta,
    busca el primer .pdf que encuentre dentro."""
    if os.path.isfile(ruta) and ruta.lower().endswith(".pdf"):
        return ruta
    if os.path.isdir(ruta):
        for nombre in os.listdir(ruta):
            if nombre.lower().endswith(".pdf"):
                return os.path.join(ruta, nombre)
    return None


def extraer_orden_del_acta(ruta_acta):
    """Lee el Acta en PDF y devuelve la lista de cédulas (como texto),
    en el mismo orden en que aparecen en el documento."""
    cedulas = []
    with pdfplumber.open(ruta_acta) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text() or ""
            # <numero de fila> <numero de cedula> + una letra mayúscula
            # (cubre tipos de documento como "CC", "PPT", "TI", "CE",
            # el tipo en blanco seguido del nombre, o texto de
            # encabezado/pie de página mezclado).
            filas = re.findall(r'\b\d+\s+(\d{4,12})\s*[A-ZÁÉÍÓÚÑ]', texto)
            cedulas.extend(filas)
    return cedulas


def encontrar_archivo(cedula, archivos_disponibles):
    """Busca el PDF cuyo nombre empieza exactamente con esa cédula
    (evita que 123 le gane a 1234)."""
    for nombre in archivos_disponibles:
        base = nombre[:-4] if nombre.lower().endswith(".pdf") else nombre
        if base == cedula or base.startswith(cedula + "_"):
            return nombre
    return None


def pedir_ruta(mensaje, opcional=False):
    ruta = input(mensaje).strip().strip('"')
    if opcional and ruta == "":
        return None
    return ruta


def main():
    print("=" * 60)
    print(" UNIR PRIMERA PÁGINA SEGÚN EL ORDEN DEL ACTA")
    print("=" * 60)

    ruta_acta_input = pedir_ruta("\nRuta del Acta (archivo PDF o carpeta que lo contiene): ")
    ruta_acta = resolver_pdf(ruta_acta_input)
    if not ruta_acta:
        print(f"\n[ERROR] No se encontró un PDF en: {ruta_acta_input}")
        sys.exit(1)
    print(f"  -> Usando Acta: {ruta_acta}")

    carpeta_normal = pedir_ruta("Ruta de la carpeta con los PDFs principales (por cédula): ")
    if not os.path.isdir(carpeta_normal):
        print(f"\n[ERROR] La carpeta no existe: {carpeta_normal}")
        sys.exit(1)

    carpeta_hc = pedir_ruta(
        "Ruta de la carpeta con los PDFs complementarios (deja vacío si no aplica): ",
        opcional=True,
    )
    if carpeta_hc and not os.path.isdir(carpeta_hc):
        print(f"\n[ERROR] La carpeta complementaria no existe: {carpeta_hc}")
        sys.exit(1)

    archivo_requieren_hc = pedir_ruta(
        "Archivo .txt con las cédulas que SÍ requieren documento complementario "
        "(una por línea; deja vacío si no aplica): ",
        opcional=True,
    )
    cedulas_requieren_hc = set()
    if archivo_requieren_hc:
        if not os.path.isfile(archivo_requieren_hc):
            print(f"\n[ERROR] No se encontró el archivo: {archivo_requieren_hc}")
            sys.exit(1)
        with open(archivo_requieren_hc, "r", encoding="utf-8") as f:
            for linea in f:
                c = linea.strip()
                if c:
                    cedulas_requieren_hc.add(c)
        print(f"  -> {len(cedulas_requieren_hc)} cédulas marcadas como que requieren documento complementario.")

    print("\nLeyendo el Acta...")
    orden_cedulas = extraer_orden_del_acta(ruta_acta)
    print(f"Se encontraron {len(orden_cedulas)} cédulas en el Acta, en orden.")

    if not orden_cedulas:
        print("\n[ERROR] No se pudo leer ninguna cédula del Acta. Revisa el archivo.")
        sys.exit(1)

    archivos_normales = [f for f in os.listdir(carpeta_normal) if f.lower().endswith(".pdf")]
    archivos_hc = []
    if carpeta_hc:
        archivos_hc = [f for f in os.listdir(carpeta_hc) if f.lower().endswith(".pdf")]

    writer = PdfWriter()
    no_encontrados = []
    usados_normales = set()
    usados_hc = set()
    cedulas_con_hc = set()
    pagina_de_cedula = {}  # cédula -> número de página (1-indexado) de su hoja principal
    total_paginas = 0

    for i, cedula in enumerate(orden_cedulas, start=1):
        nombre_normal = encontrar_archivo(cedula, archivos_normales)
        nombre_hc = encontrar_archivo(cedula, archivos_hc) if carpeta_hc else None

        if nombre_normal is None and nombre_hc is None:
            no_encontrados.append(cedula)
            print(f"  [{i}/{len(orden_cedulas)}] SIN PDF -> cédula {cedula}")
            continue

        if nombre_normal:
            try:
                reader = PdfReader(os.path.join(carpeta_normal, nombre_normal))
                writer.add_page(reader.pages[0])
                usados_normales.add(nombre_normal)
                total_paginas += 1
                pagina_de_cedula[cedula] = total_paginas
                print(f"  [{i}/{len(orden_cedulas)}] OK -> {nombre_normal} (página {total_paginas})")
            except Exception as e:
                print(f"  [{i}/{len(orden_cedulas)}] FALLÓ -> {nombre_normal}: {e}")

        if nombre_hc:
            try:
                reader_hc = PdfReader(os.path.join(carpeta_hc, nombre_hc))
                writer.add_page(reader_hc.pages[0])
                usados_hc.add(nombre_hc)
                cedulas_con_hc.add(cedula)
                total_paginas += 1
                if cedula not in pagina_de_cedula:
                    pagina_de_cedula[cedula] = total_paginas
                print(f"           + Complementario -> {nombre_hc} (página {total_paginas})")
            except Exception as e:
                print(f"           + Complementario FALLÓ -> {nombre_hc}: {e}")

    salida = os.path.join(carpeta_normal, "resultado_final.pdf")
    with open(salida, "wb") as f:
        writer.write(f)

    # --- Índice de páginas: para buscar cualquier cédula sin hojear el PDF ---
    ruta_indice = os.path.join(carpeta_normal, "indice_paginas.txt")
    with open(ruta_indice, "w", encoding="utf-8") as f:
        f.write("CÉDULA -> PÁGINA en resultado_final.pdf\n")
        f.write("=" * 40 + "\n")
        for cedula in orden_cedulas:
            pagina = pagina_de_cedula.get(cedula, "NO INCLUIDA")
            f.write(f"{cedula} -> {pagina}\n")

    # --- Reporte de pendientes (solo si se dio la lista de quiénes lo requieren) ---
    ruta_reporte_hc = None
    pendientes = []
    if cedulas_requieren_hc:
        pendientes = sorted(cedulas_requieren_hc - cedulas_con_hc)
        ruta_reporte_hc = os.path.join(carpeta_normal, "reporte_hc_pendientes.txt")
        with open(ruta_reporte_hc, "w", encoding="utf-8") as f:
            f.write("CÉDULAS QUE REQUIEREN DOCUMENTO COMPLEMENTARIO Y AÚN NO LO TIENEN\n")
            f.write("=" * 65 + "\n")
            if not pendientes:
                f.write("Ninguna. Todas las cédulas marcadas ya tienen su documento.\n")
            for cedula in pendientes:
                pagina = pagina_de_cedula.get(cedula, "SIN NINGÚN PDF ENCONTRADO")
                f.write(f"Cédula {cedula} -> ir a la página {pagina}\n")

    sobrantes_normales = [f for f in archivos_normales if f not in usados_normales]
    sobrantes_hc = [f for f in archivos_hc if f not in usados_hc]

    print("\n" + "=" * 60)
    print(f"LISTO. Se unieron {total_paginas} páginas en el orden del Acta.")
    print(f"Archivo generado: {salida}")

    if no_encontrados:
        print(f"\nCédulas del Acta SIN NINGÚN PDF ({len(no_encontrados)}):")
        for c in no_encontrados:
            print(f"  - {c}")

    if sobrantes_normales:
        print(f"\nPDFs principales que NO aparecen en el Acta ({len(sobrantes_normales)}):")
        for s in sobrantes_normales:
            print(f"  - {s}")

    if sobrantes_hc:
        print(f"\nPDFs complementarios que NO aparecen en el Acta ({len(sobrantes_hc)}):")
        for s in sobrantes_hc:
            print(f"  - {s}")

    print(f"\nÍndice de páginas generado: {ruta_indice}")
    if ruta_reporte_hc:
        print(f"Reporte de pendientes generado: {ruta_reporte_hc}")
        if pendientes:
            print(f"  -> {len(pendientes)} cédulas requieren el documento y todavía no lo tienen.")
        else:
            print("  -> Todas las cédulas marcadas ya tienen su documento.")

    print("=" * 60)
    print("\nAhora solo abre resultado_final.pdf y mándalo a imprimir UNA vez.")


if __name__ == "__main__":
    main()
