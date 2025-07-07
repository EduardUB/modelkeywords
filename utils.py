# utils.py
import re

def normalizar_entrada(lineas):
    dois_limpios = []
    for e in lineas:
        e = e.strip()

        if "hdl.handle.net/" in e:
            match = re.search(r'handle\.net/([^ \n\r\t]+)', e)
            if match:
                dois_limpios.append(match.group(1))
                continue

        if "doi.org/" in e:
            match = re.search(r'doi\.org/([^ \n\r\t]+)', e)
            if match:
                dois_limpios.append(match.group(1))
                continue

        if e.lower().startswith("doi:"):
            dois_limpios.append(e[4:].strip())
            continue

        dois_limpios.append(e)
    return dois_limpios
