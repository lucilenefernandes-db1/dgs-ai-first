# Árvore de Skills — NovaTech Assistant

> **Hierarquia:** Foundation → Domain → Artifact  
> **Repositório:** `db1/novatech-assistant`  
> **Stack:** TypeScript strict · Azure Functions v4 · Zod · pino · Vitest · msw · React · Azure AI Search · Azure OpenAI

---

## Foundation — Convenções Globais

Skills base lidas por todas as outras. Todo agente consulta ao menos uma delas antes de gerar qualquer artefato.

| Arquivo | Título | Frase-ativação | Cria | Consome | Frequência |
|---|---|---|---|---|---|
| `typescript-conventions.md` | TypeScript Conventions | Use when creating or editing any `.ts` or `.tsx` file in the project — defines naming, imports, strict mode, and module structure. | Tech Lead | Dev + Copilot; TL + Copilot | **Alta** — todo arquivo gerado é TypeScript |
| `error-handling.md` | Error Handling | Use when a function can fail, call an external service, or must log an error — defines custom error types, retry patterns, and pino logging. | Tech Lead | Dev + Copilot | **Alta** — qualquer endpoint, service ou pipeline pode falhar |
| `project-structure.md` | Project Structure | Use when creating a new module, file, or directory — defines onde código vive no repositório e as convenções de export. | Tech Lead | Dev + Copilot; TL + Copilot; todos os papéis + Claude | **Alta** — referência constante ao criar qualquer artefato novo |

---

## Domain — Padrões por Camada Técnica

Skills que encapsulam os padrões de cada camada do sistema. Dependem das Foundation e são lidas pelas Artifact.

| Arquivo | Título | Frase-ativação | Cria | Consome | Frequência |
|---|---|---|---|---|---|
| `azure-functions-endpoint.md` | Azure Functions Endpoint | Use when creating an HTTP trigger Azure Function — defines handler structure, Zod validation, response shape, and error boundaries. | Tech Lead | Dev + Copilot; TL + Copilot | **Alta** — 4 endpoints previstos, mais eventuais novos no futuro |
| `azure-ai-search-integration.md` | Azure AI Search Integration | Use when querying or indexing documents in Azure AI Search — defines client setup, query parameters, result shape, and retry logic. | Tech Lead | Dev + Copilot | **Média** — central ao RAG, mas concentrado em poucos módulos |
| `react-components.md` | React Components | Use when creating a React component for the web panel — defines component structure, prop typing, state management, and accessibility patterns. | Tech Lead / Dev sênior | Dev + Copilot | **Média** — escopo limitado ao painel web interno |
| `testing-patterns.md` | Testing Patterns | Use when writing any test file — defines Vitest setup, msw mock patterns, arrange/act/assert structure, and fixture conventions. | QA + Tech Lead | Dev + Copilot; QA + Claude | **Alta** — todo módulo implementado deve ter testes |

---

## Artifact — Receitas de Geração Específicas

Skills que encapsulam o artefato completo, do início ao fim. As mais ricas em exemplos e as mais diretamente consumidas pelos agentes no momento de geração.

| Arquivo | Título | Frase-ativação | Cria | Consome | Frequência |
|---|---|---|---|---|---|
| `create-rag-endpoint.md` | Create RAG Endpoint | Use when creating an endpoint that receives a user question, retrieves chunks from Azure AI Search, and returns a grounded answer with source citation. | Tech Lead + Dev sênior | Dev + Copilot; TL + Copilot | **Alta** — padrão central do projeto; todo endpoint novo herda esse padrão |
| `create-integration-test.md` | Create Integration Test | Use when writing a test that exercises an endpoint or service boundary using msw to mock HTTP calls — covers arrange/act/assert with realistic RAG fixtures. | QA + Tech Lead | Dev + Copilot; QA + Claude | **Alta** — todo endpoint gerado requer teste de integração correspondente |
| `create-react-card.md` | Create React Card | Use when building a response card or feedback form component for the web panel — defines layout, prop interface, and Adaptive Card parity. | Dev + Product Specialist | Dev + Copilot | **Média** — escopo restrito ao painel web, mas componente reutilizado várias vezes |

