# TypeScript Conventions

> **Nível:** Foundation · **Lida por:** todas as skills Domain e Artifact  
> **Frase-ativação:** Use when creating or editing any `.ts` or `.tsx` file in the project.

## 1. Contexto
Use esta skill sempre que for gerar, revisar ou refatorar código TypeScript no NovaTech Assistant, especialmente para Azure Functions, serviços compartilhados, testes e utilitários.

Esta skill existe para impedir que agentes de IA produzam código inconsistente com o projeto: o repositório usa TypeScript em `strict` mode, ESM, Azure Functions v4 e logging com `pino`. Sem estas regras, o Copilot e o Claude tendem a omitir extensões `.js`, usar `console.log`, introduzir `any` implícito e espalhar padrões incompatíveis entre módulos.

## 2. Regras prescritivas
- DEVE manter `strict: true` como padrão em todo código TypeScript e tratar qualquer aviso de tipagem como defeito a corrigir, não como algo a contornar.
- NÃO DEVE introduzir `any` implícito, parâmetros sem tipo, nem usar `as any` para silenciar o compilador.
- DEVE preferir `named exports` para funções, constantes, tipos e classes reutilizáveis; DEVE usar `default export` apenas no módulo principal quando houver uma convenção explícita para isso.
- NÃO DEVE criar exports default em cadeia para utilitários, serviços, validadores ou handlers secundários.
- DEVE usar nomes descritivos e consistentes: interfaces e types devem representar o domínio ou a forma do dado; DEVE preferir `type` para unions, aliases e composições, e `interface` para contratos de objetos extensíveis.
- NÃO DEVE usar prefixo `I` em interfaces, a menos que um arquivo legado já siga esse padrão e a alteração seja puramente local.
- NÃO DEVE usar `enum` por padrão; DEVE preferir objetos `as const` e unions literais quando um conjunto fechado de valores for necessário.
- DEVE marcar com `readonly` todos os campos, propriedades e parâmetros que não mudam após a criação do valor.
- NÃO DEVE tornar mutável algo que representa configuração, contexto de execução, resultado validado ou dados derivados que não precisam ser alterados.
- DEVE representar ausência opcional com `undefined` em APIs internas e usar `null` apenas quando o contrato externo ou a origem dos dados realmente distinguir `null` de `undefined`.
- DEVE usar optional chaining (`?.`) e nullish coalescing (`??`) para lidar com valores potencialmente ausentes, quando isso deixar o fluxo mais claro.
- NÃO DEVE usar `||` para fallback de valores que podem ser vazios por design, como `''`, `0` ou `false`.
- DEVE usar `pino` para logging estruturado em todo o projeto.
- NÃO DEVE usar `console.log`, `console.warn`, `console.error` ou qualquer outra chamada direta a `console` em código de produção.
- DEVE importar módulos internos com extensão `.js` no caminho de import, mesmo quando o arquivo fonte seja `.ts`, porque o projeto é ESM e Azure Functions v4 exige esse formato no runtime.
- NÃO DEVE omitir a extensão `.js` em imports relativos internos.
- DEVE manter imports ordenados por origem lógica: externos primeiro, depois internos por proximidade, sem misturar estilos de exportação.

## 3. Exemplos de código (DO / DON'T)

### DO / DON'T: importar com `.js` vs sem extensão
```typescript
// DO: em ESM com Azure Functions v4, o runtime resolve o import no formato final do build.
import { validateQueryRequest } from './validator.js';
import { createRequestLogger } from '../../shared/logger.js';
```

```typescript
// DON'T: isto falha no runtime ESM do projeto porque o import relativo sem extensão não é o formato esperado.
import { validateQueryRequest } from './validator';
import { createRequestLogger } from '../../shared/logger';
```

### DO / DON'T: usar `pino` vs `console.log`
```typescript
import { createRequestLogger } from '../../shared/logger.js';

const log = createRequestLogger(requestId);
log.info({ requestId, status }, 'query request processed');
```

