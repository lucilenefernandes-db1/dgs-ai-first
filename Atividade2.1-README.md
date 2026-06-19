# .mcp/README.md — Documentação dos MCP Servers

> **Projeto:** NovaTech Assistant | **Fase:** Estruturação | **Exercício:** Dev 2.1
>
> Este arquivo documenta cada server configurado em `.mcp/mcp.json`. É a referência principal para qualquer membro do time entender o propósito, escopo e restrições de cada server — sem precisar consultar documentos externos. Toda alteração no `mcp.json` deve ser acompanhada de atualização aqui.

---

## Índice

| Server | Propósito resumido | Permissão |
|---|---|---|
| [filesystem-src](#filesystem-src) | Leitura e escrita de artefatos de desenvolvimento | Leitura + escrita |
| [filesystem-docs-readonly](#filesystem-docs-readonly) | Consulta à documentação oficial de negócio da NovaTech | Somente leitura |
| [filesystem-corpus-readonly](#filesystem-corpus-readonly) | Recuperação de chunks do corpus RAG para testes | Somente leitura |
| [git](#git) | Acesso ao histórico, diffs e branches do repositório local | Somente leitura (histórico) |
| [memory](#memory) | Memória persistente de decisões e linguagem ubíqua | Leitura + escrita (no grafo) |
| [mcp-learning-everything](#mcp-learning-everything) | Aprendizado das primitivas MCP — somente onboarding | N/A (exemplos canônicos) |

---

## filesystem-src

| Atributo | Valor |
|---|---|
| **Propósito** | Permite que agentes de IA leiam e escrevam artefatos de desenvolvimento: código-fonte, specs SDD e skills do projeto. |
| **Escopo configurado** | `./src`, `./specs`, `./skills` |
| **Permissão efetiva** | **Leitura + escrita.** O server filesystem não distingue permissão por pasta — a escrita é habilitada intencionalmente para que agentes possam criar e modificar arquivos de trabalho. |
| **Como a escrita é controlada** | Gate humano: todo arquivo gerado ou modificado por agente passa por code review (PR com aprovação do Tech Lead) antes de merge. O server não faz commit autônomo. |
| **Quem consome** | GitHub Copilot e Claude — papel **Dev** e **Tech Lead**. |
| **O que está excluído (e por quê)** | Raiz do repositório: evita exposição de `.env`, `package.json`, `tsconfig.json` e workflows de CI/CD (`.github/`). Documentação de negócio e corpus RAG: cobertos por instâncias separadas, com escopo restrito a leitura. `infra/`: arquivos Bicep que provisionam recursos Azure não devem ser modificados por agentes sem revisão explícita. |

---

## filesystem-docs-readonly

| Atributo | Valor |
|---|---|
| **Propósito** | Permite que agentes consultem a documentação oficial de negócio da NovaTech (políticas, procedimentos, tabelas de SLA) para gerar código e respostas corretas. |
| **Escopo configurado** | `./docs/novatech` |
| **Permissão efetiva** | **Somente leitura** — por convenção e política documentada no `AGENTS.md`. O server filesystem não possui flag read-only nativa; a restrição é garantida pela combinação de instância separada (sem acesso a `./src`) + regra explícita no `AGENTS.md` proibindo escrita nesta pasta. |
| **Quem consome** | GitHub Copilot e Claude — **todos os papéis** do time. |
| **Por que read-only é obrigatório** | Esta pasta é a fonte de verdade do domínio. Qualquer escrita acidental ou induzida por prompt injection corromperia silenciosamente as políticas que governam o comportamento do assistente em produção — sem rastreabilidade imediata. |
| **Documentos presentes** | `POL-001` (Política de Devolução), `PROC-042` e `PROC-042-v2` (Frete Especial), `SLA-2024` (Tabela de SLA), `FAQ-Atendimento`. |

---

## filesystem-corpus-readonly

| Atributo | Valor |
|---|---|
| **Propósito** | Permite que agentes recuperem chunks do corpus de retrieval para testes e validação do pipeline RAG, simulando o comportamento do Azure AI Search em produção. |
| **Escopo configurado** | `./data/retrieval-corpus` |
| **Permissão efetiva** | **Somente leitura** — mesma estratégia da instância `filesystem-docs-readonly`: instância separada + regra no `AGENTS.md`. |
| **Quem consome** | GitHub Copilot e Claude — papel **Dev** e **QA**. |
| **Por que read-only é obrigatório** | O corpus é gerado exclusivamente pelo pipeline de ingestão (`src/pipeline/`). Escrita direta por agentes adulteraria os dados de retrieval sem passar pelo processo de chunking e validação, comprometendo a qualidade das respostas do assistente em todos os ambientes. |

---

## git

| Atributo | Valor |
|---|---|
| **Propósito** | Fornece acesso semântico ao histórico do repositório local: commits, diffs, branches e status. Permite que agentes entendam decisões anteriores e o contexto de código existente. |
| **Escopo configurado** | `.` (raiz do repositório local, via `--repository .`) |
| **Permissão efetiva** | **Somente leitura do histórico.** O server expõe operações de consulta (`git_log`, `git_diff`, `git_status`, `git_show`, `git_branch`). Não executa `commit`, `push` ou `merge` de forma autônoma. |
| **Quem consome** | GitHub Copilot e Claude — papel **Dev** e **Tech Lead**. |
| **O que está excluído** | Acesso a remotes, credenciais ou tokens. O server opera exclusivamente no repositório local — não há remote configurado nesta fase do projeto. |

---

## memory

| Atributo | Valor |
|---|---|
| **Propósito** | Mantém um grafo de conhecimento persistente entre sessões: decisões arquiteturais, glossário de domínio (linguagem ubíqua) e contexto de projeto que não deve ser repetido a cada nova sessão. |
| **Escopo configurado** | Grafo local interno do server — não acessa o filesystem do projeto. |
| **Permissão efetiva** | **Leitura + escrita no grafo persistente.** Exemplos de entidades registradas: `"cliente Gold = tier com contrato anual > R$500k ou > 200 operações/mês"`, `"frete especial = carga acima de 500kg"`, `"context budget = 4K tokens (system prompt) + 8K tokens (chunks)"`. |
| **Quem consome** | Claude — **Tech Lead**, **Product Specialist** e **Delivery Manager** escrevem entidades; **Dev** lê. |
| **Controle de escrita** | Convenção: apenas papéis com autoridade sobre decisões arquiteturais ou de produto adicionam ou modificam entidades no grafo. Escrita irrestrita por qualquer agente poderia sobrescrever definições da linguagem ubíqua e corromper o vocabulário compartilhado. |

---

## mcp-learning-everything

| Atributo | Valor |
|---|---|
| **Propósito** | Server de referência para aprendizado das primitivas MCP (tools, resources, prompts). Usado exclusivamente em sessões de onboarding e exploração do protocolo — **não para desenvolvimento real**. |
| **Escopo configurado** | Nenhum — não acessa pastas do projeto. |
| **Permissão efetiva** | N/A — as tools e resources são exemplos canônicos sem semântica de domínio (ex: `echo`, recursos fictícios, prompts de demonstração). |
| **Quem consome** | Claude — papel **Dev**, apenas durante onboarding individual. |
| **Restrição crítica** | ⚠️ **NÃO usar em fluxos de desenvolvimento real ou de produção.** Suas tools genéricas podem confundir agentes sobre quais capacidades estão disponíveis no projeto. Deve ser **removido do `mcp.json` compartilhado** após a conclusão do onboarding do time. |

---

## Política de alterações neste arquivo

Qualquer mudança no `mcp.json` exige:

1. Atualização correspondente neste `README.md` (mesma PR).
2. Revisão de escopo pelo Tech Lead: confirmar que nenhuma pasta sensível foi adicionada e que o princípio de least privilege foi mantido.
3. Se um novo server for adicionado: justificativa documentada de por que os servers existentes não cobrem a necessidade.
4. Se o escopo de um server existente for ampliado: justificativa de por que o escopo anterior era insuficiente e análise de risco da ampliação.

> **Decisão de design sobre read-only:** ver `docs/adr/` — a estratégia de separação em instâncias nomeadas e suas limitações estão documentadas no artefato de Decisão de Design (Tarefa 2, Artefato 3).
