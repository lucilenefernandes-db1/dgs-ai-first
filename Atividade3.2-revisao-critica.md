# Exercício 3.2 — Desenvolvedor: Revisão Crítica de Código Gerado por IA

**Papel:** Desenvolvedor  
**Fase:** Governança e Validação  
**Tópico:** Revisão Crítica de Outputs de IA  
**Ferramentas utilizadas:** Claude (chat) + GitHub Copilot

---

## 1. Contexto

O módulo `feedback-handler.ts` foi gerado pelo GitHub Copilot e encaminhado para revisão antes do merge. O Tech Lead pediu que o código fosse analisado criticamente antes de ir para produção. A revisão foi feita em duas etapas independentes — primeiro pelo desenvolvedor, depois pelo Claude — com comparação honesta ao final.

---

## 2. Minha análise prévia

*Problemas identificados antes de usar o Claude:*

### 🔴 Problemas de Segurança

**Problema 1 — `as any` no parse do body**  
**Classificação:** Violação do AGENTS.md + Problema de segurança

O cast `as any` desabilita toda verificação de tipo. Campos maliciosos ou inesperados do body são aceitos sem validação e gravados diretamente no banco.

```typescript
const body = await request.json() as any; // ❌
```

---

**Problema 2 — Dados do body gravados sem sanitização**  
**Classificação:** Problema de segurança

`body.queryId`, `body.rating`, `body.comment` e `body.attendantEmail` vão direto para o CosmosDB sem nenhuma validação de formato, tipo ou tamanho. Abre margem para injeção de dados inválidos ou maliciosos.

---

**Problema 3 — `console.log` logando dados sensíveis**  
**Classificação:** Violação do AGENTS.md + Problema de segurança

O e-mail do atendente e o comentário (potencialmente com dados pessoais) são serializados e logados via `JSON.stringify(feedback)`. Isso pode violar LGPD/GDPR dependendo do contexto.

```typescript
console.log('Feedback recebido:', JSON.stringify(feedback)); // ❌ loga attendantEmail
```

---

### 🟠 Bugs Potenciais

**Problema 4 — Sem tratamento de erro**  
**Classificação:** Bug potencial

Não há `try/catch`. Se o CosmosDB estiver indisponível ou o body vier malformado, a função lança uma exceção não tratada, retornando 500 sem mensagem útil.

---

**Problema 5 — `request.json()` pode lançar exceção silenciosa**  
**Classificação:** Bug potencial

Se o `Content-Type` não for `application/json` ou o body estiver corrompido, o `await request.json()` falha sem nenhum fallback.

---

**Problema 6 — Campos obrigatórios não verificados**  
**Classificação:** Bug potencial

`queryId` e `rating` são obrigatórios para o negócio, mas o código aceita e persiste o objeto mesmo se ambos forem `undefined`.

---

### 🔵 Violações de AGENTS.md / Boas Práticas

**Problema 7 — `require()` dinâmico dentro de função**  
**Classificação:** Violação do AGENTS.md

O `CosmosClient` é importado com `require()` dentro do corpo da função, misturando CommonJS com ESModules e recriando o cliente a cada requisição. O import deveria estar no topo e o cliente instanciado uma única vez (singleton).

```typescript
const { CosmosClient } = require('@azure/cosmos'); // ❌ dentro da função
```

---

**Problema 8 — Ausência de tipo explícito para o body**  
**Classificação:** Violação do AGENTS.md

O uso de `as any` em vez de uma interface (`FeedbackBody`) vai contra o propósito do TypeScript e os padrões do AGENTS.md que exigem tipagem estrita.

---

**Problema 9 — Nomes de DB e container hardcoded**  
**Classificação:** Boas práticas

`'novatech'` e `'feedbacks'` estão literais no código. Deveriam ser constantes nomeadas ou variáveis de ambiente para facilitar troca entre ambientes (dev/staging/prod).

---

**Problema 10 — Retorno sem JSON estruturado**  
**Classificação:** Boas práticas

`body: 'OK'` retorna uma string plana. O padrão REST esperado seria um JSON (`{ message: 'OK' }`), com o `Content-Type` correto.

---

**Resumo da minha análise:**

| # | Problema | Classificação |
|---|---|---|
| 1 | `as any` sem validação Zod | Segurança + AGENTS.md |
| 2 | Dados gravados sem sanitização | Segurança |
| 3 | `console.log` logando `attendantEmail` | Segurança + AGENTS.md |
| 4 | Sem `try/catch` | Bug potencial |
| 5 | `request.json()` sem fallback | Bug potencial |
| 6 | Campos obrigatórios não verificados | Bug potencial |
| 7 | `require()` dinâmico dentro da função | AGENTS.md |
| 8 | Ausência de tipo explícito para o body | AGENTS.md |
| 9 | Nomes de DB e container hardcoded | Boas práticas |
| 10 | Retorno `'OK'` como string plana | Boas práticas |