---

## Dependências entre Skills

### Domain → Foundation

#### `azure-functions-endpoint` lê (obrigatório):
- `typescript-conventions` — define tipagem, naming e estrutura de imports do handler
- `error-handling` — define como tratar falhas nas chamadas ao Azure e retry com backoff
- `project-structure` — define onde o handler, validator e response-builder ficam em `src/functions/`

#### `azure-ai-search-integration` lê (obrigatório):
- `typescript-conventions` — tipagem dos parâmetros de query e shape dos resultados
- `error-handling` — central: todas as chamadas ao Azure AI Search precisam de retry com backoff exponencial

#### `react-components` lê (obrigatório):
- `typescript-conventions` — tipagem de props, interfaces e hooks
- `project-structure` — define onde o componente vive dentro de `src/web/src/components/`

> `error-handling` não é mandatório para React Components — componentes não fazem chamadas diretas a APIs externas; isso fica em serviços separados.

#### `testing-patterns` lê (obrigatório):
- `typescript-conventions` — tipagem de fixtures, factories e mocks
- `error-handling` — testes de integração exercitam exatamente os pontos de falha documentados aqui
- `project-structure` — determina onde fixtures e mocks ficam dentro de `tests/`

---

### Artifact → Domain

#### `create-rag-endpoint` lê:
- **Obrigatório:** `azure-functions-endpoint` + `azure-ai-search-integration`  
  É a composição direta dessas duas skills — um endpoint HTTP que chama o Azure AI Search.
- **Recomendado:** `testing-patterns`  
  A skill Artifact inclui um exemplo de teste junto ao código do endpoint.

#### `create-integration-test` lê:
- **Obrigatório:** `testing-patterns`  
  Define todo o scaffolding de Vitest, msw e fixtures que o teste usa.
- **Recomendado:** `azure-functions-endpoint` + `azure-ai-search-integration`  
  Necessário para entender o formato de resposta que o teste deve verificar; sem isso, os mocks ficam genéricos e não cobrem o shape real do endpoint RAG.

#### `create-react-card` lê:
- **Obrigatório:** `react-components`  
  Define a estrutura de props, layout e acessibilidade do card.
- **Recomendado:** `testing-patterns`  
  Cards de resposta devem ter testes de renderização (snapshot e interação).

---

## Grafo resumido de dependências

```
Foundation
├── typescript-conventions ──┬──> azure-functions-endpoint
│                            ├──> azure-ai-search-integration
│                            ├──> react-components
│                            └──> testing-patterns
│
├── error-handling ──────────┬──> azure-functions-endpoint
│                            ├──> azure-ai-search-integration
│                            └──> testing-patterns
│
└── project-structure ───────┬──> azure-functions-endpoint
                             ├──> react-components
                             └──> testing-patterns

Domain
├── azure-functions-endpoint ─────┬──> create-rag-endpoint      (obrigatório)
│                                 └──> create-integration-test   (recomendado)
│
├── azure-ai-search-integration ──┬──> create-rag-endpoint      (obrigatório)
│                                 └──> create-integration-test   (recomendado)
│
├── react-components ─────────────> create-react-card           (obrigatório)
│
└── testing-patterns ─────────────┬──> create-integration-test  (obrigatório)
                                  └──> create-react-card         (recomendado)
```

---

## Notas de expansão

Se o projeto crescer para cobrir os Adaptive Cards do Teams Bot, a hierarquia acomoda isso sem quebrar dependências existentes:

- Nova skill Domain: `bot-teams-card.md` — dependeria de `typescript-conventions` + `project-structure`
- Nova skill Artifact: `create-adaptive-card.md` — dependeria de `bot-teams-card` + `testing-patterns`

Qualquer nova skill Domain deve sempre declarar suas dependências Foundation explicitamente no cabeçalho do arquivo, no campo `reads:`, para que os agentes saibam o que carregar antes de usar a skill.
