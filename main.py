# main.py

import re
from crossref import obtener_metadatos
from embeddings import obtener_keywords, clean_jats
from utils import normalizar_entrada

print("🌍 Analizador semántico en inglés (vocabulario único)")
print("\nIntroduce DOIs o Handles (uno por línea). Deja vacío y pulsa Enter para continuar:")

entradas = []
while True:
    entrada = input("> ").strip()
    if not entrada:
        break
    entradas.append(entrada)

dois = normalizar_entrada(entradas)

if not dois:
    print("⚠️ No se proporcionaron identificadores.")
    exit(0)

for doi in dois:
    print(f"\n🔍 Identificador: {doi}")
    datos = obtener_metadatos(doi)

    if not datos:
        print("❌ No se pudieron obtener metadatos.")
        continue

    titulo, resumen = datos
    texto = f"{titulo} {resumen}".strip()

    print(f"📘 Título: {titulo}")
    if resumen:
        print(f"📝 Resumen: {clean_jats(resumen)}")

    try:
        resultados = obtener_keywords(texto)
        print("🏷️ Palabras clave relevantes:")
        for r in resultados:
            print(f" - {r['término']} → {r['link']} (score: {r['score']:.4f})")
    except Exception as e:
        print(f"❌ Error al generar palabras clave: {e}")
