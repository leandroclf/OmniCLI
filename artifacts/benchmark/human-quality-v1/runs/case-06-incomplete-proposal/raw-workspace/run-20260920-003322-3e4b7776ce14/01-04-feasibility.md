# Revisão de viabilidade — Plataforma de colaboração

## 1. Veredicto

O documento anterior é tecnicamente correto, mas **desproporcional ao insumo recebido**. A ideia original tem uma frase e nenhum detalhe. A resposta entrega ~14 seções, 5 ADRs, modelo de dados, plano de 6 fases e checklist de aceitação. Isso não é uma arquitetura "evolutiva e enxuta" — é um documento de referência genérico que qualquer SaaS de colaboração poderia reaproveitar, o que é sinal de que resolve pouco o problema real (que ainda nem existe).

**Fato:** a ideia fornecida não contém escopo, usuário, volume ou orçamento.
**Inferência:** o documento anterior tratou a ausência de escopo como licença para produzir uma arquitetura de referência completa, em vez de sinalizar que a etapa correta aqui é descoberta, não arquitetura.
**Recomendação:** o próximo ciclo (ou interação humana) deveria travar em uma pergunta única — "qual é o recurso central e quem o usa amanhã?" — antes de qualquer documento adicional.

## 2. Custos e complexidade não sinalizados

- **Custo operacional do "mínimo" proposto já não é mínimo.** O núcleo descrito exige: banco relacional gerenciado, armazenamento de objetos, fila/broker, serviço de e-mail, observabilidade estruturada (logs + métricas + auditoria separada). Isso é 4-5 peças de infraestrutura gerenciada para uma ideia sem usuário validado. Um MVP real de "validar um fluxo" poderia rodar em um único banco Postgres com jobs agendados (cron/worker simples), sem fila dedicada — a fila é uma otimização prematura sem volume conhecido.
- **Auditoria separada de logs de aplicação** (seção 4, módulo de auditoria) é uma exigência de compliance madura. Sem jurisdição, sem cliente corporativo confirmado, isso é trabalho antecipado sem gatilho — hipótese não sinalizada como tal no documento original.
- **Outbox pattern** (seção 6) é uma técnica correta para consistência transacional, mas é complexidade real de implementação (tabela extra, poller/relay, idempotência ponta a ponta) que só se paga quando já existe volume de eventos assíncronos. Para um fluxo único de MVP, poderia haver apenas uma tabela de tarefas simples processada por worker, sem o padrão formal.

## 3. Riscos operacionais

- **Multi-tenant/organização desde o dia 1** (módulo de espaços) é a decisão que mais infla o modelo de dados e testes de isolamento. O documento já assume isso como hipótese (seção 2), mas não deixa claro o custo de manter isolamento lógico correto sob teste — é o tipo de requisito que, se estiver errado, gera vazamento de dados entre clientes. Deveria ser tratado como decisão explícita a confirmar, não como padrão.
- **Autorização baseada em papéis "suficiente"** é razoável, mas o documento já antecipa "colaborador limitado" e "leitor" sem um caso de uso que exija diferenciação — risco de over-design que o próprio documento alerta na seção 14, mas não aplica a si mesmo na seção 4.
- **Plano de 6 fases com backups testados, testes de carga, piloto formal** (Fase 4) pressupõe equipe e prazo que não foram informados. Não há como avaliar se isso é viável em 2 semanas ou 2 anos.

## 4. Limitações de ferramentas e afirmações não verificáveis

- O documento não cita nenhuma tecnologia específica (banco, fila, provedor de nuvem), o que é correto dado o nível de informação — mas isso também significa que **nenhuma estimativa de custo real pode ser feita** ainda. Qualquer número de infraestrutura seria invenção.
- Não há dados suficientes para confirmar se "monólito modular" é de fato mais barato que alternativas mais simples ainda, como **não construir infraestrutura nenhuma e validar com uma ferramenta existente** (planilha compartilhada, Notion, Trello) antes de escrever qualquer código. Essa alternativa mais simples não foi considerada no documento original e deveria ser explicitada como opção de "Fase -1".

## 5. Alternativa mais simples recomendada

Antes de qualquer arquitetura de software:

1. **Validar o problema com uma ferramenta pronta** (planilha, board, formulário) por 1–2 semanas com usuários reais.
2. Só then codificar o **menor fluxo único** (um tipo de recurso, um espaço, sem multi-tenant, sem fila, sem auditoria separada) em um único serviço com Postgres.
3. Adicionar fila, auditoria formal, multi-tenant e observabilidade avançada **somente quando houver evidência de uso real**, não como parte do "núcleo mínimo".

Isso reduz o "Fase 0 + Fase 1" do documento anterior para uma única fase mais barata e mais rápida de descartar se a hipótese falhar.

## 6. O que preservar do documento anterior

- A recusa em assumir tempo real, videoconferência ou edição colaborativa sem evidência (ADR-005) está correta e deve ser mantida.
- A separação de arquivos fora do banco (ADR-003) é uma boa prática de baixo custo e deve ser mantida mesmo no MVP mínimo, pois evita retrabalho de migração posterior.
- O aviso final da seção 14 ("uma arquitetura tecnicamente sólida não compensa ausência de validação de produto") é a conclusão correta — mas o restante do documento não age de acordo com esse próprio aviso.

## 7. Conclusão

Tecnicamente viável? Sim, todas as escolhas descritas funcionariam. **Recomendado agora?** Não — o custo de manter 8+ módulos, 5 ADRs e um plano de 6 fases é desproporcional a uma ideia de uma frase. A recomendação de viabilidade é: **reduzir drasticamente o escopo do MVP técnico e mover o esforço de descoberta de produto para antes da arquitetura**, não depois dela.
