# Exercício 3.1 — Desenvolvedor: Structured Output e Verificações Determinísticas

**Papel:** Desenvolvedor  
**Fase:** Governança e Validação  
**Tópico:** Harness Engineering  
**Ferramentas utilizadas:** GitHub Copilot + Claude (chat)

---

## 1. Schema Zod

O schema define o contrato estrutural obrigatório para toda resposta do assistente. Usa `.strict()` para rejeitar silenciosamente qualquer campo não mapeado — impedindo que informações extras passem despercebidas pelo pipeline.

```typescript
import { z } from 'zod';

export const assistantResponseSchema = z
  .object({
    answer: z
      .string({
        required_error: 'O campo "answer" é obrigatório.',
        invalid_type_error: 'O campo "answer" deve ser uma string.',
      })
      .trim()
      .min(1, { message: 'O campo "answer" não pode estar vazio.' }),
    source_document: z
      .string({
        required_error: 'O campo "source_document" é obrigatório.',
        invalid_type_error: 'O campo "source_document" deve ser uma string.',
      })
      .trim()
      .min(1, { message: 'O campo "source_document" não pode estar vazio.' }),
    confidence_score: z
      .number({
        required_error: 'O campo "confidence_score" é obrigatório.',
        invalid_type_error: 'O campo "confidence_score" deve ser um número.',
      })
      .min(0, { message: 'O campo "confidence_score" deve ser maior ou igual a 0.' })
      .max(1, { message: 'O campo "confidence_score" deve ser menor ou igual a 1.' }),
  })
  .strict();

export type AssistantResponse = z.infer<typeof assistantResponseSchema>;
```

**Campos obrigatórios e suas restrições:**

| Campo | Tipo | Restrição |
|---|---|---|
| `answer` | string | Não vazia, sem espaços extras (`.trim()`) |
| `source_document` | string | Não vazia — toda resposta deve ter fonte |
| `confidence_score` | number | Entre 0 e 1 inclusive |

---

## 2. response-validator.ts (código final pós-correções)

```typescript
import pino from 'pino';
import { z } from 'zod';

const logger = pino({ redact: ['raw'] });

export const assistantResponseSchema = z
  .object({
    answer: z
      .string({
        required_error: 'O campo "answer" é obrigatório.',
        invalid_type_error: 'O campo "answer" deve ser uma string.',
      })
      .trim()
      .min(1, { message: 'O campo "answer" não pode estar vazio.' }),
    source_document: z
      .string({
        required_error: 'O campo "source_document" é obrigatório.',
        invalid_type_error: 'O campo "source_document" deve ser uma string.',
      })
      .trim()
      .min(1, { message: 'O campo "source_document" não pode estar vazio.' }),
    confidence_score: z
      .number({
        required_error: 'O campo "confidence_score" é obrigatório.',
        invalid_type_error: 'O campo "confidence_score" deve ser um número.',
      })
      .min(0, { message: 'O campo "confidence_score" deve ser maior ou igual a 0.' })
      .max(1, { message: 'O campo "confidence_score" deve ser menor ou igual a 1.' }),
  })
  .strict();

export type AssistantResponse = z.infer<typeof assistantResponseSchema>;

export const FALLBACK_RESPONSE: AssistantResponse = {
  answer: 'Desculpe, não posso responder com segurança no momento.',
  source_document: '',
  confidence_score: 0,
};

export type ValidationResult =
  | { success: true; data: AssistantResponse }
  | { success: false; reason: string; data: typeof FALLBACK_RESPONSE };

export function validateResponse(raw: unknown): ValidationResult {
  const parsed = assistantResponseSchema.safeParse(raw);

  if (!parsed.success) {
    const reason = parsed.error.issues.map((issue) => issue.message).join('; ');
    logger.error({ motivo: reason }, 'Falha na validação da resposta do assistente');
    return { success: false, reason, data: FALLBACK_RESPONSE };
  }

  const validated = parsed.data;
  const answerLower = validated.answer.toLowerCase();

  const dangerousTerms = [
    'carga perigosa', 'carga classe', 'produto perigoso',
    'material perigoso', 'substância perigosa', 'resíduo perigoso',
    'explosivo', 'inflamável', 'corrosivo', 'mercadoria perigosa',
  ];

  const returnTerms = [
    'devolu', 'devolver', 'retornar', 'reenviar',
    'restituir', 'reexpedir', 'redirecionar',
    'recall', 'logística reversa',
  ];

  const mentionsDangerous = dangerousTerms.some((term) => answerLower.includes(term));
  const mentionsReturn = returnTerms.some((term) => answerLower.includes(term));

  if (mentionsDangerous && mentionsReturn) {
    const reason = 'Guardrail 2: resposta cita termos de carga perigosa e devolução.';
    logger.error({ motivo: reason }, 'Guardrail acionado');
    return { success: false, reason, data: FALLBACK_RESPONSE };
  }

  return { success: true, data: validated };
}
```

