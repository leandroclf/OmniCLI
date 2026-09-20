# Proposta Mestra de Arquitetura — Plataforma de colaboração

## 1. Escopo desta etapa

Este documento consolida os dois ciclos anteriores (proposta inicial de arquitetura + revisão crítica). Ele **não é uma arquitetura para construir agora** — é o registro de onde a discussão chegou e do que falta decidir antes que faça sentido escrever código.

**Fato:** a ideia original é "construir uma plataforma de colaboração", sem escopo, usuário, volume, orçamento ou prazo definidos.
**Fato:** a revisão do ciclo anterior apontou, corretamente, que a resposta inicial (14 seções, 5 ADRs, plano de 6 fases) era desproporcional a esse insumo.

Diante disso, esta proposta mestra assume um papel diferente do que o pedido original sugere: em vez de fixar uma arquitetura definitiva, ela define **o que já é consenso**, **o que é hipótese**, e **qual é o próximo passo mínimo antes de qualquer construção**.

## 2. Premissas (marcadas por origem)

| Premissa | Origem | Status |
|---|---|---|
| Existe um "recurso central" a ser colaborado (documento, tarefa, item) | Hipótese herdada da proposta inicial | Não confirmada — precisa de resposta do usuário |
| Múltiplas organizações/tenants desde o dia 1 | Hipótese herdada, contestada pela revisão | Recomendo tratar como **decisão pendente**, não padrão |
| Sem tempo real, sem videoconferência, sem edição colaborativa síncrona | Consenso dos dois ciclos anteriores | Preservado |
| Nenhuma tecnologia específica (banco, fila, nuvem) foi validada | Fato | Qualquer menção futura a stack é hipótese, não decisão |
| Não há orçamento, prazo ou tamanho de equipe informado | Fato | Impede avaliar viabilidade de qualquer plano de fases |

## 3. Decisões preservadas dos ciclos anteriores

Estas são as únicas decisões que sobrevivem à crítica e que recomendo manter como válidas independentemente do rumo que o escopo tomar:

1. **Não assumir colaboração em tempo real** (edição simultânea, presença, videochamada) sem evidência de demanda. Se isso for necessário depois, é uma mudança de arquitetura relevante, não um detalhe incremental.
2. **Armazenar arquivos fora do banco relacional** (armazenamento de objetos), mesmo em um MVP mínimo — é uma prática de baixo custo agora e caro de corrigir depois via migração.
3. **Uma arquitetura tecnicamente correta não substitui validação de produto.** Esse princípio deve orientar a ordem dos próximos passos (seção 6), não apenas constar como aviso final.

## 4. O que foi descartado do ciclo anterior (e por quê)

| Item descartado | Motivo |
|---|---|
| Fila/broker de mensagens dedicado | Otimização prematura sem volume conhecido; cron/worker simples resolve o mesmo problema no estágio atual |
| Outbox pattern | Complexidade real (tabela extra, poller, idempotência) que só se paga com volume de eventos assíncronos existente |
| Módulo de auditoria separado de logs de aplicação | Requisito de compliance maduro sem cliente corporativo ou jurisdição confirmados |
| Papéis diferenciados (colaborador limitado, leitor) | Nenhum caso de uso concreto exige essa granularidade ainda |
| Plano de 6 fases com testes de carga e piloto formal | Pressupõe equipe e prazo não informados; inavaliável no momento |

**Recomendação:** cada um desses itens pode voltar à mesa, mas apenas quando houver um gatilho concreto (volume medido, cliente com exigência de compliance, caso de uso real de permissão). Adicioná-los antes disso é custo sem retorno demonstrado.

## 5. Requisitos

### 5.1 Requisitos que já podem ser tratados como estáveis
- Persistir um recurso central e permitir que mais de uma pessoa interaja com ele de forma assíncrona.
- Manter arquivos anexos fora do banco relacional.
- Rodar com uma única base de dados relacional gerenciada.

