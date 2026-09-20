# Revisão de viabilidade

## 1. Veredito geral

O documento anterior está tecnicamente correto na conclusão central (CAP se aplica; "consistência forte + offline total + custo mínimo" simultâneos para todo o sistema é impossível) e não precisa ser refeito. Esta revisão foca no que falta: custo real, complexidade operacional e onde a proposta é maior do que o problema pede.

## 2. Fatos fornecidos

- Idea original: consistência forte global, custo mínimo, disponibilidade offline total. Nenhum domínio, escala ou stack foi informado.
- Não há indicação de orçamento, equipe disponível, prazo ou se isto é greenfield ou retrofit de sistema existente.

Sem esses dados, qualquer número de custo abaixo é estimativa qualitativa, não orçamento.

## 3. Onde a proposta está inflada (hipótese: sim, para a maioria dos casos reais)

O desenho da etapa anterior é correto como referência, mas é dimensionado para um sistema multi-tenant com muitos escritores concorrentes e dados críticos globais reais (ex.: um produto SaaS com milhares de instalações). Antes de aceitar a arquitetura completa (14 seções, 7 fases, 8 componentes de serviço), vale confirmar se o problema exige isso.

- **Se for 1 usuário/instalação por "tenant"** (ex.: ferramenta CLI local com sync ocasional para nuvem própria): não há concorrência real, logo não há necessidade de resolução de conflitos multi-escritor, fila de conflitos, nem serviço de reconciliação dedicado. Um `updated_at` + revisão monotônica por dispositivo já resolve.
- **Se o volume de dados críticos globais for pequeno** (ex.: só permissões e licenciamento): não é preciso um "Serviço de autoridade global" separado — um único banco relacional com transações serializáveis já entrega consistência forte, sem inventar um serviço novo.
- Log de operações + outbox + motor de sincronização + serviço de reconciliação + serviço de resolução de conflitos = 5 componentes distintos. Isso é apropriado para sistemas tipo CRDT/replicação distribuída (nível de complexidade de um Figma multiplayer ou um CRM offline-first). Para a maioria dos casos, isso é over-engineering perigoso frente ao objetivo declarado de "custo mínimo".

**Recomendação:** antes de aprovar a Fase 1, obrigar uma resposta objetiva a "quantos escritores concorrentes por entidade, realisticamente, em 99% dos casos?". Se a resposta for 1, cortar toda a seção 5.6 (resolução de conflitos) e substituir por rejeição simples de escrita com revisão obsoleta — o cliente reenvia manualmente. Isso elimina a maior fonte de custo de desenvolvimento e suporte do desenho.

## 4. Custos e riscos operacionais (sinalizando incerteza)

*Hipótese, não fato*: não tenho dados de precificação de nenhum provedor específico para este projeto — os itens abaixo são categorias de custo a orçar, não valores.

| Item | Risco | Observação |
|---|---|---|
| Autoridade central com controle de concorrência otimista | Baixo-médio | Pode ser um único banco relacional gerenciado; não exige serviço novo se o volume for baixo |
| Log de operações + auditoria com retenção | Médio | Cresce indefinidamente sem política de expurgo definida (seção 9.6 menciona isso, mas não fixa números) |
| Fila de conflitos + intervenção manual | Alto (custo operacional, não infra) | Esse é o item que historicamente mais gera custo de suporte humano recorrente — a proposta não estima taxa de conflito esperada, e sem isso "custo mínimo" é uma afirmação não verificável |
| Observabilidade completa (seção 11) desde o "primeiro protótipo" | Médio | Correto como prática, mas conflita com "custo mínimo" se aplicado à risca antes de haver usuários reais; sugiro mínimo viável (log estruturado + 3-4 métricas) na Fase 2, expandir na Fase 6 conforme já planejado |
| Multi-região | Já corretamente descartado no texto | Boa decisão, manter |

## 5. Limitações de ferramentas não verificadas

O documento anterior usa nomes de contrato ilustrativos (`Operation`, `Applied/Conflict/Rejected`) e afirma isso explicitamente — correto, evita a aparência de integração real. Nenhuma tecnologia concreta (banco, fila, SDK de sync) foi nomeada, então não há capacidade de ferramenta para verificar aqui. Ponto de atenção: qualquer escolha futura de "CRDT pronto" ou "sync engine de terceiros" deve ser validada quanto a licença, maturidade e suporte antes de entrar no plano — não assumir que existe uma biblioteca que resolve merge automático para o domínio específico sem checar.

## 6. Alternativa mais simples a considerar

Se a maioria dos dados do sistema puder ser classificada como local ou sincronizável (não crítica), a alternativa mais barata é:

1. Um banco local embutido (ex. SQLite) por dispositivo com uma coluna de revisão/versão.
2. Uma única tabela remota "log de eventos" com chave de idempotência (sem serviço de autoridade separado).
3. Resolução de conflito = rejeitar e pedir reenvio ao usuário (sem merge automático), até que dados reais mostrem que isso incomoda.
4. Autoridade forte só para autenticação/permissões, delegada a um provedor de identidade existente em vez de construída do zero.

Isso cobre consistência forte onde importa, disponibilidade offline onde é viável, e corta a maior parte do custo de desenvolvimento das seções 5.6, 5.7 e parte da 11. Evoluir para o desenho completo (CRDTs, merge automático, reconciliação) somente se o piloto (Fase 7, já prevista) mostrar taxa de conflito ou volume que justifique.

## 7. Decisões que travam a viabilidade (complementa a seção 14 do documento anterior)

Antes de orçar ou iniciar a Fase 1:

1. Escritores concorrentes reais por entidade — se 1, cortar conflito automático.
2. Existe orçamento e prazo definidos, ou "custo mínimo" é apenas uma preferência relativa?
3. Há already um provedor de identidade/autorização em uso, ou isso será construído do zero (impacto direto em custo e prazo)?
4. Taxa de conflito aceitável para intervenção manual — sem isso, não é possível validar se "custo mínimo" foi atingido.

## 8. Conclusão

A arquitetura de referência da etapa anterior é sólida como teto de complexidade e não contém erros técnicos identificados. O risco de viabilidade não está na arquitetura em si, mas na ausência de escopo: sem saber concorrência real, orçamento e volume de dados críticos, o próximo passo correto não é implementar as 7 fases, e sim responder as quatro perguntas da seção 7 acima e, com as respostas, cortar (não expandir) o desenho para o subconjunto mínimo que atende ao caso real.
