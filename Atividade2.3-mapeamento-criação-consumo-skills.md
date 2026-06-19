# Mapeamento de Skills por Papel — NovaTech Assistant

> **Referência:** Árvore de skills em `skills-novatech-assistant.md`  
> **Time:** Tech Lead · Dev Sênior · Dev Pleno · QA · Product Specialist · Delivery Manager  
> **Agentes disponíveis:** GitHub Copilot (devs e Tech Lead) · Claude chat (todos os papéis)

---

## Tech Lead

| Skill | Papel na skill | Agente | Etapa SDD |
|---|---|---|---|
| `typescript-conventions` | **CRIA e mantém** | Claude (rascunho inicial) → Copilot (valida com geração de código) | Plan |
| `error-handling` | **CRIA e mantém** | Claude (rascunho) → Copilot (valida exemplos de retry/pino) | Plan |
| `project-structure` | **CRIA e mantém** | Claude (rascunho) | Plan |
| `azure-functions-endpoint` | **CRIA e mantém** | Claude (rascunho) → Copilot (valida com endpoint real) | Plan / Implement |
| `azure-ai-search-integration` | **CRIA e mantém** | Claude (rascunho) → Copilot (valida com query real) | Plan / Implement |
| `testing-patterns` | **CRIA e co-mantém com QA** | Claude (rascunho) → Copilot (valida com teste real) | Plan |
| `create-rag-endpoint` | **CRIA e mantém** | Copilot (valida iterando sobre a receita) | Implement |
| `typescript-conventions` | **CONSOME** ao revisar PRs e ao gerar código de referência | Copilot | Review |
| `error-handling` | **CONSOME** ao revisar tratamento de erros em PRs | Copilot | Review |
| `azure-functions-endpoint` | **CONSOME** ao gerar endpoints de exemplo e arquitetura | Copilot | Implement / Review |
| `azure-ai-search-integration` | **CONSOME** ao definir contratos de integração | Copilot | Plan / Review |
| `create-rag-endpoint` | **CONSOME** ao revisar endpoints gerados pelos devs | Copilot | Review |
| `create-integration-test` | **CONSOME** ao revisar testes gerados pelos devs | Copilot | Review |

**Resumo do papel:** O Tech Lead é o principal **autor** da hierarquia Foundation e das skills Domain de backend. Consome as skills no Review para avaliar se o código gerado pelos devs está aderente aos padrões que ele mesmo definiu. Usa o Copilot não só para gerar código, mas como **ferramenta de validação** das próprias skills — se o Copilot não segue a skill, ela precisa ser reescrita.

---

## Desenvolvedor Sênior