### 5.2 Requisitos que dependem de resposta do usuário (ver seção 8)
- Qual é o recurso central (documento? tarefa? projeto? outro?).
- Quem usa isso amanhã — um time interno, clientes externos, ambos?
- Multi-tenant é necessário desde o início ou pode vir depois?
- Existe uma ferramenta pronta (planilha, Trello, Notion) já em uso que essa plataforma pretende substituir? Se sim, por quê ela é insuficiente?

## 6. Arquitetura recomendada — apenas o próximo passo, não o produto final

Dado o nível de informação disponível, a arquitetura recomendável não é uma arquitetura de sistema — é uma sequência de validação:

**Fase -1 (recomendada pela revisão anterior, agora incorporada): validar sem código.**
Usar uma ferramenta pronta (planilha compartilhada, board existente) por 1–2 semanas com usuários reais para confirmar que o fluxo de colaboração proposto resolve um problema real.

**Fase 0: menor fluxo único, se a Fase -1 confirmar a hipótese.**
- Um serviço único (monólito), um tipo de recurso, sem multi-tenant, sem fila, sem auditoria separada.
- Um banco Postgres (ou equivalente) + armazenamento de objetos para arquivos.
- Processamento assíncrono, se necessário, via worker simples (não fila dedicada).

Isso não é uma "arquitetura evolutiva completa" — é deliberadamente incompleto até que haja evidência de uso.

**Sinalização explícita de incerteza:** nenhuma tecnologia, provedor de nuvem ou custo é citado aqui porque nenhum foi validado nos ciclos anteriores. Qualquer número de infraestrutura neste estágio seria invenção.

## 7. Riscos

| Risco | Natureza | Mitigação recomendada |
|---|---|---|
| Investir em arquitetura antes de validar o problema | Já materializado no ciclo 1 | Adotar a Fase -1 antes de qualquer código |
| Multi-tenant mal implementado causar vazamento de dados entre organizações | Potencial, se a decisão for tomada sem análise | Tratar multi-tenant como decisão explícita a confirmar, não padrão default |
| Adicionar fila/auditoria/permissões antecipadamente | Custo de manutenção sem uso comprovado | Só adicionar mediante gatilho medido (volume, cliente, exigência legal) |
| Prazo e equipe desconhecidos tornarem qualquer plano de fases inavaliável | Fato atual | Não comprometer com cronograma até ter esses dados |

## 8. Decisões pendentes (bloqueiam o avanço)

Estas perguntas precisam de resposta humana antes que qualquer arquitetura adicional faça sentido:

1. **Qual é o recurso central da colaboração?** (documento, tarefa, projeto, outro)
2. **Quem usa isso e quando?** (usuário interno vs. cliente externo; "amanhã" ou "em 6 meses")
3. **Multi-tenant é um requisito confirmado ou uma suposição a testar?**
4. **Existe orçamento e prazo, ainda que aproximados?**
5. **Já existe uma ferramenta pronta em uso que essa plataforma substituiria? Por que ela falha?**
6. **Há algum requisito de compliance ou jurisdição já conhecido** (ex.: cliente corporativo com exigência de auditoria) que justificaria adiantar o módulo de auditoria da seção 4?

## 9. Critérios de aceite para esta etapa

- [ ] O documento separa claramente fatos, hipóteses herdadas e recomendações (feito acima).
- [ ] Nenhuma tecnologia, custo ou integração é apresentada como decidida sem sinalização de incerteza.
- [ ] As decisões válidas dos ciclos anteriores (seção 3) foram preservadas e não descartadas por engano.
- [ ] As inconsistências do ciclo anterior (escopo desproporcional ao insumo) foram corrigidas, não repetidas.
- [ ] As decisões pendentes (seção 8) estão explícitas e endereçadas a uma pessoa, não ao próximo ciclo do pipeline.

## 10. Conclusão

Como este é o ciclo 1 de 1, não há próxima rodada automática de refinamento arquitetural neste pipeline. O documento correto a produzir agora não é uma arquitetura maior — é este registro de consenso mínimo e da lista de perguntas em aberto. **Recomendação final: a próxima ação não é técnica, é uma conversa com o usuário para responder à seção 8.**
