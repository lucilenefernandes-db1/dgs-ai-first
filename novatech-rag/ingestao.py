# Script de ingestão de documentos NovaTech para ChromaDB
# Estratégia de chunking: por seção semântica, 300-600 tokens, overlap 50 tokens

import os
import re
import chromadb
#from sentence_transformers import SentenceTransformer

# --- Configuração do ChromaDB (persistente em ./chroma_db) ---
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="novatech_docs",
    metadata={"hnsw:space": "cosine"},
)

# --- Modelo de embeddings ---
#modelo = SentenceTransformer("all-MiniLM-L6-v2")


# ---------------------------------------------------------------------------
# Funções
# ---------------------------------------------------------------------------

def carregar_documentos(pasta: str) -> list[dict]:
    """Lê todos os arquivos .md da pasta.

    Retorna lista de dicts com:
        nome_arquivo (str): nome do arquivo .md
        conteudo     (str): conteúdo completo do arquivo
    """
    documentos = []
    for nome_arquivo in sorted(os.listdir(pasta)):
        if nome_arquivo.endswith(".md"):
            caminho = os.path.join(pasta, nome_arquivo)
            with open(caminho, "r", encoding="utf-8") as f:
                conteudo = f.read()
            documentos.append({"nome_arquivo": nome_arquivo, "conteudo": conteudo})
    return documentos


def _estimar_tokens(texto: str) -> int:
    """Aproximação simples: 1 token ≈ 4 caracteres."""
    return max(1, len(texto) // 4)


def _subdividir_com_overlap(
    palavras: list[str],
    max_tokens: int = 600,
    overlap_tokens: int = 50,
) -> list[str]:
    """Divide uma lista de palavras em sub-chunks com overlap.

    Usa a heurística 1 palavra ≈ 1,25 tokens para converter limites
    de tokens em limites de palavras.
    """
    max_palavras = max(1, int(max_tokens / 1.25))
    overlap_palavras = max(0, int(overlap_tokens / 1.25))

    resultado: list[str] = []
    inicio = 0
    while inicio < len(palavras):
        fim = min(inicio + max_palavras, len(palavras))
        resultado.append(" ".join(palavras[inicio:fim]))
        if fim >= len(palavras):
            break
        inicio = fim - overlap_palavras
    return resultado


def dividir_em_chunks(conteudo: str, nome_arquivo: str) -> list[dict]:
    """Divide o texto em chunks por seção semântica.

    Regras:
    - Detecta ## e ### como quebras de seção.
    - Seções que caibam em ≤ 600 tokens viram um único chunk.
    - Seções maiores são subdivididas com overlap de 50 tokens.

    Retorna lista de dicts com:
        texto  (str): conteúdo do chunk (com contexto de overlap quando aplicável)
        fonte  (str): nome do arquivo de origem
        secao  (str): título da seção
        indice (int): índice sequencial do chunk no documento
    """
    # Quebra o documento nas marcações ## e ###, preservando o cabeçalho
    partes = re.split(r"(?=^#{2,3} )", conteudo, flags=re.MULTILINE)

    chunks: list[dict] = []
    indice = 0

    for parte in partes:
        parte = parte.strip()
        if not parte:
            continue

        # Identifica o título da seção a partir da primeira linha
        primeira_linha = parte.split("\n", 1)[0].strip()
        if re.match(r"^#{2,3} ", primeira_linha):
            secao = re.sub(r"^#+\s*", "", primeira_linha).strip()
        else:
            secao = "Introdução"

        if _estimar_tokens(parte) <= 600:
            chunks.append(
                {"texto": parte, "fonte": nome_arquivo, "secao": secao, "indice": indice}
            )
            indice += 1
        else:
            # Seção grande: subdivide com overlap de 50 tokens
            for sub in _subdividir_com_overlap(parte.split(), max_tokens=600, overlap_tokens=50):
                chunks.append(
                    {"texto": sub, "fonte": nome_arquivo, "secao": secao, "indice": indice}
                )
                indice += 1

    # Enriquecimento semântico: adiciona prefixo em chunks que contêm exceções
    PALAVRAS_EXCECAO = [
        "não são elegíveis",
        "não é elegível",
        "exceto",
        "exceção",
        "não se aplica",
        "salvo",
        "vedado",
        "proibido",
    ]

    for chunk in chunks:
        texto_lower = chunk["texto"].lower()
        if any(palavra in texto_lower for palavra in PALAVRAS_EXCECAO):
            chunk["texto"] = (
                "[ATENÇÃO — Este trecho define restrições ou categorias "
                "NÃO elegíveis para o processo padrão]\n\n"
                + chunk["texto"]
            )

    return chunks

# Mapeamento de versão e tipo por arquivo
METADADOS_ARQUIVO = {
    "PROC-042-frete-especial-v1.md":          {"versao": "v1", "data_emissao": "2023-03-03", "tipo_fonte": "normativo"},
    "PROC-042-v2-frete-especial-revisado.md": {"versao": "v2", "data_emissao": "2023-11-10", "tipo_fonte": "normativo"},
    "POL-001-politica-devolucao.md":          {"versao": "v1", "data_emissao": "2024-01-15", "tipo_fonte": "normativo"},
    "SLA-2024-tabela-sla-clientes.md":        {"versao": "v1", "data_emissao": "2024-01-02", "tipo_fonte": "normativo"},
    "FAQ-atendimento.md":                     {"versao": "v1", "data_emissao": "2024-01-01", "tipo_fonte": "informal"},
}

def gerar_e_indexar(chunks: list[dict]) -> None:
    if not chunks:
        return

    textos = [c["texto"] for c in chunks]
    ids = [f"{c['fonte']}__idx{c['indice']}" for c in chunks]
    metadados = []
    for c in chunks:
        extra = METADADOS_ARQUIVO.get(
            c["fonte"],
            {"versao": "desconhecida", "data_emissao": "", "tipo_fonte": "normativo"}
        )
        metadados.append({
            "fonte":        c["fonte"],
            "secao":        c["secao"],
            "indice":       c["indice"],
            "versao":       extra["versao"],
            "data_emissao": extra["data_emissao"],
            "tipo_fonte":   extra["tipo_fonte"],
        })

    # O ChromaDB gera os embeddings automaticamente com o modelo embutido
    collection.upsert(
        ids=ids,
        documents=textos,
        metadatas=metadados,
    )


# ---------------------------------------------------------------------------
# Execução principal
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pasta = "./docs"
    documentos = carregar_documentos(pasta)

    total_geral = 0
    for doc in documentos:
        chunks = dividir_em_chunks(doc["conteudo"], doc["nome_arquivo"])
        gerar_e_indexar(chunks)
        print(f"  {doc['nome_arquivo']}: {len(chunks)} chunks indexados")
        total_geral += len(chunks)

    print(f"\nTotal geral: {total_geral} chunks indexados")
