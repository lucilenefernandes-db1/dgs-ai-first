# tasks.md — Query Endpoint

> **Gerado a partir de:** `specs/query-endpoint/plan.md`
> **Módulo:** `src/functions/query/` + `src/services/`
> **Dependências externas:** Azure AI Search index populado; `prompts/system-prompt.md` finalizado

---

## Legenda

| Campo | Formato |
|---|---|
| ID | TASK-QE-NNN |
| Estimativa | P = < 2h · M = 2–4h · G = > 4h |
| Dependências | IDs de tasks que devem estar concluídas antes |

---

## TASK-QE-001 — Definir tipos TypeScript do domínio do query endpoint

**Descrição:**
Criar o arquivo de tipos compartilhados que será importado por todos os módulos do query endpoint. Inclui as interfaces de request, response, chunk recuperado e metadado de documento.

**Critérios de aceite:**
- `QueryRequest` possui campo obrigatório `question: string` e campo opcional `conversationHistory: ConversationTurn[]` (máx. 3 turnos, conforme ADR-0002).
- `QueryResponse` possui campos obrigatórios `answer: string`, `sourceDocuments: SourceDocument[]` e `lowConfidence: boolean`.
- `SourceDocument` possui campos `documentId: string`, `section: string` e `version: string` (para rastreabilidade de documentos contraditórios, ADR-0003).
- `RetrievedChunk` possui campos `content: string`, `score: number`, `metadata: SourceDocument`.
- O arquivo compila sem erros com `tsc --strict` e não possui imports externos (apenas tipos primitivos e tipos do próprio arquivo).

**Dependências:** nenhuma

**Estimativa:** P

**Arquivo a criar:** `src/shared/types.ts`

---

## TASK-QE-002 — Implementar validador Zod de input/output

**Descrição:**
Criar o módulo de validação que usa Zod para validar o body da requisição HTTP de entrada e o objeto de resposta antes de serializar. Deve rejeitar qualquer campo fora do schema e normalizar o campo `question`.

**Critérios de aceite:**
- `validateQueryRequest({ question: '' })` retorna erro de validação com mensagem `"question must not be empty"`.
- `validateQueryRequest({})` retorna erro de validação com mensagem `"question is required"`.
- `validateQueryRequest({ question: 'x'.repeat(2001) })` retorna erro de validação indicando comprimento máximo excedido (limite: 2000 caracteres).
- `validateQueryRequest({ question: '  qual o SLA Gold?  ' })` retorna `question` com whitespace removido nas bordas.
- `validateQueryResponse` rejeita objetos sem `sourceDocuments` com erro de validação (campo obrigatório).
- O módulo exporta os schemas Zod e os tipos inferidos; não exporta funções que façam I/O.

**Dependências:** TASK-QE-001

**Estimativa:** P

**Arquivo a criar:** `src/functions/query/validator.ts`

---

## TASK-QE-003 — Implementar handler HTTP da Azure Function

**Descrição:**
Criar o HTTP trigger da Azure Function que recebe `POST /api/query`, executa a validação de input via TASK-QE-002, orquestra os serviços (ainda como stubs/mocks) e retorna a resposta serializada. Toda a lógica de negócio permanece em serviços separados — o handler apenas coordena.

**Critérios de aceite:**
- `POST /api/query` com body `{}` retorna HTTP 400 com body `{ "error": "question is required" }`.
- `POST /api/query` com `Content-Type` ausente ou incorreto retorna HTTP 415.
- `POST /api/query` com body válido e serviços mockados retorna HTTP 200 com corpo que satisfaz o schema `QueryResponse`.
- `GET /api/query` retorna HTTP 405 (method not allowed).
- O handler registra cada requisição via `pino` com campos `requestId`, `questionLength` e `durationMs`; nunca usa `console.log`.
- O handler não contém lógica de embedding, busca ou chamada ao LLM — delega 100% para os serviços.

**Dependências:** TASK-QE-001, TASK-QE-002

**Estimativa:** M

**Arquivos a criar/editar:**
- `src/functions/query/handler.ts`
- `src/shared/logger.ts`

---

## TASK-QE-004 — Implementar cliente de embedding (Azure OpenAI)

**Descrição:**
Criar o serviço que converte um texto de pergunta em um vetor de embedding chamando a API de embeddings do Azure OpenAI. Deve implementar retry com exponential backoff para erros transitórios (429, 503).

**Critérios de aceite:**
- `generateEmbedding('qual o prazo de devolução?')` retorna um `number[]` com comprimento `> 0`.
- Quando a API retorna HTTP 429, o cliente aguarda e tenta novamente até 3 vezes antes de lançar `EmbeddingError`.
- Quando a API retorna HTTP 500 na 1ª e 2ª tentativas e HTTP 200 na 3ª, a função retorna o embedding com sucesso (retry funciona).
- O intervalo entre tentativas segue exponential backoff: 1s, 2s, 4s (±jitter); não é intervalo fixo.
- Nenhuma chamada real à API é feita nas execuções de teste — o módulo aceita injeção de um `httpClient` mockável.
- Erros não transitórios (400, 401) lançam `EmbeddingError` imediatamente, sem retry.