---

## 3. Análise do Claude

O Claude identificou 6 problemas reais, todos com fundamentação técnica precisa:

| # | Problema | Classificação |
|---|---|---|
| 1 | `as any` sem validação Zod | Violação AGENTS.md + Bug potencial |
| 2 | `console.log` em vez de `pino` | Violação AGENTS.md |
| 3 | Log de `attendantEmail` | Violação AGENTS.md + Segurança |
| 4 | `require()` dinâmico dentro da função | Violação AGENTS.md |
| 5 | `CosmosClient` recriado por requisição | Bug potencial |
| 6 | `process.env` sem validação de presença | Bug potencial |

O Claude destacou especificamente que `process.env.COSMOS_CONNECTION_STRING` é `string | undefined` no TypeScript strict mode — se a variável não estiver definida, o SDK falha de forma obscura em runtime em vez de lançar uma mensagem clara na inicialização do serviço.

---

## 4. Comparação honesta — minha análise vs. Claude

| Problema | Eu identifiquei? | Claude identificou? |
|---|---|---|
| `as any` sem Zod | ✅ Sim | ✅ Sim |
| `attendantEmail` logado | ✅ Sim | ✅ Sim |
| `console.log` em vez de pino | ✅ Sim | ✅ Sim |
| `require()` dinâmico | ✅ Sim | ✅ Sim |
| Sem `try/catch` / exceções não tratadas | ✅ Sim | ✅ Sim |
| `CosmosClient` recriado por requisição (singleton) | ✅ Sim | ✅ Sim |
| `process.env` sem validação de presença | — | ✅ Sim |
| Campos obrigatórios não verificados | ✅ Sim | — (coberto implicitamente pelo Zod) |
| Nomes de DB e container hardcoded | ✅ Sim | — |
| Retorno sem JSON estruturado | ✅ Sim | — |

**Concordâncias:** Os 6 problemas mais graves foram identificados por ambos de forma independente — `as any`, `attendantEmail` logado, `console.log`, `require()` dinâmico, ausência de tratamento de erro e singleton do cliente. Isso valida que os problemas são objetivos.

**O que só o Claude viu:** A validação de presença do `process.env.COSMOS_CONNECTION_STRING`. É um erro de *startup* — como o cliente é instanciado fora do handler (no escopo do módulo), uma variável de ambiente ausente derruba o serviço inteiro na inicialização, não apenas uma requisição. Difícil de debugar em produção sem essa verificação explícita.

**O que só eu vi:** Três pontos que o Claude não endereçou — campos obrigatórios não verificados explicitamente como risco de negócio (o Zod resolve tecnicamente, mas o Claude não nomeou o risco), nomes de DB hardcoded impedindo multi-ambiente, e o retorno `'OK'` como string plana quebrando o contrato REST. Os dois últimos são de boas práticas, não de segurança crítica, mas impactam manutenibilidade e consistência da API.

---

## 5. Código reescrito — handler.ts final

**Processo de geração com o Copilot:** O GitHub Copilot gerou aproximadamente 85% do handler corretamente a partir de um prompt detalhado com as regras do AGENTS.md (Zod, pino, imports estáticos, singleton, try/catch). Foram necessários dois ajustes após a geração inicial: (1) o Copilot instanciou o `CosmosClient` dentro do handler em vez de no escopo do módulo — foi necessário um segundo prompt explícito para mover o singleton para fora da função; (2) o retorno de sucesso foi gerado como `body: 'OK'` em vez de `jsonBody` — corrigido via prompt adicional para seguir o contrato REST. O `redact` do pino e a validação de presença do `connectionString` no startup foram gerados corretamente sem ajuste.

**Nota regulatória — `attendantEmail` em repouso:** O campo `attendantEmail` é persistido no CosmosDB em texto claro. O código corrigido resolve o vazamento via logs, mas não aborda o armazenamento. Para um sistema em produção com dados de funcionários, o próximo passo natural seria avaliar: (a) se o e-mail é necessário para o caso de uso ou pode ser substituído por um ID interno anonimizado; (b) se deve ser criptografado em repouso ou pseudonimizado antes da gravação; (c) qual a política de retenção e quem tem acesso ao container no CosmosDB. Essas decisões excedem o escopo deste exercício, mas são o próximo nível de análise de segurança de dados em conformidade com LGPD.