| Skill | Papel na skill | Agente | Etapa SDD |
|---|---|---|---|
| `create-rag-endpoint` | **CO-CRIA** com o Tech Lead (contribui com exemplos DO/DON'T reais) | Copilot (gera variações para teste) | Implement |
| `create-integration-test` | **CO-CRIA** com QA (contribui com exemplos de integração) | Copilot | Implement |
| `create-react-card` | **CO-CRIA** com Product Specialist (contribui com lógica de componente) | Copilot | Implement |
| `typescript-conventions` | **CONSOME** antes de criar qualquer arquivo `.ts` | Copilot | Implement |
| `error-handling` | **CONSOME** ao implementar qualquer chamada externa | Copilot | Implement |
| `project-structure` | **CONSOME** ao criar módulos, pastas ou novos arquivos | Copilot | Tasks / Implement |
| `azure-functions-endpoint` | **CONSOME** ao implementar endpoints | Copilot | Implement |
| `azure-ai-search-integration` | **CONSOME** ao integrar com o Azure AI Search | Copilot | Implement |
| `testing-patterns` | **CONSOME** ao escrever testes | Copilot | Implement |
| `create-rag-endpoint` | **CONSOME** ao implementar novos endpoints RAG | Copilot | Implement |
| `create-integration-test` | **CONSOME** ao escrever testes de integração | Copilot | Implement |
| `create-react-card` | **CONSOME** ao criar cards para o painel web | Copilot | Implement |

**Resumo do papel:** O Dev Sênior é o principal **consumidor** das skills Artifact e o principal **co-autor** delas — é quem usa as receitas no dia a dia e, quando encontra lacunas ou anti-padrões não cobertos, abre um PR de atualização da skill. Atua como ponte entre a intenção do Tech Lead (que escreve as skills) e a realidade do código gerado.

---

## Desenvolvedor Pleno

| Skill | Papel na skill | Agente | Etapa SDD |
|---|---|---|---|
| `typescript-conventions` | **CONSOME** antes de criar qualquer arquivo `.ts` | Copilot | Implement |
| `error-handling` | **CONSOME** ao implementar chamadas externas | Copilot | Implement |
| `project-structure` | **CONSOME** ao criar arquivos e pastas | Copilot | Tasks / Implement |
| `azure-functions-endpoint` | **CONSOME** ao implementar endpoints | Copilot | Implement |
| `testing-patterns` | **CONSOME** ao escrever testes unitários e de integração | Copilot | Implement |
| `create-rag-endpoint` | **CONSOME** ao implementar endpoints RAG | Copilot | Implement |
| `create-integration-test` | **CONSOME** ao escrever testes de integração | Copilot | Implement |
| `create-react-card` | **CONSOME** ao criar componentes para o painel web | Copilot | Implement |

**Resumo do papel:** O Dev Pleno é **consumidor primário** das skills, especialmente das Artifact. Não cria nem mantém skills — mas tem responsabilidade ativa de **reportar gaps**: quando a skill não é suficiente para guiar o Copilot em um caso concreto, abre uma issue no repositório descrevendo o problema para que o Dev Sênior ou Tech Lead atualize a skill.

---

## QA

| Skill | Papel na skill | Agente | Etapa SDD |
|---|---|---|---|
| `testing-patterns` | **CO-CRIA e mantém** com Tech Lead (autora dos padrões de asserção, nomenclatura e fixtures) | Claude (rascunho e revisão) | Plan |
| `create-integration-test` | **CO-CRIA e mantém** com Tech Lead e Dev Sênior (autora dos critérios de qualidade da receita) | Claude (rascunho de exemplos DO/DON'T) | Plan / Review |
| `testing-patterns` | **CONSOME** ao escrever test plans e ao revisar testes gerados pelos devs | Claude | Plan / Review |
| `create-integration-test` | **CONSOME** ao validar se os testes gerados pelos devs seguem a receita | Claude | Review |
| `azure-functions-endpoint` | **CONSOME** (leitura) ao escrever testes para entender o shape de resposta esperado | Claude | Plan |
| `create-rag-endpoint` | **CONSOME** (leitura) ao definir cenários de teste baseados no comportamento do endpoint | Claude | Plan |

**Resumo do papel:** O QA é **co-autor das skills de teste** e **revisor** da qualidade dos artefatos gerados com base nelas. Usa Claude como parceiro de raciocínio — não para gerar código de produção, mas para escrever test plans, elaborar cenários de edge case e revisar se a `create-integration-test` produz testes que realmente cobrem os verification criteria das specs.

---

## Product Specialist

| Skill | Papel na skill | Agente | Etapa SDD |
|---|---|---|---|
| `create-react-card` | **CO-CRIA** com Dev Sênior (define o que o card deve exibir, o comportamento esperado do feedback form, e a linguagem ubíqua nas labels) | Claude | Plan |
| `project-structure` | **CONSOME** (leitura) para entender onde specs e prompts ficam no repositório | Claude | Spec |
| `create-rag-endpoint` | **CONSOME** (leitura) para entender o contrato de resposta do endpoint ao escrever verification criteria nas specs | Claude | Spec |
| `azure-functions-endpoint` | **CONSOME** (leitura) para entender limites técnicos ao escrever requirements.md | Claude | Spec |
| `create-react-card` | **CONSOME** ao revisar se os cards entregues pelos devs refletem os requisitos definidos na spec | Claude | Review |

**Resumo do papel:** O Product Specialist **não cria skills técnicas**, mas é co-autor das skills que têm interface direta com produto (como `create-react-card`) porque define o comportamento esperado e a linguagem do domínio que o componente deve usar. Consome skills Domain e Artifact em **modo leitura** para entender restrições técnicas ao escrever specs — isso evita requirements impossíveis de implementar.

---

## Delivery Manager

| Skill | Papel na skill | Agente | Etapa SDD |
|---|---|---|---|
| `project-structure` | **CONSOME** (leitura) para entender a estrutura do repositório ao comunicar status e gerar relatórios de progresso | Claude | Spec / Plan |
| *(nenhuma skill)* | **Não cria skills** — o DM não gera artefatos técnicos ou de código | — | — |

**Resumo do papel:** O Delivery Manager **não cria nem mantém skills**. Consome `project-structure` em modo leitura para entender onde specs, tasks e artefatos ficam no repositório — informação necessária para rastrear progresso no board e comunicar status ao cliente. Usa Claude exclusivamente para gestão: elaborar relatórios, redigir comunicados, estruturar retrospectivas e gerar checklists de validation gates.

---

## Visão consolidada: quem cria cada skill

| Skill | Nível | Autor principal | Co-autor |
|---|---|---|---|
| `typescript-conventions` | Foundation | Tech Lead | — |
| `error-handling` | Foundation | Tech Lead | — |
| `project-structure` | Foundation | Tech Lead | — |
| `azure-functions-endpoint` | Domain | Tech Lead | Dev Sênior (exemplos) |
| `azure-ai-search-integration` | Domain | Tech Lead | Dev Sênior (exemplos) |
| `react-components` | Domain | Tech Lead | Dev Sênior (exemplos) |
| `testing-patterns` | Domain | Tech Lead + QA | — |
| `create-rag-endpoint` | Artifact | Tech Lead | Dev Sênior |
| `create-integration-test` | Artifact | QA | Tech Lead · Dev Sênior |
| `create-react-card` | Artifact | Dev Sênior | Product Specialist |

---

## Ciclo de vida de uma skill

### 1. Criação

**Quem inicia:** O autor principal (conforme tabela acima) identifica um artefato que será gerado repetidamente — tipicamente após a segunda vez que o mesmo tipo de código é escrito manualmente. A regra prática é: *se você vai gerar isso três vezes, escreva uma skill antes da terceira.*

**Como é escrita:**

1. O autor usa o **Claude** para rascunhar a estrutura da skill a partir dos artefatos reais já produzidos no projeto (não de abstrações). O rascunho inclui: contexto, frase-ativação, regras prescritivas, dois exemplos completos (DO / DON'T) e anti-padrões.
2. Para skills de código (Foundation e Domain), o autor usa o **Copilot** para validar a skill: com o arquivo presente no repositório, pede que o Copilot gere um artefato do tipo descrito e verifica aderência. Se o Copilot não seguir a skill, a skill é reescrita — não o código.
3. O co-autor (quando houver) revisa o rascunho e adiciona exemplos do seu domínio de experiência.
4. A skill é salva no caminho correto dentro de `/skills/` conforme o Anexo C (`foundation/`, `domain/`, ou `artifact/`).
5. Um PR é aberto com a skill como único arquivo alterado. O Tech Lead aprova PRs de Domain e Artifact; o Tech Lead + QA aprovam juntos para `testing-patterns` e `create-integration-test`.

**Critério de "skill pronta para uso":** o Copilot (ou Claude, dependendo do consumidor) gera um artefato aderente aos padrões do projeto em pelo menos 2 tentativas consecutivas sem que o desenvolvedor precise corrigir violações estruturais.

---

### 2. Atualização

**Quando deve ser revisada:**

- Um desenvolvedor encontra um anti-padrão não coberto pela skill (o Copilot gerou algo errado que a skill não prevenia).
- Uma decisão técnica muda (ex: mudança de biblioteca, nova versão do Azure Functions, alteração nos padrões de logging).
- Um incidente em produção é rastreado até um artefato gerado com base na skill — a skill não preveniu o problema.
- A cada **sprint de revisão** (sugerido: a cada 4 sprints), o Tech Lead e QA fazem uma leitura das skills ativas e verificam se os exemplos ainda refletem o código real em `src/`.

**Quem inicia a atualização:** Qualquer membro do time pode abrir uma issue de melhoria de skill. O desenvolvedor descreve: qual regra está faltando, qual anti-padrão a skill não preveniu, e um exemplo concreto do artefato problemático.

**Quem aprova a atualização:**

| Skill | Aprovação |
|---|---|
| Foundation | Tech Lead (obrigatório) |
| Domain — backend | Tech Lead (obrigatório) |
| Domain — testing | Tech Lead + QA |
| Domain — React | Tech Lead + Dev Sênior |
| Artifact — `create-rag-endpoint` | Tech Lead |
| Artifact — `create-integration-test` | QA + Tech Lead |
| Artifact — `create-react-card` | Dev Sênior + Product Specialist |

**Processo de atualização:**

1. Branch `skill/update-<nome-da-skill>` criada a partir de `main`.
2. Skill atualizada com: nova regra ou exemplo adicionado, anti-padrão documentado, e data de atualização registrada no cabeçalho do arquivo (`updated_at: YYYY-MM-DD`).
3. O autor valida a skill atualizada com o Copilot antes de abrir o PR — mesma validação da criação.
4. PR aprovado pelos papéis listados acima.
5. Após merge, o autor notifica o time via canal de comunicação do projeto com um resumo do que mudou e por quê.

> **Nota sobre retroatividade:** Atualizações de skill **não exigem** refatoração imediata dos artefatos já produzidos. A skill vigente se aplica a artefatos novos. Se a mudança corrigir um bug ou risco de segurança, o Tech Lead decide caso a caso se a retroatividade é obrigatória.

---

### 3. Depreciação

**Quando remover uma skill:**

- A skill cobre um artefato que não é mais produzido no projeto (ex: o painel React foi substituído por uma solução third-party).
- A skill foi totalmente absorvida por outra — o conteúdo foi consolidado e duplicação geraria inconsistência.
- A tecnologia que a skill documenta foi removida do stack (ex: migração de Azure Functions para outro runtime).

**O que fazer com artefatos que dependiam dela:**

1. Antes de depreciar, o Tech Lead lista todos os artefatos no repositório gerados com base na skill (busca por referências ao nome da skill em comentários, PRs e tasks).
2. Cada artefato listado é avaliado: ainda está em uso? Precisa de refatoração? O Tech Lead documenta a decisão.
3. A skill **não é deletada imediatamente** — ela é movida para `/skills/deprecated/` com um cabeçalho de depreciação:

```markdown
> ⚠️ DEPRECADA em YYYY-MM-DD  
> Motivo: [razão]  
> Substituída por: [nome da skill substituta, se houver]  
> Artefatos afetados: [lista ou "nenhum identificado"]
```

4. A skill permanece em `/skills/deprecated/` por **2 sprints** após a depreciação, para que o time possa consultar o histórico se necessário.
5. Após esse período, um PR remove o arquivo de `/skills/deprecated/`. O histórico permanece acessível via `git log`.

**Quem aprova a depreciação:** Tech Lead (obrigatório) + o co-autor principal da skill (quando houver). Para `testing-patterns` e `create-integration-test`, QA também aprova.