---

## 3. Code Review — Minha análise prévia

*Problemas identificados antes de usar o Claude:*

### Problema 1 — `FALLBACK_RESPONSE` viola o schema definido 🔴 Alto

**Classificação:** Problema de segurança + Violação do AGENTS.md (consistência de contrato)

`source_document: null` viola o próprio schema que exige `string` não vazia. A resposta de fallback nunca passaria pela validação que o próprio código define, criando um contrato incoerente.

```typescript
// Schema exige string não vazia...
source_document: z.string().min(1)
// ...mas o fallback entrega null
source_document: null, // ❌
```

**Impacto:** Quem consome `AssistantResponse | typeof FALLBACK_RESPONSE` precisa tratar `null` separadamente, quebrando type safety. Um consumer descuidado pode chamar `.trim()` em `null` e quebrar em runtime.

---

### Problema 2 — Guardrail 1 é redundante e morto 🟡 Médio

**Classificação:** Violação do AGENTS.md (lógica de guardrail deve ser efetiva)

O Guardrail 1 nunca será acionado. O schema já garante que `source_document` é uma string não vazia (`.min(1)`). Se a validação com `safeParse` passar, esse campo já é válido por definição.

```typescript
// Essa verificação nunca será verdadeira após safeParse bem-sucedido:
if (!validated.source_document || validated.source_document.trim() === '') { // ❌ morto
```

---

### Problema 3 — Guardrail 2 tem lógica frágil e contornável 🔴 Alto

**Classificação:** Problema de segurança

A detecção de termos perigosos é baseada em correspondência textual simples, sem considerar contexto semântico. Pode ser facilmente contornada e também gera falsos positivos.

```typescript
// Falso negativo — frase perigosa passa:
"A devolução de carga CLASSE 3 pode ocorrer normalmente" // "não é" ausente → escapa

// Falso positivo — frase legítima bloqueada:
"Produto perigoso não deve ser devolvido sem autorização" // bloqueado, mas é correto negar
```

Além disso, `returnTerms` usa prefixos (`'devolu'`) sem delimitadores de palavra, o que pode casar com palavras não relacionadas.

---

### Problema 4 — `console.error` expõe informações internas em produção 🔴 Alto

**Classificação:** Problema de segurança

Os logs expõem quais guardrails foram acionados, quais termos foram detectados e detalhes da falha de validação. Em ambientes onde logs são acessíveis externamente, isso revela a lógica interna do sistema de segurança.

```typescript
console.error('Guardrail 2 acionado: resposta cita carga perigosa e devolução...');
// ❌ Revela exatamente quais padrões o guardrail monitora
```

**Recomendação:** Usar um logger estruturado com níveis e redação de dados sensíveis — nunca `console.error` direto em produção. O AGENTS.md do projeto define `pino` como logger padrão.

---

### Problema 5 — Tipo de retorno impreciso da função 🟡 Médio

**Classificação:** Violação do AGENTS.md (tipagem deve refletir o contrato real)

O tipo `AssistantResponse | typeof FALLBACK_RESPONSE` é enganoso porque os dois tipos são estruturalmente incompatíveis (`source_document: string` vs `source_document: null`). Isso força os consumers a fazer type narrowing manual e propenso a erro.

