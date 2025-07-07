import requests
import xml.etree.ElementTree as ET
from lxml import etree

def obtener_metadatos(identificador):
    limpio = identificador.strip().replace("https://doi.org/", "").replace("http://doi.org/", "")

    # --- 🌐 INTENTA CON CROSSREF ---
    url_crossref = f"https://api.crossref.org/works/{limpio}"
    try:
        resp = requests.get(url_crossref, timeout=10)
        if resp.status_code == 200 and 'application/json' in resp.headers.get('Content-Type', ''):
            data = resp.json().get("message", {})
            titulo = data.get("title", [""])[0]
            resumen = data.get("abstract", "") or ""
            return titulo, resumen
    except Exception as e:
        print(f"⚠️ Error al consultar Crossref para {identificador}: {e}")

    # --- 📊 INTENTA CON DATACITE ---
    url_datacite = f"https://api.datacite.org/dois/{limpio}"
    try:
        resp = requests.get(url_datacite, timeout=10)
        if resp.status_code == 200 and 'application/json' in resp.headers.get('Content-Type', ''):
            data = resp.json().get("data", {}).get("attributes", {})
            titulo = data.get("titles", [{}])[0].get("title", "")
            resumen = data.get("descriptions", [{}])[0].get("description", "") if data.get("descriptions") else ""
            return titulo, resumen
    except Exception as e:
        print(f"⚠️ Error al consultar DataCite para {identificador}: {e}")

    # --- 🗂️ SI PARECE UN HANDLE, PRUEBA OAI ---
    if "/" in limpio:
        handle = limpio
        return obtener_desde_oai(handle)

    # ❌ Todo falló
    print(f"❌ No se pudo obtener metadatos para: {identificador}")
    return None



def obtener_desde_oai(handle):
    url = "https://diposit.ub.edu/dspace-oai/request"
    params = {
        "verb": "GetRecord",
        "identifier": f"oai:diposit.ub.edu:{handle}",
        "metadataPrefix": "qdc"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        tree = etree.fromstring(response.content)

        ns = {
            "oai": "http://www.openarchives.org/OAI/2.0/",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/"
        }

        metadata = tree.xpath("//oai:metadata", namespaces=ns)
        if not metadata:
            print(f"⚠️ No se encontró la sección <metadata> en el OAI de {handle}")
            return "", ""

        metadata_element = metadata[0]

        titles = metadata_element.xpath(".//dc:title", namespaces=ns)
        desc_dc = metadata_element.xpath(".//dc:description", namespaces=ns)
        desc_dcterms = metadata_element.xpath(".//dcterms:abstract", namespaces=ns)

        titulo = titles[0].text.strip() if titles and titles[0].text else ""
        
        # Combina ambas fuentes de resumen
        resumen_parts = []
        if desc_dc:
            resumen_parts += [d.text.strip() for d in desc_dc if d.text]
        if desc_dcterms:
            resumen_parts += [d.text.strip() for d in desc_dcterms if d.text]
        
        resumen = " ".join(resumen_parts)

        if not titulo and not resumen:
            print(f"⚠️ No se encontraron título ni resumen en el OAI de {handle}")
        else:
            print(f"✅ Título extraído: {titulo[:80]}...")
            print(f"✅ Resumen extraído: {resumen[:100]}...")

        return titulo, resumen

    except Exception as e:
        print(f"❌ Error al procesar OAI para {handle}: {e}")
        return "", ""


