import chromadb

# Conectar ao ChromaDB persistente (mesmo path da ingestão)
client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="novatech_docs")


def buscar(pergunta: str, n_resultados: int = 5) -> list[dict]:
    resultados = collection.query(
        query_texts=[pergunta],
        n_results=n_resultados,
        include=["documents", "metadatas", "distances"],
    )

    documentos = resultados["documents"][0]
    metadados = resultados["metadatas"][0]
    distancias = resultados["distances"][0]

    saida = []
    for texto, meta, distancia in zip(documentos, metadados, distancias):
        saida.append({
            "texto":        texto,
            "fonte":        meta.get("fonte", ""),
            "secao":        meta.get("secao", ""),
            "versao":       meta.get("versao", ""),
            "tipo_fonte":   meta.get("tipo_fonte", ""),
            "similaridade": round(1 - distancia, 4),
        })
    return saida


def exibir_resultados(resultados: list[dict]) -> None:
    for i, item in enumerate(resultados, start=1):
        print(f"--- Resultado {i} ---")
        print(f"Fonte:        {item['fonte']}")
        print(f"Seção:        {item['secao']}")
        print(f"Versão:       {item['versao']}")
        print(f"Tipo:         {item['tipo_fonte']}")
        print(f"Similaridade: {item['similaridade']}")
        print(f"Prévia:       {item['texto'][:200]}")
        print()


if __name__ == "__main__":
    pergunta = "qual o prazo de devolução"
    resultados = buscar(pergunta)
    exibir_resultados(resultados)