```typescript
// DON'T: console.log ignora o padrão estruturado do projeto e quebra consistência com o logger compartilhado.
console.log('query request processed', requestId, status);
```

### DO / DON'T: `readonly` em interfaces vs campos mutáveis
```typescript
export interface QueryRequest {
	readonly question: string;
	readonly contextId?: string;
}

export interface QueryResponse {
	readonly answer: string;
	readonly sourceDocuments: ReadonlyArray<string>;
	readonly lowConfidence: boolean;
}
```

```typescript
// DON'T: campos mutáveis tornam mais fácil para a IA gerar código que altera payload validado no meio do fluxo.
export interface QueryRequest {
	question: string;
	contextId?: string;
}
```

### DO / DON'T: type assertion segura vs casting com `as`
```typescript
import { z } from 'zod';

const querySchema = z.object({
	question: z.string().min(1),
});

const parsed = querySchema.safeParse(body);

if (!parsed.success) {
	throw new Error('Invalid query payload');
}

const question = parsed.data.question;
```

```typescript
// DON'T: `as QueryRequest` apenas promete ao compilador que o dado é válido; não valida nada e esconde erro de entrada.
const payload = body as QueryRequest;
const question = payload.question;
```

### DO / DON'T: `readonly` com objetos de configuração
```typescript
export interface RetryConfig {
	readonly attempts: number;
	readonly initialDelayMs: number;
	readonly maxDelayMs: number;
}

export const defaultRetryConfig: RetryConfig = {
	attempts: 3,
	initialDelayMs: 250,
	maxDelayMs: 2000,
};
```

```typescript
// DON'T: mutação posterior de configuração compartilha estado e cria comportamento instável em handlers concorrentes.
export const retryConfig = {
	attempts: 3,
	initialDelayMs: 250,
	maxDelayMs: 2000,
};

retryConfig.attempts = 5;
```

## 4. Anti-padrões específicos de IA
- Nome: Import ESM incompleto
	```typescript
	import { createRequestLogger } from '../../shared/logger';
	```
	Por que é um problema neste projeto: o repositório é ESM e o runtime das Azure Functions v4 exige extensão `.js` nos imports relativos; sem isso o código quebra após build ou em execução.

- Nome: Logging por `console`
	```typescript
	console.error('validation failed', error);
	```
	Por que é um problema neste projeto: o projeto usa `pino` como logger estruturado; `console` produz logs inconsistentes, dificulta filtragem e ignora metadados como `requestId`.

- Nome: Tipo validado só no papel
	```typescript
	const payload = body as QueryRequest;
	```
	Por que é um problema neste projeto: o Copilot tende a gerar cast para “fazer passar” sem validar entrada; em endpoints do assistente isso mascara payloads inválidos e enfraquece a proteção dos handlers.

- Nome: Mutação de contrato
	```typescript
	interface QueryResponse {
		answer: string;
		sourceDocuments: string[];
	}

	response.sourceDocuments.push('doc-1');
	```
	Por que é um problema neste projeto: respostas e payloads são contratos entre camadas; mutabilidade facilita bugs de estado, dificulta testes e produz saídas não determinísticas.

- Nome: `enum` desnecessário para constantes de domínio
	```typescript
	enum ResponseMode {
		Direct = 'direct',
		Fallback = 'fallback',
	}
	```
	Por que é um problema neste projeto: a IA costuma introduzir `enum` por hábito, mas unions literais e objetos `as const` são mais simples, mais previsíveis e mais fáceis de serializar.

## 5. Dependências
- `error-handling.md` para padrão de erros, exceções tipadas e propagação segura de falhas.
- `project-structure.md` para organização de pastas, fronteiras de módulos e convenções de exportação.
- `testing-patterns.md` para como escrever testes TypeScript consistentes com `strict` mode.
- `azure-functions-endpoint.md` para handlers HTTP, tipos de Azure Functions e padrão de imports no runtime.