**Dependências:** TASK-QE-001

**Estimativa:** M

**Arquivo a criar:** `src/services/embedding.ts`

---

## TASK-QE-005 — Implementar cliente de busca (Azure AI Search)

**Descrição:**
Criar o serviço que recebe um vetor de embedding e retorna os top-5 chunks mais relevantes do índice Azure AI Search, incluindo seus metadados de vigência. Deve respeitar o filtro de `documentVersion` para priorizar versões mais recentes (ADR-0003).

**Critérios de aceite:**
- `searchChunks(embeddingVector)` retorna exatamente 5 `RetrievedChunk[]` quando o índice contém ≥ 5 documentos.
- `searchChunks(embeddingVector)` retorna `n` resultados (< 5) sem erro quando o índice contém `n < 5` documentos.
- Quando existem chunks de PROC-042-v1 e PROC-042-v2 com scores similares, o chunk com `metadata.version` mais recente aparece antes no array retornado.
- A função lança `SearchError` (não expõe o erro original da SDK) quando a API do Azure AI Search retorna HTTP 503.
- O cliente não faz chamadas reais ao Azure — aceita injeção de um `searchClient` mockável.
- O campo `metadata.documentId` de cada chunk retornado é um identificador não-vazio (ex: `"PROC-042-v2"`).

**Dependências:** TASK-QE-001

**Estimativa:** M

**Arquivo a criar:** `src/services/search.ts`

---

## TASK-QE-006 — Implementar montador de prompt (context budget)

**Descrição:**
Criar o serviço que monta o prompt final a ser enviado ao LLM, combinando system prompt lido de disco, chunks recuperados e a pergunta do atendente, respeitando o context budget definido na ADR-0002 (~4K tokens para system prompt, ~8K para chunks).

**Critérios de aceite:**
- `buildPrompt({ systemPrompt, chunks, question })` retorna uma string que contém, nesta ordem: o system prompt, os chunks formatados com seu `documentId`/`section`, e a pergunta do atendente.
- Quando o conjunto de chunks excede ~8K tokens (estimativa: 1 token ≈ 4 chars), os chunks de menor `score` são descartados até caber no budget — sem lançar exceção.
- O prompt resultante nunca excede 13K tokens estimados (4K system + 8K chunks + ~1K pergunta + margem).
- Quando dois chunks são de documentos conflitantes (ex: PROC-042-v1 e PROC-042-v2), ambos são incluídos no prompt com indicação de versão — sem descartar o mais antigo silenciosamente.
- `buildPrompt` com `chunks: []` retorna prompt válido sem seção de contexto (fallback gracioso).
- A função é pura (sem I/O, sem side effects) e retorna string determinística dado o mesmo input.

**Dependências:** TASK-QE-001

**Estimativa:** M

**Arquivo a criar:** `src/services/prompt-builder.ts`

---

## TASK-QE-007 — Implementar cliente de completion (Azure OpenAI GPT-4o)

**Descrição:**
Criar o serviço que envia o prompt montado ao GPT-4o via Azure OpenAI e retorna a resposta estruturada com `answer` e `sourceDocuments` extraídos. Deve incluir retry com exponential backoff idêntico ao do cliente de embedding.

**Critérios de aceite:**
- `getCompletion(prompt)` retorna objeto com `answer: string` não-vazio quando a API responde com sucesso.
- O campo `sourceDocuments` do retorno é populado a partir das referências encontradas na resposta do LLM; não é inventado pelo serviço.
- Quando a API retorna HTTP 429 três vezes seguidas, `getCompletion` lança `CompletionError` após esgotar as tentativas de retry.
- O campo `lowConfidence: true` é retornado quando a resposta do LLM contém o prefixo de aviso de baixa confiança definido no system prompt.
- Nenhuma chamada real ao Azure é feita nos testes — o módulo aceita injeção de `openAIClient` mockável.
- A função registra via `pino` o número de tokens usados (`promptTokens`, `completionTokens`) quando disponível na resposta da API.

**Dependências:** TASK-QE-001, TASK-QE-006

**Estimativa:** M

**Arquivo a criar:** `src/services/completion.ts`

---

## TASK-QE-008 — Implementar montador de resposta HTTP

**Descrição:**
Criar o módulo que transforma o objeto `QueryResponse` (saída do serviço de completion) em uma resposta HTTP serializada, com headers corretos e validação final pelo schema Zod de output.

