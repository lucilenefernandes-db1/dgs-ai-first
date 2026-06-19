# Revisão Crítica — TASK-QE-001

**Data:** junho/2026
**Revisado por:** Desenvolvedor (papel Dev 2.2)
**Arquivos revisados:**
- `src/shared/types.ts`
- `src/shared/errors.ts`
- `src/shared/logger.ts`
- `src/functions/query/validator.ts`
- `src/functions/query/handler.ts`

**Ferramenta usada na geração:** GitHub Copilot (via Copilot Chat no VS Code)

---

## Resumo

O código gerado pelo Copilot é funcional e segue corretamente a estrutura
definida no plan.md e no tasks.md. A sintaxe do Azure Functions v4, a
hierarquia de erros, o uso do pino e a separação de responsabilidades entre
arquivos estão adequados. Foram identificados 3 problemas reais que precisariam
de ajuste antes de aprovação em code review.

---

## Problemas identificados

### Problema 1 — Log no `finally` não captura o status HTTP final

**Arquivo:** `src/functions/query/handler.ts`
**Critério de aceite afetado:** TASK-QE-003 — "O handler registra cada
requisição via pino com campos requestId, questionLength e durationMs"
**Impacto em produção:** Logs sem o campo `status` tornam a observabilidade
inútil — não é possível filtrar erros 4xx vs 5xx no Azure Monitor.

**Código com problema:**
```typescript
} finally {
  log.info(
    { requestId, questionLength, durationMs: Date.now() - start },
    'query request'
  );
}
```

**Código corrigido:**
```typescript
let status = 500;

try {
  const body: unknown = await request.json();
  const queryRequest = validateQueryRequest(body);
  questionLength = queryRequest.question.length;

  const response: QueryResponse = {
    answer: 'mock',
    sourceDocuments: [],
    lowConfidence: false,
  };

  status = 200;
  return { status: 200, jsonBody: response };
} catch (error) {
  if (error instanceof ValidationError) {
    status = 400;
    return {
      status: 400,
      jsonBody: { error: error.message, details: error.details },
    };
  }
  throw error;
} finally {
  log.info(
    { requestId, questionLength, durationMs: Date.now() - start, status },
    'query request'
  );
}
```

**Por que foi corrigido:** O campo `status` no log é essencial para
rastreabilidade em produção. Sem ele, uma requisição que retorna 400 e uma
que retorna 200 são indistinguíveis nos logs.

---

### Problema 2 — `request.json()` não trata body malformado

**Arquivo:** `src/functions/query/handler.ts`
**Critério de aceite afetado:** TASK-QE-003 — "POST /api/query com
Content-Type ausente ou incorreto retorna HTTP 415"
**Impacto em produção:** Um body inválido (XML, texto puro, body vazio)
lança exceção nativa do Azure Functions que não é capturada como
`ValidationError`, resultando em HTTP 500 em vez de HTTP 400/415.

**Código com problema:**
```typescript
const body: unknown = await request.json();
const queryRequest = validateQueryRequest(body);
```

**Código corrigido:**
```typescript
let body: unknown;
try {
  body = await request.json();
} catch {
  return {
    status: 400,
    jsonBody: { error: 'invalid_json', details: [] },
  };
}
const queryRequest = validateQueryRequest(body);
```

**Por que foi corrigido:** O Copilot assumiu que o body sempre chega como
JSON válido. Em produção, clientes mal configurados enviam payloads
inválidos com frequência. O handler deve retornar 400 com mensagem clara,
não deixar o runtime lançar 500.

---

### Problema 3 — Mensagens de erro do Zod são genéricas e em inglês

**Arquivo:** `src/functions/query/validator.ts`
**Critério de aceite afetado:** TASK-QE-002 — `validateQueryRequest
({ question: '' })` deve retornar erro com mensagem
`"question must not be empty"`
**Impacto em produção:** Testes que verificam mensagens literais falham.
A mensagem padrão do Zod é `"String must contain at least 1 character(s)"`,
que não corresponde ao critério definido no tasks.md.

**Código com problema:**
```typescript
question: z.string().trim().min(1).max(2000),
```

**Código corrigido:**
```typescript
question: z
  .string({ required_error: 'question is required' })
  .trim()
  .min(1, { message: 'question must not be empty' })
  .max(2000, { message: 'question must not exceed 2000 characters' }),
```

**Por que foi corrigido:** Os critérios de aceite do tasks.md especificam
mensagens literais. O Copilot não teve acesso ao tasks.md durante a geração
— gerou o schema com as mensagens padrão do Zod. A correção alinha o
comportamento real com o comportamento esperado nos testes.

---

## O que o Copilot fez bem

- Estrutura dos 5 arquivos correta e nos caminhos exatos definidos no prompt
- `errors.ts` com hierarquia de classes limpa, `readonly` nos campos e
  `this.name = this.constructor.name` para stack traces legíveis
- `logger.ts` com padrão `child()` para request logger — abordagem correta
  para propagar `requestId` sem repetir em cada chamada
- `types.ts` sem imports externos, compila com `--strict` sem erros
- Sintaxe Azure Functions v4 (`app.http`) correta — o Copilot não usou
  a sintaxe v3 deprecated (`module.exports`)
- Uso de `crypto.randomUUID()` nativo em vez de biblioteca externa

---

## Observações para o AGENTS.md

Os 3 problemas identificados sugerem que o Copilot precisaria de guidance
adicional nas seguintes áreas:

1. **Logging com status:** adicionar ao AGENTS.md a regra: "Todo handler
   DEVE incluir o campo `status` no log de fim de request, capturado antes
   do `finally`."

2. **Parsing defensivo de JSON:** adicionar ao AGENTS.md: "Todo handler
   DEVE envolver `request.json()` em try/catch e retornar HTTP 400 com
   `{ error: 'invalid_json' }` em caso de falha."

3. **Mensagens Zod customizadas:** adicionar ao AGENTS.md ou à skill
   `azure-functions-endpoint.md`: "Schemas Zod DEVEM definir mensagens
   customizadas em português para todos os campos obrigatórios e
   validações de formato."