```typescript
// Consumer é obrigado a fazer isso:
if (result.source_document === null) { ... }
// Mas AssistantResponse garante que source_document nunca é null — contradição de tipos
```

**Recomendação:** Criar um tipo de retorno explícito e unificado, ou usar um discriminated union com um campo `success: boolean`.

---

**Resumo da minha análise:**

| # | Problema | Classificação |
|---|---|---|
| 1 | `FALLBACK_RESPONSE` viola o schema (`null` em campo `string`) | Segurança + AGENTS.md |
| 2 | Guardrail 1 é código morto — nunca acionado | AGENTS.md |
| 3 | Guardrail 2 contornável por variações textuais | Segurança |
| 4 | `console.error` expõe lógica interna de guardrails | Segurança |
| 5 | Tipo de retorno incompatível entre os dois branches | AGENTS.md |

---

## 4. Code Review — Análise do Claude

O Claude identificou 4 problemas reais no código gerado pelo Copilot:

### Problema 1 — `FALLBACK_RESPONSE` viola o próprio schema 🔴 Alto

**O que estava errado:** `source_document: null` no fallback, mas o schema define `source_document` como `z.string()` — nunca `null`. O tipo de retorno da função ficava `AssistantResponse | typeof FALLBACK_RESPONSE`, forçando consumidores a lidar com `string | null`.

**Risco em produção:** Qualquer código que acesse `response.source_document.trim()` lança `TypeError` em runtime — justamente no caminho de erro, quando o sistema já estava degradado.

**Correção aplicada:** Tipado explicitamente como `AssistantResponse` e `source_document` alterado para string vazia `''`, compatível com o schema.

---

### Problema 2 — Guardrail 1 era dead code 🟡 Médio

**O que estava errado:** O schema já rejeita `source_document` vazio com `.min(1)`. Se o `safeParse` passou, a verificação manual subsequente nunca seria verdadeira — código que nunca executa.

**Risco em produção:** Falsa sensação de segurança. A equipe acreditava haver uma segunda linha de defesa que na prática não existia.

**Correção aplicada:** Bloco removido. A validação é feita inteiramente pelo schema Zod.

---

### Problema 3 — Guardrail 2 contornável por negação deslocada 🔴 Alto

**O que estava errado:** A lógica `!mentionsNegation` bloqueava apenas quando não havia termos de negação. Um modelo que gerasse *"Não é verdade que a devolução de carga perigosa é impossível"* passaria pelo guardrail, pois `mentionsNegation = true` — mesmo a resposta sendo perigosa.

**Risco em produção:** Respostas que afirmam ser possível devolver carga perigosa passam pelo filtro. Em logística regulada (ANTT), isso tem consequências legais e de segurança física.

**Correção aplicada:** Lógica invertida para whitelist — bloquear sempre que `mentionsDangerous && mentionsReturn`, sem exceção por negação.

---

### Problema 4 — Cobertura léxica incompleta 🟡 Médio

**O que estava errado:** Ausência de termos técnicos ANTT em `dangerousTerms` (ex: "substância perigosa", "explosivo", "inflamável") e de termos de logística reversa em `returnTerms` (ex: "recall", "logística reversa", "restituir").

**Risco em produção:** Modelo que usa vocabulário técnico ou formal passa sem detecção.

**Correção aplicada:** Ambas as listas expandidas com termos do domínio logístico e da regulação ANTT.

---

## 5. Comparação honesta — você vs. Claude

| Problema | Você identificou? | Claude identificou? | Observação |
|---|---|---|---|
| `FALLBACK` null viola schema | ✅ Sim | ✅ Sim | Ambos identificaram o problema central e o impacto de runtime |
| Guardrail 1 é dead code | ✅ Sim | ✅ Sim | Ambos chegaram à mesma conclusão com argumentação equivalente |
| Guardrail 2 contornável | ✅ Sim | ✅ Sim | Você apontou falsos positivos também; Claude focou em negação deslocada |
| Cobertura léxica incompleta | — | ✅ Sim | Claude identificou com base em conhecimento de domínio ANTT |
| `console.error` expõe lógica interna | ✅ Sim | — | Apenas você identificou — crítico em sistemas de segurança |
| Tipo de retorno incompatível | ✅ Sim | Parcial | Claude resolveu ao tipar o FALLBACK; você apontou a necessidade de um contrato explícito |

