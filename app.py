# app.py

import streamlit as st
import pandas as pd
from crossref import obtener_metadatos
from embeddings import obtener_keywords, clean_jats
from utils import normalizar_entrada

st.set_page_config(page_title="🔍 Analizador Semántico", layout="wide")

st.title("🔍 Analizador Semántico de DOIs y Handles")
st.markdown(
    "Introduce una lista de **DOIs o Handles** (uno por línea) o súbelos mediante un archivo para analizar títulos, resúmenes y extraer palabras clave relevantes (vocabulario en inglés)."
)

# Idioma decorativo (opcional)
st.selectbox("🌍 Idioma del vocabulario (solo inglés disponible)", ["en"], index=0, disabled=True)

# Entrada manual
with st.expander("✏️ Introducción manual"):
    input_str = st.text_area(
        "Introduce DOIs o Handles (uno por línea):",
        placeholder="10.1234/abcd123\n2445/221185\nhttps://hdl.handle.net/2445/221185"
    )
    doi_manual = normalizar_entrada(input_str.splitlines()) if input_str else []

# Subida de archivo
with st.expander("📂 Subir archivo (.txt o .csv)"):
    archivo = st.file_uploader("Selecciona archivo", type=["txt", "csv"])
    doi_archivo = []

    if archivo:
        if archivo.name.endswith(".txt"):
            content = archivo.read().decode("utf-8")
            doi_archivo = normalizar_entrada(content.splitlines())
        elif archivo.name.endswith(".csv"):
            df = pd.read_csv(archivo)
            posibles_columnas = [col for col in df.columns if "doi" in col.lower() or "handle" in col.lower()]
            if posibles_columnas:
                valores = df[posibles_columnas[0]].dropna().astype(str).tolist()
                doi_archivo = normalizar_entrada(valores)
            else:
                st.warning("⚠️ No se encontró una columna con DOIs o Handles en el CSV.")

# Combinar lista sin duplicados
dois = list(dict.fromkeys(doi_manual + doi_archivo))

if st.button("🚀 Analizar"):
    if not dois:
        st.warning("⚠️ Por favor, introduce al menos un DOI o Handle válido.")
    else:
        for doi in dois:
            st.markdown("---")
            enlace = f"https://doi.org/{doi}" if doi.startswith("10.") else f"https://hdl.handle.net/{doi}"
            st.subheader(f"🔎 Identificador: [{doi}]({enlace})")

            datos = obtener_metadatos(doi)
            if not datos:
                st.error("❌ No se pudieron obtener metadatos.")
                continue

            titulo, resumen = datos
            st.markdown(f"**📘 Título:** {titulo}")
            if resumen:
                st.markdown(f"**📝 Resumen:** {clean_jats(resumen)}", unsafe_allow_html=True)
            else:
                st.info("ℹ️ No se encontró resumen.")

            texto = f"{titulo} {resumen}".strip()
            try:
                resultados = obtener_keywords(texto)
                st.markdown("### 🏷️ Palabras clave relevantes:")
                for r in resultados:
                    st.markdown(f"- [{r['término']}]({r['link']}) — `score: {r['score']:.4f}`")
            except Exception as e:
                st.error(f"❌ Error durante el análisis de embeddings: {e}")