```typescript
import { CosmosClient } from '@azure/cosmos';
import { app, HttpRequest, HttpResponseInit } from '@azure/functions';
import pino from 'pino';
import { z } from 'zod';

const connectionString = process.env.COSMOS_CONNECTION_STRING;
if (!connectionString) {
  throw new Error('COSMOS_CONNECTION_STRING não configurada.');
}

const databaseName = process.env.COSMOS_DATABASE_NAME ?? 'novatech';
const containerName = process.env.COSMOS_CONTAINER_NAME ?? 'feedbacks';

const client = new CosmosClient(connectionString);
const database = client.database(databaseName);
const container = database.container(containerName);

const logger = pino({ redact: ['body.attendantEmail', 'feedback.attendantEmail'] });

const feedbackBodySchema = z.object({
  queryId: z.string().trim().min(1, { message: 'queryId é obrigatório.' }),
  rating: z
    .number({ invalid_type_error: 'rating deve ser um número.' })
    .min(1, { message: 'rating deve ser no mínimo 1.' })
    .max(5, { message: 'rating deve ser no máximo 5.' }),
  comment: z.string().optional(),
  attendantEmail: z.string().email({ message: 'attendantEmail deve ser um e-mail válido.' }),
});

type FeedbackBody = z.infer<typeof feedbackBodySchema>;

export async function feedbackHandler(request: HttpRequest): Promise<HttpResponseInit> {
  let body: unknown;

  try {
    body = await request.json();
  } catch {
    const reason = 'Body JSON inválido.';
    logger.error({ motivo: reason }, 'Falha de validação do payload de feedback');
    return {
      status: 400,
      jsonBody: { error: 'Payload inválido.', details: reason },
    };
  }

  const parsed = feedbackBodySchema.safeParse(body);
  if (!parsed.success) {
    const reason = parsed.error.issues.map((issue) => issue.message).join('; ');
    logger.error({ motivo: reason }, 'Falha de validação do payload de feedback');
    return {
      status: 400,
      jsonBody: { error: 'Payload inválido.', details: reason },
    };
  }

  const validBody: FeedbackBody = parsed.data;

  const feedback = {
    queryId: validBody.queryId,
    rating: validBody.rating,
    comment: validBody.comment,
    attendantEmail: validBody.attendantEmail, // persistido — ver nota regulatória acima
    timestamp: new Date().toISOString(),
  };

  logger.info(
    { queryId: feedback.queryId, rating: feedback.rating },
    'Feedback recebido'
  );

  try {
    await container.items.create(feedback);
    return { status: 200, jsonBody: { message: 'Feedback registrado com sucesso.' } };
  } catch {
    const reason = 'Falha ao persistir feedback no CosmosDB.';
    logger.error({ motivo: reason }, 'Erro ao salvar feedback');
    return {
      status: 500,
      jsonBody: { error: 'Erro interno ao processar feedback.' },
    };
  }
}

app.http('feedback', {
  methods: ['POST'],
  handler: feedbackHandler,
});
```

---

## 6. Correções aplicadas

| # | Problema corrigido | Regra do AGENTS.md / princípio aplicado |
|---|---|---|
| 1 | `as any` removido — body validado com `feedbackBodySchema.safeParse()` | Zod para validação de input obrigatório |
| 2 | `console.log` removido — substituído por `pino` com logs estruturados | `pino` para logging (nunca `console.log`) |
| 3 | `attendantEmail` não aparece em nenhuma chamada do logger — `redact` no pino como proteção adicional | Nunca logar dados pessoais |
| 4 | `require()` dinâmico removido — `CosmosClient` importado estaticamente no topo | Imports estáticos no topo (nunca `require` dinâmico) |
| 5 | `CosmosClient` instanciado uma única vez no escopo do módulo (singleton) | Boas práticas de performance e gestão de conexões |
| 6 | `process.env.COSMOS_CONNECTION_STRING` validado no startup — `throw` imediato se ausente | TypeScript strict mode + fail-fast na inicialização |
| 7 | `try/catch` adicionado em torno do `request.json()` e da operação no CosmosDB | Bug potencial — exceções não tratadas |
| 8 | Erros retornam `jsonBody` estruturado (400 para validação, 500 para banco) sem expor internos | Contrato REST + segurança de informação |
| 9 | Retorno de sucesso alterado de `body: 'OK'` para `jsonBody: { message: '...' }` | Contrato REST consistente |
| 10 | Tipo `FeedbackBody` inferido do schema Zod — nenhum `as any` no código | TypeScript strict mode |
| 11 | Nomes de DB e container extraídos para `process.env.COSMOS_DATABASE_NAME` e `process.env.COSMOS_CONTAINER_NAME` com fallback | Configurabilidade multi-ambiente — sem valores literais no código |