**Critérios de aceite:**
- `buildResponse(queryResponse)` retorna objeto com `status: 200`, `headers['Content-Type']: 'application/json'` e `body` serializável como JSON válido.
- `buildResponse` com `lowConfidence: true` inclui no body o campo `"warning": "low_confidence"`.
- `buildResponse` com `sourceDocuments: []` retorna body com array vazio (não omite o campo).
- O body nunca contém campos fora do schema `QueryResponse` validado pelo Zod — campos extras do LLM são removidos.
- `buildResponse` com input que falha na validação Zod lança `ResponseBuildError` com detalhes dos campos inválidos.

**Dependências:** TASK-QE-001, TASK-QE-002

**Estimativa:** P

**Arquivo a criar:** `src/functions/query/response-builder.ts`

---

## TASK-QE-009 — Integrar serviços no handler e remover stubs

**Descrição:**
Substituir os stubs usados em TASK-QE-003 pelas implementações reais dos serviços (embedding, search, prompt-builder, completion). O handler orquestra o pipeline completo: validate → embed → search → buildPrompt → complete → buildResponse.

**Critérios de aceite:**
- O fluxo completo `validate → embed → search → buildPrompt → complete → buildResponse` é executado sem erros quando todos os serviços são mockados com respostas válidas.
- Quando `generateEmbedding` lança `EmbeddingError`, o handler retorna HTTP 502 com body `{ "error": "upstream_embedding_failure" }`.
- Quando `searchChunks` lança `SearchError`, o handler retorna HTTP 502 com body `{ "error": "upstream_search_failure" }`.
- Quando `getCompletion` lança `CompletionError`, o handler retorna HTTP 502 com body `{ "error": "upstream_completion_failure" }`.
- O `requestId` gerado no handler é propagado como header `X-Request-Id` na resposta.
- O log de fim de request inclui `status`, `durationMs`, `chunkCount` e `tokenCount`.

**Dependências:** TASK-QE-003, TASK-QE-004, TASK-QE-005, TASK-QE-006, TASK-QE-007, TASK-QE-008

**Estimativa:** M

**Arquivo a editar:** `src/functions/query/handler.ts`

---

## TASK-QE-010 — Escrever testes de integração do handler

**Descrição:**
Criar a suíte de testes de integração que cobre o handler completo com serviços mockados via `msw`. Os testes usam os dados de referência do Anexo B (chunks e perguntas do domínio NovaTech) para fixtures realistas.

**Critérios de aceite:**
- O teste `"should return 400 when question is missing"` falha se o handler retornar status diferente de 400.
- O teste `"should return source_document when chunks are found"` verifica que `response.body.sourceDocuments` contém ao menos um item com `documentId` não-vazio.
- O teste `"should return low_confidence warning when LLM flags uncertainty"` verifica a presença de `warning: 'low_confidence'` no body.
- O teste `"should return 502 when embedding service is unavailable"` mocka o Azure OpenAI para retornar 503 e verifica HTTP 502 + body `{ error: 'upstream_embedding_failure' }`.
- Nenhum teste faz chamada real a serviços externos (msw intercepta 100% das chamadas HTTP).
- Todos os testes passam isoladamente (sem dependência de ordem de execução).

**Dependências:** TASK-QE-009

**Estimativa:** G

**Arquivo a criar:** `tests/integration/query-handler.test.ts`

---

## Ordem de implementação sugerida

```
TASK-QE-001  (tipos — base de tudo)
     ↓
TASK-QE-002  (validação Zod)
TASK-QE-004  (embedding client)   ← paralelo com QE-002
TASK-QE-005  (search client)      ← paralelo com QE-002
     ↓
TASK-QE-003  (handler com stubs)
TASK-QE-006  (prompt builder)     ← paralelo com QE-003
TASK-QE-007  (completion client)  ← depende QE-006
TASK-QE-008  (response builder)   ← paralelo com QE-007
     ↓
TASK-QE-009  (integração — conecta tudo)
     ↓
TASK-QE-010  (testes de integração)
```

---

## Resumo de estimativas

| ID | Título | Estimativa |
|---|---|---|
| TASK-QE-001 | Definir tipos TypeScript | P |
| TASK-QE-002 | Implementar validador Zod | P |
| TASK-QE-003 | Implementar handler HTTP | M |
| TASK-QE-004 | Implementar cliente de embedding | M |
| TASK-QE-005 | Implementar cliente de busca | M |
| TASK-QE-006 | Implementar montador de prompt | M |
| TASK-QE-007 | Implementar cliente de completion | M |
| TASK-QE-008 | Implementar montador de resposta HTTP | P |
| TASK-QE-009 | Integrar serviços no handler | M |
| TASK-QE-010 | Escrever testes de integração | G |
| **Total** | | **2P + 7M + 1G ≈ 20–26h** |
