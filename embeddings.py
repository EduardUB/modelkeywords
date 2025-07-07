# embeddings.py

import os
import torch
import pandas as pd
from sentence_transformers import SentenceTransformer, util

CACHE_DIR = "cache_embeddings"
VOCAB_PATH = "vocabulario.xlsx"

os.makedirs(CACHE_DIR, exist_ok=True)

# 🔹 Modelos únicos para todos los idiomas
MODELO_RAPIDO = SentenceTransformer("BAAI/bge-small-en-v1.5")
RERANKER = SentenceTransformer("thenlper/gte-base")

def cargar_vocabulario():
    df = pd.read_excel(VOCAB_PATH).dropna(subset=["término", "link"])
    terminos = df["término"].tolist()
    links = df["link"].tolist()
    return terminos, links

def get_embeddings():
    terminos, _ = cargar_vocabulario()
    terminos_passage = [f"passage: {t}" for t in terminos]

    # Cache embeddings rápido
    cache_rapido = os.path.join(CACHE_DIR, "emb_vocab_rapido.pt")
    emb_vocab_rapido = torch.load(cache_rapido) if os.path.exists(cache_rapido) else None

    if emb_vocab_rapido is None:
        emb_vocab_rapido = MODELO_RAPIDO.encode(terminos, convert_to_tensor=True)
        torch.save(emb_vocab_rapido, cache_rapido)

    # Cache embeddings reranker
    cache_preciso = os.path.join(CACHE_DIR, "emb_vocab_preciso.pt")
    emb_vocab_preciso = torch.load(cache_preciso) if os.path.exists(cache_preciso) else None

    if emb_vocab_preciso is None:
        emb_vocab_preciso = RERANKER.encode(terminos_passage, convert_to_tensor=True)
        torch.save(emb_vocab_preciso, cache_preciso)

    return terminos, emb_vocab_rapido, emb_vocab_preciso

def obtener_keywords(texto, top_n=10, candidatos_iniciales=50):
    terminos, emb_vocab_rapido, emb_vocab_preciso = get_embeddings()
    _, links = cargar_vocabulario()

    emb_texto_rapido = MODELO_RAPIDO.encode(texto, convert_to_tensor=True)
    similitudes_rapidas = util.cos_sim(emb_texto_rapido, emb_vocab_rapido)[0]
    top_indices = similitudes_rapidas.topk(candidatos_iniciales).indices.tolist()

    texto_query = f"query: {texto}"
    emb_texto_preciso = RERANKER.encode(texto_query, convert_to_tensor=True)
    emb_candidatos = emb_vocab_preciso[top_indices]
    similitudes_precisas = util.cos_sim(emb_texto_preciso, emb_candidatos)[0]

    reordenados = similitudes_precisas.topk(top_n)
    final_indices = [top_indices[i] for i in reordenados.indices.tolist()]
    scores = reordenados.values.tolist()

    resultados = []
    for idx, score in zip(final_indices, scores):
        resultados.append({
            "término": terminos[idx],
            "link": links[idx],
            "score": score
        })

    return resultados

def clean_jats(texto):
    import re
    return re.sub(r"<[^>]+>", "", texto)