**Concordâncias:** Os 3 problemas mais graves foram identificados por ambos de forma independente — FALLBACK nulo, Guardrail 1 morto e fragilidade do Guardrail 2. Isso valida que os problemas são objetivos e não dependem de perspectiva.

**Divergências relevantes:**

- **Só você viu:** `console.error` expondo lógica interna de guardrails em produção. Este é um problema de segurança operacional — o Claude não endereçou a questão de observabilidade segura, apenas os problemas de lógica. O AGENTS.md define `pino` como logger padrão, e você aplicou essa regra corretamente.
- **Só o Claude viu em profundidade:** A cobertura léxica incompleta com termos técnicos ANTT. Exige conhecimento do domínio de logística regulada que vai além da análise do código em si.
- **Ângulos diferentes no Guardrail 2:** Você identificou o risco de falsos positivos (frases legítimas bloqueadas) além dos falsos negativos. O Claude focou apenas nos falsos negativos. O seu ponto é relevante para a UX do sistema — um guardrail muito agressivo também prejudica o atendimento.

---

## 6. Correções aplicadas

| # | O que foi corrigido | Por quê | Origem |
|---|---|---|---|
| 1 | `FALLBACK_RESPONSE` tipado como `AssistantResponse`, `source_document` alterado de `null` para `''` | Evitar violação de contrato de tipo e TypeError em runtime | Ambos |
| 2 | Bloco do Guardrail 1 manual removido | Dead code — o schema Zod já garante a mesma validação | Ambos |
| 3 | Lógica do Guardrail 2 simplificada: removida verificação `!mentionsNegation` | Negação em substring não é confiável — whitelist é mais segura | Ambos |
| 4 | `dangerousTerms` e `returnTerms` expandidos com termos técnicos ANTT e de logística reversa | Cobrir vocabulário formal que passa sem detecção | Claude |
| 5 | `console.error` substituído por `pino` com `redact: ['raw']` e logs estruturados `{ motivo }` | Seguir AGENTS.md (pino é o logger padrão) e não expor lógica interna dos guardrails em produção | Desenvolvedor |
| 6 | Tipo de retorno refatorado para discriminated union `ValidationResult` (`success: true/false`) | Eliminar union ambígua, garantir type safety nos consumers e tornar o contrato explícito | Desenvolvedor |

---

## 7. Distinção: probabilístico vs. determinístico

O sistema de governança opera em duas camadas com naturezas fundamentalmente distintas:

**Camada probabilística — prompt e LLM:** O modelo *tenta* gerar respostas corretas, citar fontes e seguir instruções. Mas pode falhar, alucinar ou ser induzido por prompt injection. Não há garantia estrutural — apenas uma distribuição de probabilidade sobre os outputs.

**Camada determinística — este código:** O `validateResponse` *garante* que certas propriedades são verdadeiras antes da resposta chegar ao atendente: o schema sempre estará presente, `source_document` nunca será vazio, e nenhuma resposta que mencione carga perigosa e devolução juntas passará adiante. Essas garantias não dependem do modelo — são verificações de código que executam sempre da mesma forma.

A limitação importante: guardrails determinísticos eliminam *classes conhecidas* de falhas estruturais, mas não substituem avaliação semântica. O Guardrail 2 detecta padrões léxicos — um modelo sofisticado com vocabulário diferente pode contorná-lo. Por isso a arquitetura correta combina as duas camadas:

```
Prompt/RAG         → reduz probabilidade de respostas ruins
Guardrails (código) → elimina classes conhecidas de falhas estruturais
Monitoramento humano → captura o que nenhuma automação previu
```
